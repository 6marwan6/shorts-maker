from __future__ import annotations

import uuid

import pytest

pytestmark = pytest.mark.asyncio


# --------------------------------------------------------------------------------------
# Auth: refresh rotation, logout, ownership isolation
# --------------------------------------------------------------------------------------

async def test_refresh_rotates_token_and_invalidates_the_old_one(client, registered_user):
    r = await client.post("/v1/auth/login", json={"email": registered_user["email"], "password": registered_user["password"]})
    old_cookie = r.cookies.get("shorts_maker_refresh")
    assert old_cookie

    client.cookies.set("shorts_maker_refresh", old_cookie)
    r2 = await client.post("/v1/auth/refresh")
    assert r2.status_code == 200, r2.text
    new_cookie = r2.cookies.get("shorts_maker_refresh")
    assert new_cookie and new_cookie != old_cookie

    # impl plan §1.3 "rotating refresh tokens": the OLD token must now be rejected (rotation,
    # not just extension).
    client.cookies.set("shorts_maker_refresh", old_cookie)
    r3 = await client.post("/v1/auth/refresh")
    assert r3.status_code == 401


async def test_logout_revokes_refresh_token(client, registered_user):
    r = await client.post("/v1/auth/login", json={"email": registered_user["email"], "password": registered_user["password"]})
    cookie = r.cookies.get("shorts_maker_refresh")
    client.cookies.set("shorts_maker_refresh", cookie)
    r2 = await client.post("/v1/auth/logout")
    assert r2.status_code == 204
    client.cookies.set("shorts_maker_refresh", cookie)
    r3 = await client.post("/v1/auth/refresh")
    assert r3.status_code == 401


async def test_wrong_password_rejected(client, registered_user):
    r = await client.post("/v1/auth/login", json={"email": registered_user["email"], "password": "wrong-password"})
    assert r.status_code == 401


async def test_me_requires_bearer_token(client):
    r = await client.get("/v1/me")
    assert r.status_code == 401


async def test_tampered_access_token_rejected(client, auth_headers):
    bad = auth_headers["Authorization"][:-4] + "beef"
    r = await client.get("/v1/me", headers={"Authorization": bad})
    assert r.status_code == 401


# --------------------------------------------------------------------------------------
# Uploads
# --------------------------------------------------------------------------------------

async def test_upload_complete_rejects_oversized_object(client, auth_headers, settings, monkeypatch):
    from app.storage import build_storage_adapter
    ru = await client.post("/v1/uploads", json={"filename": "too_big.mp4", "content_type": "video/mp4"}, headers=auth_headers)
    upload = ru.json()
    storage = build_storage_adapter(settings, bucket_kind="source")
    storage.write_bytes(upload["storage_key"], b"x" * 1000)

    import app.routers.uploads as uploads_module

    class _TinyCapConfig:
        def __getitem__(self, name):
            return 10 if name == "MAX_SOURCE_SIZE_BYTES" else NotImplemented

    monkeypatch.setattr(uploads_module, "load_config", lambda: _TinyCapConfig())

    rc = await client.post(f"/v1/uploads/{upload['upload_id']}/complete", json={}, headers=auth_headers)
    assert rc.status_code == 413


async def test_upload_complete_before_object_written_rejected(client, auth_headers):
    ru = await client.post("/v1/uploads", json={"filename": "never_written.mp4", "content_type": "video/mp4"}, headers=auth_headers)
    upload = ru.json()
    rc = await client.post(f"/v1/uploads/{upload['upload_id']}/complete", json={}, headers=auth_headers)
    assert rc.status_code == 400


async def test_upload_owned_by_a_different_user_is_not_visible(client, auth_headers, completed_source_video):
    # Register a second user; their bearer token must not be able to complete the first
    # user's upload / see their source video.
    other_email = f"other-{uuid.uuid4().hex[:12]}@example.com"
    await client.post("/v1/auth/register", json={"email": other_email, "password": "another-strong-pw"})
    r = await client.post("/v1/auth/login", json={"email": other_email, "password": "another-strong-pw"})
    other_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    rj = await client.post(
        "/v1/jobs", json={"source_video_id": completed_source_video, "export_profile_id": "youtube_shorts"},
        headers=other_headers,
    )
    assert rj.status_code == 404  # the source video belongs to `auth_headers`'s user, not this one


# --------------------------------------------------------------------------------------
# Candidates
# --------------------------------------------------------------------------------------

@pytest.fixture
def make_candidate():
    async def _make(job_id, **overrides):
        from app.db import session_scope
        from app.models import EditPlan, ShortCandidate, SourceRegion, VerifiedEditPlan

        async with session_scope() as session:
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

            defaults = {
                "job_id": job_id, "verified_edit_plan_id": verified.id, "source_region_id": region.id,
                "plan_origin": "model", "comparability_class": "A", "state": "DISPLAYED",
                "schema_version": 1, "stage_version": "short_candidate@1", "config_version": "config@1",
                "config_sha256": "0" * 64, "artifact_id": uuid.uuid4(), "checksum": "0" * 64,
                "storage_location": "test://n/a",
            }
            defaults.update(overrides)
            c = ShortCandidate(**defaults)
            session.add(c)
            await session.commit()
            await session.refresh(c)
            return c.id
    return _make


async def _create_job(client, auth_headers, completed_source_video):
    r = await client.post(
        "/v1/jobs", json={"source_video_id": completed_source_video, "export_profile_id": "youtube_shorts"},
        headers=auth_headers,
    )
    return uuid.UUID(r.json()["job_id"])


async def test_accept_candidate_transitions_state(client, auth_headers, completed_source_video, make_candidate):
    job_id = await _create_job(client, auth_headers, completed_source_video)
    candidate_id = await make_candidate(job_id)
    r = await client.post(f"/v1/candidates/{candidate_id}/accept", json={}, headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["state"] == "ACCEPTED"


async def test_accept_candidate_not_displayed_is_conflict(client, auth_headers, completed_source_video, make_candidate):
    job_id = await _create_job(client, auth_headers, completed_source_video)
    candidate_id = await make_candidate(job_id, state="ACCEPTED")
    r = await client.post(f"/v1/candidates/{candidate_id}/accept", json={}, headers=auth_headers)
    assert r.status_code == 409


async def test_reject_candidate_logs_review_action_with_reason(client, auth_headers, completed_source_video, make_candidate):
    job_id = await _create_job(client, auth_headers, completed_source_video)
    candidate_id = await make_candidate(job_id)
    r = await client.post(f"/v1/candidates/{candidate_id}/reject", json={"reason": "opening too weak"}, headers=auth_headers)
    assert r.status_code == 200

    from app.db import session_scope
    from app.models import ReviewAction
    from sqlalchemy import select

    async with session_scope() as session:
        rows = (await session.execute(select(ReviewAction).where(ReviewAction.short_candidate_id == candidate_id))).scalars().all()
        assert len(rows) == 1
        assert rows[0].action == "reject"
        assert rows[0].reason == "opening too weak"


async def test_edit_candidate_requires_at_least_one_operation(client, auth_headers, completed_source_video, make_candidate):
    job_id = await _create_job(client, auth_headers, completed_source_video)
    candidate_id = await make_candidate(job_id)
    r = await client.post(f"/v1/candidates/{candidate_id}/edit", json={"operations": []}, headers=auth_headers)
    assert r.status_code == 422


async def test_edit_candidate_transitions_to_reverifying_and_enqueues_task(client, auth_headers, completed_source_video, make_candidate):
    job_id = await _create_job(client, auth_headers, completed_source_video)
    candidate_id = await make_candidate(job_id)
    r = await client.post(
        f"/v1/candidates/{candidate_id}/edit",
        json={"operations": [{"type": "trim_start", "requested_source_ms": 1200}]},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["state"] == "REVERIFYING"


async def test_reframe_candidate_does_not_change_candidate_state(client, auth_headers, completed_source_video, make_candidate):
    """v5.0 2.26.1: reframe-only edits skip content verification -- unlike a content edit, the
    candidate does not move to REVERIFYING."""
    job_id = await _create_job(client, auth_headers, completed_source_video)
    candidate_id = await make_candidate(job_id)
    r = await client.post(f"/v1/candidates/{candidate_id}/reframe", json={"strategy": "face_aware"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["state"] == "DISPLAYED"


async def test_reframe_invalid_strategy_rejected_by_schema(client, auth_headers, completed_source_video, make_candidate):
    job_id = await _create_job(client, auth_headers, completed_source_video)
    candidate_id = await make_candidate(job_id)
    r = await client.post(f"/v1/candidates/{candidate_id}/reframe", json={"strategy": "not_a_real_strategy"}, headers=auth_headers)
    assert r.status_code == 422


async def test_candidate_not_owned_by_user_is_404(client, auth_headers, completed_source_video, make_candidate):
    job_id = await _create_job(client, auth_headers, completed_source_video)
    candidate_id = await make_candidate(job_id)

    other_email = f"other-{uuid.uuid4().hex[:12]}@example.com"
    await client.post("/v1/auth/register", json={"email": other_email, "password": "another-strong-pw"})
    r = await client.post("/v1/auth/login", json={"email": other_email, "password": "another-strong-pw"})
    other_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r2 = await client.post(f"/v1/candidates/{candidate_id}/accept", json={}, headers=other_headers)
    assert r2.status_code == 404


# --------------------------------------------------------------------------------------
# Rerank / display selection immutability
# --------------------------------------------------------------------------------------

async def test_rerank_creates_new_immutable_revision_not_an_update(client, auth_headers, completed_source_video):
    job_id = await _create_job(client, auth_headers, completed_source_video)
    r1 = await client.post(f"/v1/jobs/{job_id}/rerank", headers=auth_headers)
    r2 = await client.post(f"/v1/jobs/{job_id}/rerank", headers=auth_headers)
    assert r1.json()["revision"] == 1
    assert r2.json()["revision"] == 2

    from app.db import session_scope
    from app.models import DisplaySelection
    from sqlalchemy import select

    async with session_scope() as session:
        rows = (await session.execute(select(DisplaySelection).where(DisplaySelection.job_id == job_id))).scalars().all()
        assert len(rows) == 2  # two distinct rows -- the first was never updated in place
        assert {row.revision for row in rows} == {1, 2}
