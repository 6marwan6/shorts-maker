"""Integration test fixtures (impl plan §5.0 rule 4: 'the same integration contract is
re-run against hosted components'; here run against a real local PostgreSQL, per D0).

Requires a running PostgreSQL reachable at SHORTS_MAKER_TEST_DATABASE_URL (default:
postgresql+asyncpg://shorts_maker:shorts_maker_dev@127.0.0.1:5432/shorts_maker_test) and Redis
at SHORTS_MAKER_TEST_REDIS_URL. Skipped with a clear reason if neither is reachable, rather
than silently passing or hanging.
"""
from __future__ import annotations

import asyncio
import os
import uuid

import httpx
import pytest
import pytest_asyncio

TEST_DATABASE_URL = os.environ.get(
    "SHORTS_MAKER_TEST_DATABASE_URL",
    "postgresql+asyncpg://shorts_maker:shorts_maker_dev@127.0.0.1:5432/shorts_maker_test",
)
TEST_REDIS_URL = os.environ.get("SHORTS_MAKER_TEST_REDIS_URL", "redis://127.0.0.1:6379/1")


def _postgres_reachable() -> bool:
    import asyncpg

    async def _check():
        conn = await asyncpg.connect(TEST_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
        await conn.close()

    try:
        asyncio.run(_check())
        return True
    except Exception:  # noqa: BLE001 -- deliberate: any failure here means "not reachable"
        return False


_PG_UP = _postgres_reachable()

pytestmark = pytest.mark.skipif(
    not _PG_UP,
    reason=f"PostgreSQL not reachable at {TEST_DATABASE_URL} -- start it (impl plan §15.1 D0 checklist) to run integration tests.",
)


@pytest_asyncio.fixture
async def settings(tmp_path, monkeypatch):
    monkeypatch.setenv("SHORTS_MAKER_DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("SHORTS_MAKER_REDIS_URL", TEST_REDIS_URL)
    monkeypatch.setenv("SHORTS_MAKER_STORAGE_BACKEND", "local")
    monkeypatch.setenv("SHORTS_MAKER_LOCAL_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("SHORTS_MAKER_AUTH_SECRET_KEY", "test-secret-key")

    from app.config import get_settings
    get_settings.cache_clear()
    yield get_settings()
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def db_engine(settings):
    from app.db import Base, dispose_engine, get_engine
    await dispose_engine()
    engine = get_engine()
    async with engine.begin() as conn:
        from app import models  # noqa: F401  register tables on Base.metadata
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await dispose_engine()


@pytest_asyncio.fixture
async def client(db_engine, settings):
    from app.main import app
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def registered_user(client):
    email = f"user-{uuid.uuid4().hex[:12]}@example.com"
    password = "correct-horse-battery-staple"
    r = await client.post("/v1/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    return {"email": email, "password": password, "id": r.json()["id"]}


@pytest_asyncio.fixture
async def auth_headers(client, registered_user):
    r = await client.post("/v1/auth/login", json={"email": registered_user["email"], "password": registered_user["password"]})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def completed_source_video(client, auth_headers, settings):
    from app.storage import build_storage_adapter
    ru = await client.post("/v1/uploads", json={"filename": "fixture.mp4", "content_type": "video/mp4"}, headers=auth_headers)
    assert ru.status_code == 201, ru.text
    upload = ru.json()
    storage = build_storage_adapter(settings, bucket_kind="source")
    storage.write_bytes(upload["storage_key"], b"fake-mp4-bytes-for-testing")
    rc = await client.post(f"/v1/uploads/{upload['upload_id']}/complete", json={}, headers=auth_headers)
    assert rc.status_code == 200, rc.text
    return rc.json()["source_video_id"]
