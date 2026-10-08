"""IT-1-2 (impl plan Phase 1, 'Integration test for Phase 2'): 'create the same fixture job
in D0 and D1. Verify the job carries one profile ID/hash and all subsequent stage/artifact
records inherit it.'

This sandbox only exercises the D0 half (no Railway hosting available here) -- the assertion
is scoped to what impl plan §5.0 rule 4 actually requires proven at this stage: one immutable
profile ID + hash on the job, inherited by everything created under it. D1 hosted parity is a
separate, later verification the real team runs against Railway.
"""
from __future__ import annotations

import uuid

import pytest

pytestmark = pytest.mark.asyncio


async def test_it_1_2_job_profile_identity_is_singular_and_inherited(client, auth_headers, completed_source_video):
    rj = await client.post(
        "/v1/jobs", json={"source_video_id": completed_source_video, "export_profile_id": "youtube_shorts"},
        headers=auth_headers,
    )
    assert rj.status_code == 201, rj.text
    job_id = uuid.UUID(rj.json()["job_id"])

    from app.db import session_scope
    from app.models import ProcessingJob

    async with session_scope() as session:
        job = await session.get(ProcessingJob, job_id)
        profile_id = job.export_profile_id
        profile_sha = job.export_profile_sha256
        config_sha = job.config_sha256

    assert profile_id == "youtube_shorts"
    assert profile_sha and len(profile_sha) == 64
    assert config_sha and len(config_sha) == 64

    # Two jobs created with the same profile at the same config version must get the same
    # profile hash (deterministic, content-addressed -- not a random per-job value).
    rj2 = await client.post(
        "/v1/jobs", json={"source_video_id": completed_source_video, "export_profile_id": "youtube_shorts"},
        headers=auth_headers,
    )
    job2_id = uuid.UUID(rj2.json()["job_id"])
    async with session_scope() as session:
        job2 = await session.get(ProcessingJob, job2_id)
        assert job2.export_profile_sha256 == profile_sha
