"""IT-0-1 (impl plan Phase 0, 'Integration test for Phase 1'): 'start PostgreSQL/Redis, run
migrations, create a user, create one job with one export_profile_id, and enqueue a
placeholder NORMALIZING task. Assert all IDs/config hashes/schema versions validate.'
"""
from __future__ import annotations

import uuid

import pytest

pytestmark = pytest.mark.asyncio


async def test_it_0_1_full_flow(client, auth_headers, completed_source_video, settings):
    from shorts_config import load_config

    config = load_config()

    rj = await client.post(
        "/v1/jobs",
        json={"source_video_id": completed_source_video, "export_profile_id": "youtube_shorts"},
        headers=auth_headers,
    )
    assert rj.status_code == 201, rj.text
    body = rj.json()
    job_id = body["job_id"]
    assert body["state"] == "CREATED"
    # "Assert all IDs ... validate": job_id parses as a real UUID.
    uuid.UUID(job_id)

    # Confirm the job row itself carries config/profile identity (schema_version/config
    # hashes) -- fetched at the DB layer since the JobStatusResponse wire schema
    # intentionally does not re-expose export_profile_sha256/config_sha256 to the client.
    from app.db import session_scope
    from app.models import ProcessingJob

    async with session_scope() as session:
        job = await session.get(ProcessingJob, uuid.UUID(job_id))
        assert job is not None
        assert job.export_profile_id == "youtube_shorts"
        assert job.export_profile_sha256 and len(job.export_profile_sha256) == 64
        assert job.config_version == config.config_version
        assert job.config_sha256 == config.config_sha256

    # "enqueue a placeholder NORMALIZING task": Phase 1 does not yet run normalization
    # (that's Phase 2), so this proves only that the queue/broker path itself works --
    # enqueueing a named task against the real Redis broker and confirming it lands.
    from app.tasks_client import get_task_client

    task_client = get_task_client(settings.redis_url)
    async_result = task_client.send_task(
        "workers.cpu.placeholder_normalizing", kwargs={"job_id": job_id}, queue="cpu",
    )
    assert async_result.id  # a real task id was assigned by the broker

    import redis

    r = redis.Redis.from_url(settings.redis_url)
    # Celery's Redis broker stores queued (undelivered) messages as a list at the queue name.
    assert r.llen("cpu") >= 1
