"""Body of the `workers.gpu.execute_gpu_task` Celery task (owner G7: worker-gpu executes what
`gpu_dispatch` submits).

Owner decisions 2026-10-02 #5/#6/#7: the worker reads input artifact METADATA (DB read-only, for
id -> storage_location) and transport-input descriptors, runs ONE backend call, writes the result
as an internal transport envelope (`phase3_stage_output_v1`, NOT a canonical artifact, no
Artifact row, no lineage) to content-addressed `transport/...` storage, and returns descriptors.
The control plane materializes canonical artifacts.

Failure semantics (#5): a StageFailure is a DECLARED failure and crosses the boundary typed
(PERMANENT_MODEL is reserved for explicit permanent model/config/provider incompatibility).
Any other exception is an unexpected crash: it is NOT caught here -- it propagates, the task
fails, and task/stage recovery + idempotency (bounded retries by the orchestrator) handle it."""
from __future__ import annotations

import json
import tempfile
import uuid
from pathlib import Path
from typing import Any

from app.models import Artifact, ProcessingJob
from app.storage import StorageAdapter
from shorts_config import Config, canonical_json, sha256_bytes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from workers.gpu.backends import Backends
from workers.shared.artifact_keys import transport_storage_key
from workers.shared.failures import FailureKind, StageFailure

STAGE_OUTPUT_TYPE = "phase3_stage_output_v1"  # internal transport envelope kind, not an artifact_type
STAGE_OUTPUT_VERSION = "phase3_stage_output@1"
TASKS = ("asr", "forced_alignment", "diarization")


async def _load(session: AsyncSession, ids: list[str]) -> dict[str, Artifact]:
    rows = (await session.scalars(select(Artifact).where(Artifact.id.in_([uuid.UUID(i) for i in ids])))).all()
    found = {str(r.id): r for r in rows}
    missing = [i for i in ids if i not in found]
    if missing:
        raise StageFailure(FailureKind.PERMANENT_INPUT, "input_artifact_missing", ",".join(missing))
    return found


def _stage_output_doc(cfg: Config, **fields: Any) -> dict:
    base = {
        "schema_version": 1, "stage_version": STAGE_OUTPUT_VERSION,
        "config_version": cfg.config_version, "config_sha256": cfg.config_sha256,
        "runtime_id": None, "runtime_sha256": None, "model_id": None, "model_revision": None,
        "model_sha256": None, "models": {}, "error_category": None, "segments": None, "words": None, "turns": None, "language": None,
    }
    base.update(fields)
    return base


async def run_gpu_task(
    session: AsyncSession, *, task_name: str, input_artifact_ids: list[str], cfg: Config,
    backends: Backends, artifact_storage: StorageAdapter, transport_inputs: dict | None = None,
) -> dict:
    try:
        if task_name not in TASKS:
            raise StageFailure(FailureKind.PERMANENT_VALIDATION, "unknown_gpu_task", task_name)
        arts = await _load(session, input_artifact_ids)
        by_type: dict[str, Artifact] = {a.artifact_type: a for a in arts.values()}
        audio = by_type.get("analysis_audio")
        if audio is None:
            raise StageFailure(FailureKind.PERMANENT_INPUT, "analysis_audio_missing")
        # Authorization / lineage checks stay strict although this worker only READS metadata
        # (owner 2026-10-04 #5): exactly one input artifact, of an approved type, with a job.
        if len(arts) != 1 or audio.job_id is None:
            raise StageFailure(FailureKind.PERMANENT_INPUT, "unauthorized_input_artifact",
                               f"{task_name} accepts exactly one analysis_audio artifact")
        job = await session.get(ProcessingJob, audio.job_id)
        source_video_id = str(job.source_video_id)

        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "analysis_audio.wav"
            wav.write_bytes(artifact_storage.read_bytes(audio.storage_location))
            if task_name == "asr":
                b = _need(backends.asr, "asr")
                segs = b.transcribe(wav)
                doc = _stage_output_doc(cfg, stage="asr", status="completed", segments=segs,
                                        **_identity(b))
            elif task_name == "forced_alignment":
                b = _need(backends.alignment, "alignment")
                asr_desc = (transport_inputs or {}).get("asr")
                if asr_desc is None:
                    raise StageFailure(FailureKind.PERMANENT_INPUT, "asr_output_missing")
                expected_prefix = f"transport/{source_video_id}/asr/"
                if not asr_desc["storage_location"].startswith(expected_prefix):
                    raise StageFailure(FailureKind.PERMANENT_INPUT, "unauthorized_transport_input",
                                       "transport input is not this source video's ASR envelope")
                raw = artifact_storage.read_bytes(asr_desc["storage_location"])
                if sha256_bytes(raw) != asr_desc["checksum"]:
                    raise StageFailure(FailureKind.PERMANENT_INPUT, "asr_output_checksum_mismatch")
                segs = json.loads(raw)["segments"]
                words = b.align(wav, segs)
                doc = _stage_output_doc(cfg, stage="forced_alignment", status="completed", words=words,
                                        **_identity(b))
            else:
                b = _need(backends.diarization, "diarization")
                turns = b.diarize(wav)
                doc = _stage_output_doc(cfg, stage="diarization", status="completed", turns=turns,
                                        **_identity(b))

        data = canonical_json(doc)
        sha = sha256_bytes(data)
        key = transport_storage_key(source_video_id=source_video_id, stage=task_name, sha256=sha)
        artifact_storage.write_bytes(key, data)
        return {"status": "ok", "outputs": [{
            "kind": STAGE_OUTPUT_TYPE, "stage": task_name, "schema_version": 1,
            "storage_location": key, "checksum": sha,
            "provenance": {"runtime_id": doc["runtime_id"], "model_id": doc["model_id"],
                           "model_revision": doc["model_revision"]},
        }]}
    except StageFailure as exc:
        return {"status": "error", "kind": str(exc.kind), "reason": exc.reason}


def _identity(b) -> dict:
    """Backend identity -> envelope fields. Real adapters carry runtime_sha256 / model_sha256 / models;
    test doubles may not (-> null / {})."""
    return {"runtime_id": b.runtime_id, "runtime_sha256": getattr(b, "runtime_sha256", None),
            "model_id": b.model_id, "model_revision": b.model_revision,
            "model_sha256": getattr(b, "model_sha256", None), "models": dict(getattr(b, "models", {}) or {})}


def _need(backend, name: str):
    if backend is None:
        raise StageFailure(FailureKind.BLOCKED_BY_DEPENDENCY, f"{name}_backend_unavailable")
    return backend
