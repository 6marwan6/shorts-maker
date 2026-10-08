"""IT-2-3 (impl plan Phase 2): run normalization on every Phase-0 canonical fixture (owner
decision, this session: "run all five", not a hard-coded count of three), then invoke the
ASR/diarization dispatch boundary using ONLY artifact IDs. Asserts Phase 3 locates normalized
media exclusively through artifact IDs + the storage abstraction, never a hard-coded local path.

This test also exercises the full owner-agreed dispatch flow end to end:
    upload complete -> raw_source Artifact committed -> POST /v1/jobs -> CREATED (response)
    -> enqueue NORMALIZING (separate step) -> job row advances to NORMALIZING
The Celery task is executed *inline* (CELERY_TASK_ALWAYS_EAGER-style direct call) rather than
requiring a live worker process, since no separate worker is part of this test harness; the
task body itself is untouched by that choice.
"""
from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import pytest
from sqlalchemy import select

pytestmark = pytest.mark.asyncio

FIXTURES = sorted(Path("packages/fixtures/media").glob("*.mp4"))


async def _upload_real_fixture(client, auth_headers, settings, fixture_path: Path) -> str:
    from app.storage import build_storage_adapter

    ru = await client.post("/v1/uploads", json={"filename": fixture_path.name, "content_type": "video/mp4"},
                            headers=auth_headers)
    assert ru.status_code == 201, ru.text
    upload = ru.json()
    storage = build_storage_adapter(settings, bucket_kind="source")
    storage.write_bytes(upload["storage_key"], fixture_path.read_bytes())
    rc = await client.post(f"/v1/uploads/{upload['upload_id']}/complete",
                            json={"checksum_sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest()},
                            headers=auth_headers)
    assert rc.status_code == 200, rc.text
    return rc.json()["source_video_id"]


@pytest.mark.parametrize("fixture_path", FIXTURES, ids=lambda p: p.name)
async def test_it_2_3_normalize_dispatch_and_artifact_only_resolution(
    client, auth_headers, settings, fixture_path,
):
    from app.db import session_scope
    from app.models import Artifact, ProcessingJob

    from workers.cpu.stage_normalize import run_normalization_stage
    from workers.shared.stage_runner import ConfigIdentity

    source_video_id = await _upload_real_fixture(client, auth_headers, settings, fixture_path)

    rj = await client.post("/v1/jobs", json={"source_video_id": source_video_id, "export_profile_id": "youtube_shorts"},
                            headers=auth_headers)
    assert rj.status_code == 201, rj.text
    assert rj.json()["state"] == "CREATED"  # response contract, independent of the row below
    job_id = rj.json()["job_id"]

    async with session_scope() as session:
        job = await session.get(ProcessingJob, uuid.UUID(job_id))
        # create_job's second step already advanced the persisted row.
        assert job.state == "NORMALIZING"

        from app.models import SourceVideo
        source_video_row = await session.get(SourceVideo, uuid.UUID(source_video_id))
        raw_storage_key = source_video_row.raw_storage_key

        raw_artifact = (await session.execute(
            select(Artifact).where(
                Artifact.source_video_id == uuid.UUID(source_video_id),
                Artifact.artifact_type == "raw_source"),
        )).scalar_one()
        assert raw_artifact.job_id is None  # strict ownership: raw_source never gets a job_id

        # (compute_stage_input_sha256 is exercised directly by workers/shared unit tests;
        # here we only need raw_artifact.id itself to invoke the stage below.)

    # Execute the stage body directly (no separate worker process in this harness) -- this is
    # the exact function the real Celery task calls, just invoked inline for the test.
    from app.config import get_settings
    from app.storage import build_storage_adapter
    from shorts_config import load_config

    cfg = load_config()
    source_storage = build_storage_adapter(get_settings(), bucket_kind="source")
    artifact_storage = build_storage_adapter(get_settings(), bucket_kind="artifacts")
    async with session_scope() as session:
        output_ids = await run_normalization_stage(
            session, job_id=job_id, source_video_id=source_video_id,
            source_storage_key=raw_storage_key,
            source_artifact_id=str(raw_artifact.id),
            source_storage=source_storage, artifact_storage=artifact_storage,
            config=ConfigIdentity(config_version=cfg.config_version, config_sha256=cfg.config_sha256),
            max_duration_s=cfg["MAX_SOURCE_DURATION_S"],
        )
        await session.commit()

    assert len(output_ids) >= 1

    # --- Phase-3-style consumer: resolve EXCLUSIVELY through artifact IDs + storage, never a
    # hard-coded filesystem path (this is the actual IT-2-3 assertion). ---
    async with session_scope() as session:
        video_artifact = None
        audio_artifact = None
        for aid in output_ids:
            art = await session.get(Artifact, uuid.UUID(aid))
            assert art.job_id == job_id or str(art.job_id) == str(job_id)
            assert art.source_video_id is None  # strict ownership: processing artifacts never get this
            if art.artifact_type == "normalized_media":
                video_artifact = art
            elif art.artifact_type == "analysis_audio":
                audio_artifact = art

        assert video_artifact is not None
        assert video_artifact.storage_location.endswith(".mp4")
        assert not video_artifact.storage_location.startswith("/")  # not a raw local filesystem path
        video_bytes = artifact_storage.read_bytes(video_artifact.storage_location)
        assert video_bytes and hashlib.sha256(video_bytes).hexdigest() == video_artifact.checksum

        probe = ffprobe_from_bytes(video_bytes)
        assert probe.video.pix_fmt == "yuv420p" and probe.video.codec == "h264"

        if audio_artifact is not None:
            assert audio_artifact.storage_location.endswith(".wav")
            audio_bytes = artifact_storage.read_bytes(audio_artifact.storage_location)
            assert hashlib.sha256(audio_bytes).hexdigest() == audio_artifact.checksum

    # Idempotency (§3.2): re-running the same stage input reuses the prior StageRun instead of
    # re-encoding.
    async with session_scope() as session:
        output_ids_2 = await run_normalization_stage(
            session, job_id=job_id, source_video_id=source_video_id, source_storage_key=raw_storage_key,
            source_artifact_id=str(raw_artifact.id),
            source_storage=source_storage, artifact_storage=artifact_storage,
            config=ConfigIdentity(config_version=cfg.config_version, config_sha256=cfg.config_sha256),
            max_duration_s=cfg["MAX_SOURCE_DURATION_S"],
        )
        await session.commit()
    assert output_ids_2 == output_ids


def ffprobe_from_bytes(data: bytes):
    import tempfile

    from workers.cpu.media_probe import probe_media
    with tempfile.NamedTemporaryFile(suffix=".mp4") as f:
        f.write(data)
        f.flush()
        return probe_media(f.name)
