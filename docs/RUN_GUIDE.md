# shorts-maker — how to run it (state: Phases 0–3 contract-complete, Phase 4 partial)

## 0. What you need on your machine
- Linux (Ubuntu 24.04 recommended), Python 3.12, `uv` (https://docs.astral.sh/uv/), Node >= 22 + pnpm 12 (only for the web app), FFmpeg/ffprobe on PATH, Docker.
- Everything below runs from the repo root (`shorts-maker/`).

## 1. Install Python dependencies (recreates .venv; it is NOT in the zip)
    uv sync --group test --group api --group media --group worker
Do NOT add `--group ml` unless you are provisioning real models (it pulls the large torch build).

## 2. Start Postgres + Redis (there is no docker-compose file in the repo yet)
    docker run -d --name sm-pg -p 5432:5432 -e POSTGRES_USER=shorts_maker -e POSTGRES_PASSWORD=shorts_maker_dev -e POSTGRES_DB=shorts_maker_test pgvector/pgvector:pg18
    docker run -d --name sm-redis -p 6379:6379 redis:7.4
    docker exec sm-pg psql -U shorts_maker -d shorts_maker_test -c "CREATE DATABASE shorts_maker_dev;"
(The plan pins PostgreSQL 18.6 / pgvector 0.8.2 / Redis 7.1; these tags are the closest convenient images — re-verify against the exact pins.)

## 3. Run the tests
    make test                                   # everything (unit + contract + integration); integration needs step 2
    uv run pytest tests/unit tests/contract -q  # no database needed (360 tests)
    uv run pytest tests/integration -q          # needs Postgres + Redis (59 tests, ~3 min)
    uv run pytest tests/unit/test_phase4_analysis.py -q   # the Phase-4 tests only (27)
Expected today: all pass; a few tests skip with explicit reasons (FFmpeg 9.x pin, D1-only hosted tests, real-model gate).

## 4. Run the API
From the repository root in PowerShell:

    $repoRoot = (Get-Location).Path
    $env:PYTHONPATH = "$repoRoot;$repoRoot\apps\api"
    uv run alembic -c apps/api/alembic.ini upgrade head
    uv run uvicorn app.main:app --app-dir apps/api --reload

Do not use `apps/api/app.main:app`: Uvicorn expects the Python module path
`app.main:app`. The repository root must remain on `PYTHONPATH` so the API can import
the top-level `workers` package.

Settings come from env vars prefixed `SHORTS_MAKER_` (e.g. `SHORTS_MAKER_DATABASE_URL`, `SHORTS_MAKER_REDIS_URL`) or a `.env`.

## 5. Run the web app (optional)
    pnpm install && pnpm dev:web

## 6. Try the Phase-4 pieces by hand (fixtures are in packages/fixtures/media)
    uv run python - <<'PY'
    import json, subprocess
    from shorts_config import load_config
    from workers.cpu.shot_map import compute_shot_map
    f = "packages/fixtures/media/fixture_event_6_8s.mp4"
    st = json.loads(subprocess.check_output(["ffprobe","-v","error","-count_frames","-select_streams","v:0",
        "-show_entries","stream=nb_read_frames,r_frame_rate","-of","json",f]))["streams"][0]
    a,b = map(int, st["r_frame_rate"].split("/"))
    print(compute_shot_map(f, fps=a/b, expected_frame_count=int(st["nb_read_frames"]), cfg=load_config())["shots"])
    PY

## 7. What you CANNOT run yet (and why)
- `make smoke-real` (Phase-3 exit gate): needs real models. Steps: set `HF_TOKEN` (accept the pyannote community-1 terms), then
  `make materialize-models` (downloads whisper/alignment/diarization AND the Phase-4 embedding model), put `lid.176.ftz` in `models/fasttext/`
  (sha256 sidecar already committed), put NLTK `punkt_tab` (english) under `models/nltk_data/`, then `make smoke-real`. Without these it FAILS on purpose.
- The Phase-4 visual extractor, DB table for embeddings, stage wiring and IT-4-5: not built (blocked on the answers in docs/PHASE_GAPS_ANSWER_SHEET.md).
