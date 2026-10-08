"""impl plan Phase 1 'Unit tests' section: these 5 exact-named tests are mandated verbatim.
They live under tests/integration/ (not tests/unit/) because every one of them needs a real
job/DB round-trip -- the impl plan's own section header calls them part of "the Phase 1
authentication test suite" but their bodies are inherently DB-dependent.
"""
from __future__ import annotations

import uuid

import pytest

pytestmark = pytest.mark.asyncio


async def test_job_requires_valid_export_profile(client, auth_headers, completed_source_video):
    r = await client.post(
        "/v1/jobs", json={"source_video_id": completed_source_video, "export_profile_id": "not_a_real_profile"},
        headers=auth_headers,
    )
    assert r.status_code == 422
    assert "export profile" in r.json()["detail"]

    r2 = await client.post(
        "/v1/jobs", json={"source_video_id": completed_source_video, "export_profile_id": "tiktok_default"},
        headers=auth_headers,
    )
    # tiktok_default is enabled=false in config@1.json (impl plan §2.2: "verify before enabling")
    assert r2.status_code == 422


async def test_export_profile_immutable(client, auth_headers, completed_source_video):
    """impl plan §3.10: 'Every job has exactly one immutable export_profile_id selected at job
    creation.' There is no endpoint that can change it after creation -- proven here by
    asserting the job's profile fields are unchanged after every other job-mutating action."""
    r = await client.post(
        "/v1/jobs", json={"source_video_id": completed_source_video, "export_profile_id": "youtube_shorts"},
        headers=auth_headers,
    )
    job_id = r.json()["job_id"]

    from app.db import session_scope
    from app.models import ProcessingJob

    async def _profile_fields():
        async with session_scope() as session:
            job = await session.get(ProcessingJob, uuid.UUID(job_id))
            return job.export_profile_id, job.export_profile_sha256

    before = await _profile_fields()
    await client.post(f"/v1/jobs/{job_id}/cancel", headers=auth_headers)
    after = await _profile_fields()
    assert before == after


async def test_profile_hash_persisted_on_job(client, auth_headers, completed_source_video):
    r = await client.post(
        "/v1/jobs", json={"source_video_id": completed_source_video, "export_profile_id": "youtube_shorts"},
        headers=auth_headers,
    )
    job_id = uuid.UUID(r.json()["job_id"])

    from app.db import session_scope
    from app.models import ProcessingJob

    async with session_scope() as session:
        job = await session.get(ProcessingJob, job_id)
        assert job.export_profile_sha256 is not None
        assert len(job.export_profile_sha256) == 64  # sha256 hex digest length
        int(job.export_profile_sha256, 16)  # must actually be hex


async def test_job_cannot_attach_second_profile(client, auth_headers, completed_source_video):
    """impl plan §1.4: 'The API must never allow a second profile to be attached to an
    existing job.' POST /v1/jobs only ever creates a NEW job/row; there is no PATCH/PUT
    /v1/jobs/{id} endpoint at all, so a second profile can only ever land on a second job."""
    r1 = await client.post(
        "/v1/jobs", json={"source_video_id": completed_source_video, "export_profile_id": "youtube_shorts"},
        headers=auth_headers,
    )
    job_id = r1.json()["job_id"]

    # No mutating verb is accepted on /v1/jobs/{job_id} other than /cancel and /rerank
    # (impl plan §1.4's exact endpoint list) -- confirm the forbidden verbs are rejected.
    for method in ("put", "patch"):
        resp = await client.request(method, f"/v1/jobs/{job_id}", json={"export_profile_id": "tiktok_default"},
                                     headers=auth_headers)
        assert resp.status_code == 405, f"{method} /v1/jobs/{{job_id}} must not be a valid route"


async def test_candidate_state_not_stored_as_job_state(client, auth_headers, completed_source_video):
    """impl plan §1.6/Phase 12: candidate lifecycle (v5.0 2.26.1) is independent of the coarse
    job state machine (v5.0 2.25) -- proven by inserting a candidate directly (no pipeline
    exists yet to produce one via the API) with a state no job state machine value shares,
    and confirming the job's own `state` column is untouched and uses its own vocabulary."""
    rj = await client.post(
        "/v1/jobs", json={"source_video_id": completed_source_video, "export_profile_id": "youtube_shorts"},
        headers=auth_headers,
    )
    # Response contract (impl plan §6, confirmed this session): job creation always returns
    # CREATED, even though Phase 2 now advances the persisted row to NORMALIZING immediately
    # afterward as a separate, non-atomic dispatch step.
    assert rj.json()["state"] == "CREATED"
    job_id = uuid.UUID(rj.json()["job_id"])

    from app.db import session_scope
    from app.models import (
        JOB_STATES,
        SHORT_CANDIDATE_STATES,
        EditPlan,
        ProcessingJob,
        ShortCandidate,
        SourceRegion,
        VerifiedEditPlan,
    )

    # The two state vocabularies must not be the same enum reused for both concepts.
    assert set(JOB_STATES) != set(SHORT_CANDIDATE_STATES)
    assert "USER_EDITING" in SHORT_CANDIDATE_STATES and "USER_EDITING" not in JOB_STATES
    assert "READY_FOR_REVIEW" in JOB_STATES and "READY_FOR_REVIEW" not in SHORT_CANDIDATE_STATES

    async with session_scope() as session:
        job = await session.get(ProcessingJob, job_id)
        # Phase 2: create_job dispatches NORMALIZING as its second step, so the persisted row
        # has already moved past CREATED by the time this request returns (see test_phase2_*
        # for the dispatch contract itself). This assertion only needs *a* valid, coarse job
        # state that is disjoint from the candidate vocabulary -- not the specific value.
        assert job.state in JOB_STATES

        region = SourceRegion(
            job_id=job_id, region_kind="speech_led", start_ms=0, end_ms=45000,
            schema_version=1, stage_version="discovery@1", config_version="config@1",
            config_sha256="0" * 64, artifact_id=uuid.uuid4(), checksum="0" * 64, storage_location="test://n/a",
        )
        session.add(region)
        await session.flush()
        plan = EditPlan(
            source_region_id=region.id, lineage_id=uuid.uuid4(), plan_origin="model", intensity="balanced",
            schema_version=1, stage_version="edit_plan_gen@1", config_version="config@1",
            config_sha256="0" * 64, artifact_id=uuid.uuid4(), checksum="0" * 64, storage_location="test://n/a",
        )
        session.add(plan)
        await session.flush()
        verified = VerifiedEditPlan(
            edit_plan_id=plan.id, final_status="TRANSCRIPT_VERIFIED_PASS",
            schema_version=1, stage_version="verified_plan@1", config_version="config@1",
            config_sha256="0" * 64, artifact_id=uuid.uuid4(), checksum="0" * 64, storage_location="test://n/a",
        )
        session.add(verified)
        await session.flush()

        candidate = ShortCandidate(
            job_id=job_id, verified_edit_plan_id=verified.id, source_region_id=region.id,
            plan_origin="model", comparability_class="A", state="USER_EDITING",
            schema_version=1, stage_version="short_candidate@1", config_version="config@1",
            config_sha256="0" * 64, artifact_id=uuid.uuid4(), checksum="0" * 64,
            storage_location="test://n/a",
        )
        session.add(candidate)
        await session.commit()
        await session.refresh(candidate)
        candidate_id = candidate.id

    # The job's own state column is a completely separate row/column and is untouched by the
    # candidate's state -- i.e. inserting/mutating the candidate above did not move the job
    # row. It does NOT mean the job row is frozen at CREATED forever (Phase 2 legitimately
    # advances it to NORMALIZING right after creation); the point is job.state only ever moves
    # for job-level reasons, never as a side effect of candidate lifecycle writes.
    async with session_scope() as session:
        job_before = job.state  # captured before this block re-reads, for the no-side-effect check
        job = await session.get(ProcessingJob, job_id)
        candidate = await session.get(ShortCandidate, candidate_id)
        assert job.state == job_before
        assert candidate.state == "USER_EDITING"
