"""Stage executor for NORMALIZING (impl plan Phase 2; owner decision 2026-10-02 #12). Wraps
normalize_media() + probe_media() behind the run_stage contract (§3.2) and writes Artifact rows via
the storage abstraction only -- Phase 3 must never see a raw filesystem/R2 path, only artifact IDs
(IT-2-3). Emits three artifacts: normalized_media, analysis_audio (iff the source has audio, owner
G6), and media_manifest_v1. Artifact ids are deterministic so the manifest can reference them."""
from __future__ import annotations

import subprocess
import tempfile
import uuid

from app.models import Artifact
from app.storage import StorageAdapter
from shorts_config import canonical_json, sha256_bytes
from sqlalchemy.ext.asyncio import AsyncSession

from workers.cpu.media_probe import ProbeResult, probe_media, validate_source
from workers.cpu.normalization import NormalizedMedia, normalize_media
from workers.shared.artifact_keys import artifact_storage_key
from workers.shared.stage_runner import (
    ConfigIdentity,
    NewArtifact,
    compute_stage_input_sha256,
    deterministic_artifact_id,
    run_stage,
)

STAGE_NAME = "NORMALIZING"
STAGE_VERSION = "normalize@1"
MANIFEST_STAGE_VERSION = "media_manifest@1"


def _tool_version(tool: str) -> str:
    out = subprocess.run([tool, "-version"], capture_output=True, text=True, check=False).stdout
    return (out.splitlines() or ["unknown"])[0].strip()


def _probe_doc(p: ProbeResult) -> dict:
    return {
        "duration_s": p.duration_s, "size_bytes": p.size_bytes,
        "video": None if p.video is None else {
            "codec": p.video.codec, "width": p.video.width, "height": p.video.height, "pix_fmt": p.video.pix_fmt,
            "r_frame_rate": p.video.r_frame_rate, "avg_frame_rate": p.video.avg_frame_rate,
            "rotation_deg": p.video.rotation_deg},
        "audio": None if p.audio is None else {
            "codec": p.audio.codec, "sample_rate": p.audio.sample_rate, "channels": p.audio.channels},
    }


def build_media_manifest_v1(
    *, config: ConfigIdentity, source_video_id: str, source_artifact_id: str, source_sha256: str,
    result: NormalizedMedia, video_ref: dict, audio_ref: dict | None,
) -> dict:
    sv = result.source_probe.video
    assert sv is not None and result.normalized_probe.video is not None
    nv = result.normalized_probe.video
    return {
        "schema_version": 1, "stage_version": MANIFEST_STAGE_VERSION,
        "config_version": config.config_version, "config_sha256": config.config_sha256,
        "source_video_id": source_video_id,
        "source": {"artifact_id": source_artifact_id, "sha256": source_sha256},
        "probe": _probe_doc(result.source_probe),
        "audio_presence": "present" if result.source_probe.has_audio else "no_audio_stream",
        "orientation": {
            "source_rotation_deg": sv.rotation_deg, "rotation_applied_to_pixels": sv.rotation_deg != 0,
            "display_width": nv.width, "display_height": nv.height},
        "cfr": {
            "is_cfr": result.cfr.is_cfr, "reason": result.cfr.reason, "frame_count": result.cfr.frame_count,
            "time_base": result.cfr.time_base, "constant_delta_ticks": result.cfr.constant_delta_ticks,
            "derived_fps": result.cfr.derived_fps, "selected_normalized_fps": result.selected_fps},
        "normalized_video": {"object": video_ref, "probe": _probe_doc(result.normalized_probe)},
        "analysis_audio": {
            "status": result.analysis_audio_status, "object": audio_ref,
            "probe": None if result.analysis_audio_probe is None else _probe_doc(result.analysis_audio_probe)},
        "provenance": {
            "operation": "ffprobe+ffmpeg_normalize", "ffmpeg_version": _tool_version("ffmpeg"),
            "ffprobe_version": _tool_version("ffprobe"), "ffmpeg_argv": result.ffmpeg_argv},
    }


async def run_normalization_stage(
    session: AsyncSession, *, job_id: str, source_video_id: str, source_storage_key: str,
    source_artifact_id: str, source_storage: StorageAdapter, artifact_storage: StorageAdapter,
    config: ConfigIdentity, max_duration_s: float,
) -> list[str]:
    stage_input_sha = compute_stage_input_sha256([source_artifact_id])

    def aid(kind: str) -> uuid.UUID:
        return deterministic_artifact_id(job_id=job_id, stage_input_sha256=stage_input_sha, artifact_type=kind)

    async def execute() -> list[NewArtifact]:
        src_row = await session.get(Artifact, uuid.UUID(source_artifact_id))
        source_sha256 = src_row.checksum
        # Read the source object through the storage abstraction, never a hard-coded local path.
        source_path = source_storage._path(source_storage_key) if hasattr(source_storage, "_path") else None
        if source_path is None:
            raise NotImplementedError(
                "non-local (R2) source read-through for worker-side ffmpeg execution is a D1 "
                "hosted-parity concern (impl plan §1.16); D0 uses LocalFilesystemStorage only."
            )
        probe = probe_media(source_path)
        validate_source(probe, max_duration_s=max_duration_s)

        with tempfile.TemporaryDirectory() as tmp:
            result = normalize_media(source_path, tmp, probe=probe)
            video_id = aid("normalized_media")
            video_key = artifact_storage_key(
                source_video_id=source_video_id, artifact_type="normalized_media",
                artifact_id=video_id, sha256=result.video_sha256)
            artifact_storage.write_bytes(video_key, result.video_path.read_bytes())
            video_ref = {"artifact_id": str(video_id), "sha256": result.video_sha256, "storage_location": video_key}
            artifacts = [NewArtifact(
                artifact_type="normalized_media", stage=STAGE_NAME, stage_version=STAGE_VERSION,
                schema_version=1, storage_location=video_key, checksum=result.video_sha256,
                model_versions={}, artifact_id=video_id)]

            audio_ref: dict | None = None
            if result.analysis_audio_path is not None:
                assert result.analysis_audio_sha256 is not None  # set together by normalize_media()
                audio_id = aid("analysis_audio")
                audio_key = artifact_storage_key(
                    source_video_id=source_video_id, artifact_type="analysis_audio",
                    artifact_id=audio_id, sha256=result.analysis_audio_sha256)
                artifact_storage.write_bytes(audio_key, result.analysis_audio_path.read_bytes())
                audio_ref = {"artifact_id": str(audio_id), "sha256": result.analysis_audio_sha256,
                             "storage_location": audio_key}
                artifacts.append(NewArtifact(
                    artifact_type="analysis_audio", stage=STAGE_NAME, stage_version=STAGE_VERSION,
                    schema_version=1, storage_location=audio_key,
                    checksum=result.analysis_audio_sha256, model_versions={}, artifact_id=audio_id))

            manifest = build_media_manifest_v1(
                config=config, source_video_id=source_video_id, source_artifact_id=source_artifact_id,
                source_sha256=source_sha256, result=result, video_ref=video_ref, audio_ref=audio_ref)
            data = canonical_json(manifest)
            msha = sha256_bytes(data)
            mid = aid("media_manifest_v1")
            mkey = artifact_storage_key(source_video_id=source_video_id, artifact_type="media_manifest_v1",
                                        artifact_id=mid, sha256=msha)
            artifact_storage.write_bytes(mkey, data)
            artifacts.append(NewArtifact(
                artifact_type="media_manifest_v1", stage=STAGE_NAME, stage_version=MANIFEST_STAGE_VERSION,
                schema_version=1, storage_location=mkey, checksum=msha, model_versions={}, artifact_id=mid))
            return artifacts

    return await run_stage(
        session, job_id=job_id, stage_name=STAGE_NAME, stage_version=STAGE_VERSION,
        input_artifact_ids=[source_artifact_id], config=config, execute=execute,
    )
