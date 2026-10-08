# apps/api

FastAPI backend (impl plan §1.3). Stateless -- state lives in PostgreSQL, Redis, and object
storage (impl plan §1.6.1).

## Local (D0) setup

Requires PostgreSQL 18.x + pgvector and Redis reachable at the URLs in `app/config.py`'s
defaults (override with `SHORTS_MAKER_DATABASE_URL` / `SHORTS_MAKER_REDIS_URL` env vars, or a
`.env` file in this directory). The real repo ships a `docker-compose.yml` for these (impl
plan §1.6.1) -- see `infra/docker/` once Phase 18 lands; until then, run Postgres/Redis however
is convenient locally (Docker, a native install, etc).

**Sandbox note:** this was developed and its tests were run against locally-installed
PostgreSQL 16 + pgvector 0.6.0 + Redis 7.0.15 (whatever `apt` had available in the sandbox that
built this), NOT the impl plan §1.5/§1.4 pinned versions (PostgreSQL 18.6 / pgvector 0.8.2 /
Redis OSS 7.1). This is a sandbox validation convenience only -- it proves the schema,
migrations, and API logic are actually correct against a real Postgres, not that the pinned
versions were used. The real local Docker Compose setup should still target the pinned
versions from §1.4/§1.5; re-run the integration suite against them before treating this as
fully confirmed on the pinned stack.

```bash
# from the repo root
uv sync --group api --group test

# apply migrations
cd apps/api
uv run alembic upgrade head

# run the API (PYTHONPATH must include the repo root so `workers.*` resolves for the Celery
# task client; --app-dir so `app.main:app` resolves without installing this as a package)
cd ..
PYTHONPATH="$PWD" uv run uvicorn app.main:app --app-dir apps/api --reload

# PowerShell equivalent
$env:PYTHONPATH = (Get-Location).Path
uv run uvicorn app.main:app --app-dir apps/api --reload

# run worker-cpu (Celery) -- run from the repo root so both `app` and `workers` resolve
PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}:$PWD/apps/api" uv run celery -A workers.cpu.worker worker -Q cpu,maintenance --beat --loglevel=info

# PowerShell equivalent
$env:PYTHONPATH = "$(Get-Location).Path;$(Join-Path (Get-Location) 'apps\api')"
uv run celery -A workers.cpu.worker worker -Q cpu,maintenance --beat --loglevel=info
```

## Tests

```bash
# from the repo root
uv run pytest tests/unit                 # no DB/Redis required
uv run pytest tests/integration          # requires Postgres + Redis reachable (see conftest.py)
```

Integration tests default to `shorts_maker_test` on the same Postgres instance as dev
(`SHORTS_MAKER_TEST_DATABASE_URL` to override) and drop/recreate every table before each test
module via `Base.metadata` -- never run them against a database with real data.

## What's implemented (Phase 1 scope)

- Auth: register/login/refresh/logout/me, Argon2id + rotating refresh tokens.
- Uploads: presigned-URL issuance (local filesystem adapter for D0; R2 for D1+) + completion.
- Jobs: creation with immutable, validated `export_profile_id` (impl plan §3.10), status,
  cancel, candidate listing.
- Candidates: edit/reframe/accept/reject request validation and DB-level lifecycle
  transitions, plus job-level rerank (new immutable `display_selection` revision).
- Celery app + the 6 fixed queues (`io, cpu, llm, gpu_dispatch, render, maintenance`).

## What's intentionally NOT implemented yet

The actual pipeline algorithms (normalization, ASR, discovery, edit planning, verification,
hook analysis, reframing, ranking, rendering) are Phases 2-13. `workers/cpu/tasks.py`'s task
bodies raise `NotImplementedError` on purpose (impl plan §13.4: never invent a later phase's
behavior) -- Phase 1 only proves the request/DB/queue contract those phases will fill in.
