# shorts-maker — implementation status

**Source of truth (both required):**
1. `docs/spec/virality_shorts_plan_v5_0.md` — product/behavior authority.
2. `docs/spec/virality_shorts_implementation_plan_v1_2.md` — technology/execution authority.

Copied verbatim into this repo so a clean clone is self-contained (impl plan §13.20).

**Standing rule for this build (repeated here so it survives handoff):** follow the
implementation plan exactly; cross-check every step against v5.0. If the implementation plan
contradicts itself, or contradicts v5.0, or a real JSON Schema/field can't be built without
inventing something neither document specifies — **stop and ask; never resolve it
unilaterally.**

**Environment note (revised 2026-09-27 — corrects the 2026-09-23 note below):** the original
Phase 0 pass stated this sandbox "has no Docker, Postgres, Redis, or GPU." That was true for
*Docker* and *GPU*, but **wrong for Postgres/Redis**: both install cleanly via `apt` in this
container (`apt-get install postgresql redis-server`) and were actually run for this session —
every Phase 1 integration test in `tests/integration/` executed against a real PostgreSQL and
real Redis, not a plan or a mock. Two things to know before trusting that at face value:
- **Version drift, sandbox-only:** what `apt` installed here is PostgreSQL **16** + pgvector
  **0.6.0** + Redis **7.0.15** — not the impl plan's pinned PostgreSQL **18.6** / pgvector
  **0.8.2** / Redis OSS **7.1** (§1.4/§1.5). This proves the schema, migrations, and API logic
  are correct against a real Postgres/Redis; it does **not** prove they're correct against the
  *exact pinned* versions. Re-run `tests/integration/` against the real pinned-version Docker
  Compose stack before fully trusting this on the actual dev stack.
- **Process stability:** this sandbox does not keep background daemons alive reliably across
  tool calls (Postgres/Redis were both observed to die and need restarting mid-session, with no
  code-level cause). If you pick this work up in a similar sandbox, check `pg_isready` /
  `redis-cli ping` before assuming either is still up, and restart if not
  (`service postgresql start`, `redis-server --daemonize yes --save ""`). Your real local D0
  Docker Compose setup does not have this problem — containers stay up.

GPU is still entirely unavailable here; anything needing WhisperX/embeddings/CV inference on
real media is still real-local-environment-only (impl plan §1.6.2).

---

## 2026-09-23 decision log

Six open questions were raised after the first Phase 0 pass; the owner resolved them same-day.
Recorded here verbatim-in-substance so the reasoning isn't lost:

| # | Decision | Where implemented |
|---|---|---|
| 1 | `render_profile_v1` keeps `profile_version`, not `stage_version` — distinct concepts (stage provenance vs. export-profile identity); permanent, not a gap. | `packages/schemas/json/render_profile_v1.schema.json`; regression tests in `test_phase0_schemas.py` |
| 2 | Use `uv` for Python dependency management; commit `pyproject.toml` + `uv.lock`; same lockfile in CI/Docker/local. | `pyproject.toml` (`[tool.uv]`, workspace), `uv.lock` |
| 3 | Implement `BoundaryMap`, `EditUnit`, `EvaluationReport`, `CalibrationReport`, `AdoptionDecision` schemas during Phase 0; don't invent fields not supported by v5.0. | 2 of 5 fully implemented (`EditUnit`, `boundary_event`/`super_unit`). `EvaluationReport`/`CalibrationReport`/`AdoptionDecision` confirmed as documented spec gaps, scoped to block only Phase 15 (`docs/implementation_constraints.md`). `BoundaryMap`'s container level: **resolved 2026-09-27, owner decision — deferred to Phase 5** (its per-event shape is done; the container wrapper falls out of how discovery actually consumes it, per the original recommendation). |
| 4 | Use PySceneDetect 0.7.x's `ContentDetector` (threshold 27.0, min_scene_len 15, luma_only false). | Empirically verified `pyscenedetect` doesn't exist on PyPI; `scenedetect` 0.7.1 is the real distribution. `pyproject.toml`, `tests/unit/test_phase0_scenedetect_dependency.py` |
| 5 | `canonical_json@1`: sorted keys, compact, UTF-8, preserved array order, reject NaN/Infinity, hash exact bytes, single serializer everywhere. | `packages/config/src/shorts_config/canonical.py`, `tests/unit/test_phase0_canonical_json_v1.py` (23 fixture tests) |
| 6 | One immutable `config@1` registry; Python/TS read generated/read-only bindings only; keep `context_dependency` separate from `opening_standalone`; don't divide Tier 2 coherence by 5 twice. | Registry unchanged in shape; **TS bindings now exist** (`packages/schemas/typescript`, 2026-09-27 — see below); the two correctness rules recorded in `docs/implementation_constraints.md` |
| 7 | Preserve v5.0/v1.2's exact initial values/weights; no implementation-time tuning; later calibration needs a new config version + immutable history. | Full constant-reconciliation audit run against v5.0; config@1.json has zero *retunes*, only *additions* of previously-missing named constants |

Full detail on decision 7's constant audit, and the decision-3 schema-gap audit table, is
preserved in git history / the previous revision of this file — trimmed here to keep this
document navigable now that Phase 0 is closed. The important parts (what's a genuine spec gap
vs. what was inferred and flagged) are unchanged and still hold.

---

## 2026-09-27 session — Phase 0 closed out, Phase 1 built and tested

Owner reviewed the Phase 0 status and made explicit decisions on every open item (recorded
verbatim in substance):

| Item | Decision |
|---|---|
| BoundaryMap container | Defer to Phase 5 (as recommended) |
| `EditPlan`, `VerifiedEditPlan`, `HookAnalysis`, verification-result (2.36.9.8) schemas | Implement from the literal v5.0 JSON — "transcription work, not an invitation to introduce new semantics" |
| Frontend scaffold (0.3) | Complete |
| `sentence_seg_v1`/alignment/TextTiling contracts (0.7) | Complete |
| Fixtures (0.9) | Complete |
| Thin vertical slice (0.10) | Complete — **see caveat below; this one could not actually be done as literally specified** |
| Phase 3/4-dependent helpers | Keep deferred |
| Phase 1 implementation | Yes, with explicit test boundaries |

Also corrected a bookkeeping error from the 2026-09-23 note: task 0.6 says "the remaining
helpers" but names **six**, not five (`event_safe_cut_v1`, `latest_safe_before`,
`earliest_safe_after`, `local_nonspeech_rms_v1`, `d_clean_v1`, `super_unit_embedding_v1`) — the
old count was simply wrong, not a scope change.

### 0.10 thin vertical slice — what actually happened

This one could not be completed as literally written. Impl plan Phase 0.10 asks to "execute
one complete deterministic path: normalize → ASR/language gate/alignment → analysis →
discovery → one qualified region → one verified edit plan → reframe → captions → render" — that
is Phases 2 through 10's actual algorithms, none of which can exist before those phases are
built (there is no discovery engine, no edit planner, no verifier, no reframer to run). This
was already flagged in the 2026-09-23 note ("0.10 ... depends on Phases 1–13") and remains
true; building it now would mean faking the very algorithms those phases are for.

**What was done instead**, since silently skipping it felt worse than a partial, honest
substitute: `docs/implementation_constraints.md` now carries a `thin_vertical_slice_harness`
section recording exactly which stage each future phase must wire in
(`packages/fixtures/media/fixture_speech_45s.mp4` is the fixture already earmarked for it), so
the slice can actually be run for real the moment Phase 10 lands, rather than rediscovering
what "done" means 10 phases from now. **This is flagged, not resolved** — if a different
resolution was wanted (e.g. a literal no-op placeholder script committed now), say so.

### Schemas (0.4) — now complete

Added `edit_plan_v1`, `verified_edit_plan_v1`, `hook_analysis_v1`, `verification_result_v1`
(the last has no artifact-type name given in v5.0 prose; named consistent with the impl plan's
own phrase "the verification-result artifact (2.36.9.8)" and the artifact's own
`stage_version: verifier@2` / `verification_id` fields). All four transcribed from v5.0's
literal JSON examples; every place a real ambiguity existed (e.g. `event`/`reframe` nullability,
`normalized_issues`' shape after cut_index→cut_id resolution, the bridge-test fields' nullability
when a repair "closes the cut completely") is flagged in the schema's own `description` field,
not silently resolved. All 16 artifact schemas (plus the `_identity` fragment, which is `$ref`-only and not generated) now generate both Python (`datamodel-code-generator`)
and **TypeScript** (`json-schema-to-typescript`, new this session — `packages/schemas/typescript/`)
models from the same source, drift-checked by tests in both languages.

### Frontend scaffold (0.3) — now complete

`apps/web`: Next.js 16.3.0 / React 19.2.8, App Router, strict TypeScript, Tailwind CSS 4, Zod,
TanStack Query (wired via a `Providers` client component). Root pnpm workspace
(`pnpm-workspace.yaml`) covering `apps/*` and `packages/schemas/typescript`. Deliberately
dropped `next/font/google` (Geist) in favor of a system-font stack — the font CDN isn't
reachable from this sandbox's network policy, and depending on it made the build fragile for no
product reason; a real dev machine could restore it, but a system stack is arguably the more
robust default anyway. `pnpm --filter web build/lint/exec tsc --noEmit` all pass clean.

### Deterministic analysis primitives (0.7) — now complete

`packages/config/src/shorts_config/analysis_primitives.py`: `sentence_seg_v1` (exact v5.0 2.14.1
algorithm — terminal-punctuation/gap+trigger rule, then recursive length-based splitting with
tie-break-to-earliest-gap and the `synthetic_boundary` fallback), `TextTiling_depth_v1` (with an
explicitly flagged interpretation of "complete pair of windows" — see the function's own
docstring), a forced-alignment gate (`forced_alignment_gate_v1`/`AlignmentUnavailable`), the
no-diarization fallback (`speaker_id_v1`/`speaker_dependent_feature_v1`), and an embedding-
provenance validator grounded in the exact "fixed model, tokenizer, precision and deterministic
backend settings" sentence. 34 unit tests, all passing, all against synthetic fixtures (no real
audio/embeddings needed — that's Phase 3/4's job, per the whole point of building these as pure
functions in Phase 0).

### Fixtures (0.9) — now complete

`packages/fixtures/media/`: 5 small (704 KB total) synthetic MP4s, generated **entirely
offline** via ffmpeg's built-in `flite` filter for speech (libflite, no network, no external
TTS) plus `lavfi` color/noise sources — covering the 5 media scenarios (speech ≥25 words,
speech <25 words, 6–8s event-led, multi-speaker, screen-content). Each has a
`.ground_truth.json` with the exact authored transcript/timing (genuine ground truth, since the
text was written, not transcribed) and an explicit caveat that the visual tracks are synthetic
(no real face — don't use for face-detection-accuracy testing without regenerating with real
footage). `scripts/generate_media_fixtures.sh` reproduces them from scratch, verified to
reproduce the same durations. `packages/fixtures/scenarios/`: 5 JSON fixtures for the
non-media scenarios (no-diarization path, LLM transport-error path, LLM invalid-output path per
violated-rule variant, study-ratio generation, user-edit rejection request bodies) — see
`packages/fixtures/MANIFEST.md` for the full mapping and the one thing NOT included (real
word/sentence/boundary snapshots, which need Phase 3/4/5's actual pipeline to produce honestly).

### Phase 1 — built and tested against real Postgres + Redis

Everything in impl plan §5 Phase 1: `apps/api` (FastAPI, SQLAlchemy 2.x async, Alembic —
real migration generated via `alembic revision --autogenerate`, verified to apply and downgrade
cleanly), `workers/` (Celery app with the 6 fixed queues, verified to start and register tasks
against real Redis), all exact endpoints from impl plan §1.4 (auth register/login/refresh/logout,
**`GET /v1/me` at the correct top-level path** — caught and fixed a routing bug where it was
first placed under `/v1/auth/me`), uploads (presigned-URL local-filesystem adapter for D0, real
R2/boto3 offline-signing adapter for D1+), jobs (export-profile validation reusing
`shorts_config.Config.profile()`, never a second validation implementation), candidates
(edit/reframe/accept/reject with the exact request-body shapes from impl plan §1.4, DB-level
lifecycle transitions, task-queue enqueueing to intentionally-`NotImplementedError` stubs for
the Phase 7/8/10 algorithm bodies), and job-level rerank (creates a new immutable
`display_selection` revision, never updates one in place).

24 integration tests (real Postgres + real Redis) + 39 DB-independent unit tests, all passing,
including the 5 exact-named tests impl plan Phase 1 mandates
(`test_job_requires_valid_export_profile`, `test_export_profile_immutable`,
`test_profile_hash_persisted_on_job`, `test_job_cannot_attach_second_profile`,
`test_candidate_state_not_stored_as_job_state`).

Design note worth flagging explicitly: most of the 22 tables in impl plan §1.2's migration list
are metadata/pointer envelopes (config/stage/schema identity + the few columns a router or
worker actually filters/joins on), not full duplicates of each artifact's JSON Schema as
relational columns — the JSON Schema remains the one canonical content schema (impl plan §4.3);
the DB row points at the content-addressed artifact file (impl plan §3.1). This wasn't a
literal instruction either way; flagged as a design choice, not a spec transcription.

See `apps/api/README.md` for exact run/test commands.

---

## Status by phase (impl plan §5, execution order §12)

| Phase | Status | Notes |
|---|---|---|
| 0 — Repo, contracts, reproducibility | **Closed** (with the 0.10 caveat above) | |
| 1 — Infrastructure, auth, upload, job control | **Built and tested** (real Postgres/Redis, this sandbox) | Re-verify against pinned-version Docker Compose before D1 promotion |
| 2–18 | Not started | — |

### Phase 0 checklist (impl plan §5, Phase 0 tasks 0.1–0.10)

- [x] 0.1 Monorepo tree + dotfiles + Makefile + this README.
- [x] 0.2 Python 3.12 via uv, Ruff + Pytest + MyPy. `uv.lock` committed.
- [x] 0.3 Frontend scaffold — Next.js 16.3, strict TS, Tailwind 4, Zod, TanStack Query.
- [x] 0.4 Canonical JSON Schemas — **16 of 16 tractable artifacts implemented** (all of v5.0's
      named artifacts except `BoundaryMap`'s container level, `EvaluationReport`,
      `CalibrationReport`, `AdoptionDecision` — see decision log; those four remain genuine,
      recorded spec gaps, not oversights). Python + TypeScript models generated and drift-checked
      for all 16.
- [x] 0.5 Config registry — unchanged in shape from 2026-09-23, still the sole source.
- [~] 0.6 Shared helpers — `robust_z_v1` only; the other **six** (corrected count) remain
      deferred pending Phase 3/4 artifact shapes, per owner decision.
- [x] 0.7 `sentence_seg_v1`, forced-alignment gate, `TextTiling_depth_v1`, embedding provenance,
      no-diarization fallback — implemented as pure, tested library contracts.
- [x] 0.9 Fixtures/snapshots — 5 media + 5 scenario fixtures, all 10 task-0.9 items covered.
- [~] 0.10 Thin vertical slice — **could not be literally completed** (needs Phases 2-10's
      actual algorithms); a harness plan is recorded instead. See the caveat above.

**Phase 0 exit gate: effectively met**, with 0.6 (by design, deferred) and 0.10 (structurally
impossible before Phase 10) as the two knowingly-open exceptions — both are pre-existing,
understood gaps, not new surprises.

### What's verified right now

```bash
cd shorts-maker

# Python
uv sync --group test --group api --group media
uv run pytest tests/unit -q          # 218 passed
uv run pytest tests/integration -q   # 24 passed -- needs real Postgres+Redis, see the
                                      # environment note at the top of this file
ruff check .

# Frontend / schemas
pnpm install
pnpm --filter web build && pnpm --filter web lint && pnpm --filter web exec tsc --noEmit
pnpm --filter @shorts-maker/schemas-typescript check   # TS types up to date with the JSON Schemas

# Regeneration entry points (never hand-edit their output)
uv run python3 scripts/extract_prompts.py
uv run python3 scripts/gen_types.py
pnpm --filter @shorts-maker/schemas-typescript generate
bash scripts/generate_media_fixtures.sh

# Alembic (needs Postgres reachable)
cd apps/api && uv run alembic upgrade head
```

---

## Open items carried forward

1. **Re-verify Phase 1 against the actual pinned versions** (PostgreSQL 18.6, pgvector 0.8.2,
   Redis OSS 7.1) on the real local D0 Docker Compose stack — everything here was proven against
   whatever `apt` had available in this sandbox (16 / 0.6.0 / 7.0.15), which is a strong signal
   but not the same claim.
2. **0.10's resolution** (harness plan recorded, not a literal completion) — confirm this is
   the wanted outcome, or say what else to do with it.

Everything else from the 2026-09-23 and 2026-09-27 decision logs is closed.

---

## 2026-09-29 decision log — Phase 2 (normalization) + dispatch boundary

Delivered: `packages/fixtures/media` normalization (`workers/cpu/media_probe.py`,
`workers/cpu/normalization.py`), the generic stage-idempotency contract (`workers/shared/
stage_runner.py`, impl plan §3.2/§3.3), the `GPUExecutionProvider` boundary (`workers/shared/
gpu_provider.py`), content-addressed binary-artifact keys (`workers/shared/artifact_keys.py`),
the `NORMALIZING` Celery task + stage executor (`workers/cpu/stage_normalize.py`, `workers/cpu/
tasks.py::normalize_source_video`), and the full `POST /v1/uploads/.../complete` → `POST /v1/jobs`
→ dispatch flow. IT-2-3 passes on all 5 canonical fixtures against real (unpinned, see the
2026-09-27 note above) Postgres/Redis, including idempotent re-run.

**Owner decisions this session (all confirmed before implementing, per the standing rule):**
1. **Binary artifact paths**: same content-addressed scheme as JSON artifacts, real extension
   kept (`.mp4`/`.wav`/`.json`) — `artifact_storage_key()` enforces the type→extension mapping.
2. **`media_manifest.json` schema**: **BLOCKED_BY_SPEC, still open.** Neither source document
   gives a field-level contract (types, required/optional, fps representation — numeric vs
   rational, nullability). `NORMALIZING` deliberately does **not** write this artifact.
   `test_normalized_manifest_schema` (impl plan Phase 2 unit test list) is **not implemented**
   for the same reason. Needs an owner-defined schema before this can close.
3. **`GPUExecutionProvider` signatures**: implemented as a conceptual infra contract now
   (`submit`/`get_status`/`cancel`, `provider_job_id`-keyed), flagged as implementation-level
   (not a v5.0/impl-plan-literal field contract) pending Phase 3 ratification. Both
   `LocalROCmGPUProvider`/`ModalGPUProvider` bodies raise `NotImplementedError` — Phase 3's job.
4. **No-audio sources**: supported, not rejected. `validate_source` only rejects on missing
   *video* stream / bad duration. A silent source normalizes video-only;
   `NormalizedMedia.analysis_audio_pending_spec=True` and `analysis_audio_path=None`. What a
   silent source's `analysis_audio.wav` *should* contain (generated digital silence vs. absent)
   is **still open** — `build_analysis_audio_command` raises `BlockedBySpec` if called for a
   no-audio source, so the gap can't be silently papered over later.
5. **CFR predicate**: **not implemented.** No normative definition exists in either document
   (equality of `r_frame_rate`/`avg_frame_rate` was proposed and explicitly rejected — those
   are stream-rate metadata, not a timestamp-spacing guarantee). `select_normalized_fps` always
   returns `(30, "cfr_predicate_unspecified")`. Source-FPS preservation is unimplemented by
   design until an owner defines the predicate (authoritative fields, timestamp tolerance, VFR
   handling, 29.97/59.94 treatment).
6. **Fixture count**: IT-2-3 runs all 5 canonical fixtures (not the plan's literal "three"),
   parametrized, using probe-derived capability (`has_audio`) rather than fixture names/count.
7. **FFmpeg pin**: sandbox has 6.1.1, plan requires 9.x. `test_ffmpeg_pin_9x` skips with an
   explicit `BLOCKED_BY_DEPENDENCY` message rather than passing silently; every other media test
   ran against 6.1.1 and is **UNPINNED**, same caveat as Postgres/Redis above — re-run on the
   pinned FFmpeg before trusting media-behavior tests at face value.
8. **`-fflags +bitexact`**: deliberately **not** added; not in the normative normalize contract
   (§2.2), and `test_command_builder_is_deterministic_and_pinned_flags` asserts it's absent.
9. **Raw-upload → first-stage input-artifact bootstrap**: `Artifact.job_id` made **nullable**;
   added `Artifact.source_video_id` (nullable FK) + a DB `CHECK` enforcing exactly one of the
   two is set. Convention (confirmed, strict — **no convenience population**): `artifact_type ==
   "raw_source"` → `source_video_id` set, `job_id` NULL, committed atomically with `SourceVideo`
   at upload-complete time, checksum **server-computed** (`storage.read_bytes` + sha256 — the
   client-supplied `checksum_sha256` on `CompleteUploadRequest` is untrusted/optional and never
   used for artifact identity). Every other artifact type: `job_id` set, `source_video_id` NULL,
   always. Migration: `apps/api/alembic/versions/74099a393025_*.py` (round-trip tested:
   upgrade → downgrade → upgrade, on real Postgres).
10. **Job-state dispatch sequencing** (owner-corrected mid-session): `POST /v1/jobs` commits
    `CREATED` **first**, as its own transaction/durability boundary, and returns that state in
    the response *regardless* of what happens next in the same request. Dispatch (Celery
    `send_task` with a deterministic `task_id`, computed from `workers.shared.stage_runner.
    compute_stage_input_sha256([raw_source_artifact_id])`) and the `job.state = "NORMALIZING"`
    write happen as a **second, independent** step/commit — explicitly *not* one transaction
    spanning the DB and the broker, to avoid the DB/queue atomicity problem. If step 2 fails
    after step 1 committed, the job is left stuck in `CREATED` with nothing running; there is
    **no outbox/reconciler** — that's an explicitly-deferred Phase 18 reliability concern
    (§18.2 "job resume from last successful artifact"), not solved here.

**Bugs I found and fixed in my own code before they shipped (not spec questions, noted for
transparency, not because they needed sign-off):**
- Two different import spellings (`app.*` vs `apps.api.app.*`) for the same package would have
  produced two distinct `Base`/metadata objects under pytest's `pythonpath`. Standardized on
  `app.*` everywhere (matches the existing Phase 1 convention, including `conftest.py`).
- `stage_normalize.py` originally took one `StorageAdapter` and used it for both reading the
  raw upload (which lives in the **source** bucket) and writing normalized artifacts (**artifacts**
  bucket) — silently wrong the moment source/artifacts buckets actually differ. Now takes
  `source_storage` and `artifact_storage` explicitly (both call sites — the Celery task and
  IT-2-3 — updated).
- `StorageAdapter.write_bytes` was labeled "test-only" by Phase 1 (nothing needed a real
  server-side write path yet). It's the real worker artifact-persistence primitive per §1.6.1
  ("workers read/write objects directly") — promoted to the Protocol, `R2Storage.write_bytes`
  implemented for real via `put_object` (previously didn't exist), and `R2Storage.read_bytes`
  implemented for real via `get_object` (previously raised `NotImplementedError` for no reason
  — trivial GET, unlike the ffmpeg-source-local-path case in `stage_normalize.py`, which
  genuinely needs temp-file-staging design and is left as a real, documented D1 gap).
- `[tool.mypy]` was named as a required tool (§0.2) but never actually configured anywhere in
  `pyproject.toml`. Added a minimal config matching pytest's existing `pythonpath`.
- A self-inflicted `pyproject.toml` edit briefly deleted the `[tool.pytest.ini_options]` header
  entirely (caught immediately by re-parsing the TOML and re-running the suite before treating
  anything as "done" — flagging the near-miss here only so a future reviewer isn't surprised to
  see it show up once in this log and never again).

**Verified this session (unpinned versions, see caveat above):** 261 unit+integration tests
pass, 3 correctly skip (FFmpeg pin ×1, pre-existing D1-only skips ×2); `ruff check .` clean;
`mypy` clean on every new/touched module; Alembic migration round-trips (upgrade → downgrade →
upgrade) on real Postgres.

**Still open, carried forward — do not resolve unilaterally:**
1. `media_manifest.json` field-level schema (types, fps representation, nullability, units).
2. CFR detection predicate (authoritative ffprobe fields, tolerance, VFR/29.97 handling).
3. Silent-source `analysis_audio.wav` semantics (generated digital silence, or genuinely absent).
4. `GPUExecutionProvider` exact field-level signature — ratify or amend before Phase 3 depends
   on it for real ASR/diarization dispatch.
5. Re-verify this entire phase against the actual pinned FFmpeg 9.x / PostgreSQL 18.6 / pgvector
   0.8.2 / Redis OSS 7.1 on the real local D0 Docker Compose stack (carried forward from Phase 1,
   still unresolved — this sandbox cannot install FFmpeg 9.x, and Postgres/Redis are still
   whatever `apt` provides).
6. IT-2-3's D1 half (hosted Railway/R2) — not run, per the D0/D1 promotion rule (§1.16);
   `source_storage._path`-based ffmpeg reads and `R2Storage.read_bytes` for the raw-upload
   checksum are both real D1 gaps now, not just theoretical ones (flagged inline in code).

---

## 2026-09-30 decision log — Phase 3 (ASR / alignment / sentences / diarization preflight)

**Owner decisions (2026-09-30), implemented as stated.** C1 diarization is attempted for every
speech-bearing source (success optional; no multi-speaker pre-detector). C2 no new job states:
Phase 3 runs as stage_runs (`asr`, `language_gate`, `forced_alignment`, `diarization`,
`sentence_segmentation`) while the job stays `NORMALIZED`; `NORMALIZED -> ANALYZING` only after
the language gate passed and alignment succeeded or is `not_applicable`; failures -> `FAILED`.
C3 IT-3-4 is a pure Phase-3 -> Phase-4 artifact-boundary test (embedding determinism is Phase 4).
C4 diarization failure is non-fatal: `not_available_in_stage` (not run) vs `extraction_failed`
(ran and failed); cause kept in provenance. G1 `transcript_v1` schema added. G2 ids are
`W/S/T` + six-digit 1-based ordinals, never from time/text; `U` is a separate downstream
namespace. G4 unaligned words keep text with null timing, never interpolated, never a cut anchor.
G5 max-overlap word->speaker, no invented min-turn/merge constants, raw turns preserved. G6 no
audio stream -> no WAV, no GPU call, zero-word transcript, alignment `not_applicable`. G7
`gpu_dispatch` ratified, `provider_job_id` opaque. G8 `pyannote-audio` + `fasttext` added to the
`ml` group and locked; `lid.176.ftz` is a vendored hash-pinned artifact (`models/fasttext/`).

**Built:** `transcript_v1` + `phase3_stage_output_v1` schemas (+ generated Python/TS);
`workers/cpu/{language_gate,speaker_assignment,transcript_builder,stage_transcript}.py`;
`workers/gpu/{backends,execute,tasks,worker}.py`; `LocalROCmGPUProvider` (real Celery
`send_task` on `gpu_dispatch`); `workers/shared/job_state.py` (compare-and-set transitions);
normalize task now does `NORMALIZING -> NORMALIZED` then dispatches
`workers.cpu.run_transcript_preflight` as a separate non-atomic step; `config@1`
`runtime_contracts` + `Config.runtime_contract()` (raises `ConfigSpecGap` while blocked);
`sentence_seg_v1` made null-timing-safe + `validate_cut_anchor_timing_v1`. 305 tests pass
(was 261): 26 unit + 10 integration for Phase 3.

**STILL BLOCKED (not guessed):**
- **G3 — `asr_runtime@1`, `alignment_runtime@1`, `diarization_runtime@1` values.** Stubs exist in
  `config@1` with `status: BLOCKED_BY_SPEC`; `default_backends()` raises `BlockedBySpec`. No
  WhisperX / pyannote adapter is written, because adapters must be written against frozen values.
  Real ASR/alignment/diarization has therefore **never run**; everything is tested with fakes
  behind the production Protocols. The "~144 words on fixture_speech_45s" sanity check is unrun.
- **fastText + numpy 2 (dependency conflict, verified in sandbox):** `fasttext 0.9.3`'s
  `predict()` calls `np.array(probs, copy=False)` which raises under numpy >= 2 (lock has 2.5.3).
  `FastTextLanguageID` fails closed with `BLOCKED_BY_DEPENDENCY: fasttext_numpy2_incompatible`.
  Owner must choose the fix (numpy < 2 pin, maintained fork, or other).
- `lid.176.ftz` + `.sha256` not provisioned (sandbox cannot fetch it).
- `media_manifest_v1` field schema still unwritten (G6 resolved only the silent-source branch).

**Implementer's readings flagged for owner confirmation** (none contradict either spec, but
neither spec states them): (1) cut-anchor predicate = first AND last word of every sentence must
have forced-aligned start+end, else `alignment_unavailable` (`validate_cut_anchor_timing_v1`);
(2) language sample = ASR segments whose start is < 60 s after the first segment's start;
(3) gate failure mapping: non-en with conf >= 0.90 -> `unsupported_language`, everything else
non-passing -> `language_uncertain`; (4) sentence `speaker_id` = first word's speaker;
(5) a backend crash is `PERMANENT_MODEL` (not retried); only provider-reported TRANSIENT/TIMEOUT
retry, bounded by `STAGE_MAX_ATTEMPTS`; (6) `phase3_stage_output_v1` intermediate artifact
(asr/alignment/diarization/language_gate outputs) is an implementation-level type, not in v5.0;
(7) `GPUJobStatus.outputs` descriptors replace `output_artifact_ids` (GPU worker writes bytes to
storage but never DB rows) and the GPU worker reads the DB read-only to resolve input artifact ids;
(8) `poll_interval_s` / `poll_timeout_s` are operational parameters outside `config@1`; (9) the
NORMALIZING -> NORMALIZED transition lives in the normalize task (nothing set it in Phase 2).

**Known limitations carried forward:** no transactional outbox (a crash between the
`NORMALIZED` commit and `send_task` strands the job in `NORMALIZED`; Phase 18 reliability work);
Phase 3 stage commits are required before each GPU submit (the GPU worker uses its own session).

---

## 2026-10-02 decision log — Phase 3 review resolutions

**Implemented as decided:** #1 cut-anchor usability is per sentence edge (`start_timing_usable` /
`end_timing_usable`, null timing, never synthesized/borrowed; the only job-level failure is "words
exist but none received forced-aligned timing"); #2/#3 language sample and the exact gate mapping
(non-en at any confidence -> `unsupported_language`; en < 0.90 -> `language_uncertain`; < 20 words ->
`not_applicable`); #4 sentence `speaker_id` = first word's speaker; #5 unexpected GPU-worker
crashes are NOT caught (they propagate, the provider reports TRANSIENT, the orchestrator retries
up to `STAGE_MAX_ATTEMPTS`; `PERMANENT_MODEL` only for declared incompatibility); #6
`phase3_stage_output_v1` is an internal transport envelope under `transport/` -- no Artifact row, no
lineage; descriptors live in `stage_runs.execution_metadata`; `transcript_v1` (+ `media_manifest_v1`)
are the only canonical artifacts; #7 `GPUJobStatus.outputs` descriptors, the GPU worker never writes
DB rows; #8 effective poll interval / timeout / attempts / provider job ids recorded per stage run;
#9 durable dispatch (below); #10 recorded for Phase 7 (keep the run-on guard at
`LONG_UNIT_S=15` / `SPLIT_PAUSE_MS=500`, no G0; add a zero-trigger normal-path test, a synthetic
overlong-unit test and `run_on_guard_triggered_count`); #12 `media_manifest_v1` defined and written
by NORMALIZING (artifact ids are deterministic uuid5); #13 PTS-based CFR predicate
(`workers/cpu/cfr.py`) replaces the "always 30 FPS" placeholder -- the 24 fps fixtures are now
preserved at 24.

**Durable Phase-3 dispatch (#9):** one transaction commits normalized artifacts + manifest +
`NORMALIZING -> NORMALIZED` + a `phase3_dispatch_intents` row; dispatch (send-then-mark, leased)
happens afterwards; Phase 3 claims / heartbeats / completes the intent; `reconcile_phase3_dispatch`
(beat, `maintenance` queue, every 15 s) resubmits PENDING and lease-expired intents and creates
the intent for NORMALIZED jobs that have none. Operational values reuse the impl plan's Phase 18.2
figures (heartbeat 15 s, lease 60 s) because nothing else is specified. Migration
`c3d41f7a9b20` (also adds `stage_runs.execution_metadata`) was upgraded / downgraded / re-upgraded
against a scratch Postgres. The cpu worker must now run `-Q cpu,maintenance --beat`
(apps/api/README.md updated).

**NOT implemented -- contradiction, awaiting owner (#11):** pinning `numpy == 1.26.4` is
unsatisfiable. `uv lock` fails: `pyannote-audio >= 4.0` (required for
`speaker-diarization-community-1`, and by the locked whisperx) needs numpy >= 2.0.2. The pin was
reverted; `uv.lock` is unchanged from the 2026-09-30 state. fastText therefore still fails closed
(`fasttext_numpy2_incompatible`). Options are in the owner message.

**Still blocked:** G3 runtime values (no real adapters); `lid.176.ftz` + sha256 are not provisioned
(the sandbox cannot reach any host that serves it).

**New small flags (implemented, unconfirmed):** (a) the transport envelope is written under
`transport/` and never cleaned up (needs a retention rule); (b) departs from v5.0 2.25's "each stage
writes immutable artifacts" for the asr / forced_alignment / diarization / language_gate stages
(per #6); (c) `submit(transport_inputs=...)` and `GPUOutput.kind` / `.provenance` extend the
ratified provider interface; (d) the cpu worker consuming `maintenance`; (e) lease/heartbeat figures
above; (f) `rotation_applied_to_pixels` in the manifest is `source_rotation_deg != 0`.

---

## 2026-10-04 decision log -- remaining Phase 3 issues

**Phase 3 status (exact words from the owner):** contract implementation **COMPLETE**; real-model
execution **BLOCKED_BY_SPEC** (G3); fastText execution **BLOCKED_BY_DEPENDENCY** (model file not
provisioned). The fake-backed suite proves interface/contract correctness only -- **the Phase 3 exit
gate is NOT passed.** The gate is `make smoke-real` (`tests/real_models/`): WhisperX ASR, forced
alignment, pyannote diarization and fastText language ID through the production interfaces. Today
its 5 tests are skipped with explicit BLOCKED reasons; with `REQUIRE_REAL_MODELS=1` they FAIL
(verified), so the gate cannot be passed by accident.

**Implemented:** (1) **fastText Option A** -- `fasttext_predict_v1` in `workers/cpu/language_gate.py`:
SHA-256 verified *before* load, one pybind `model.f.predict(text, 1, 0.0, "strict")` call (the very
call the broken wrapper makes first; confirmed in the installed 0.9.3 source), no `model.predict()`,
top-1 only, no training/batch API; a mandatory contract check runs at load time (shape, finite
confidence, checksum verified, adapter used) and fails closed. numpy 2 stays locked (a test asserts
no numpy pin). **Not verified against the real pybind model** -- training/loading a model crashes
in this sandbox and `lid.176.ftz` isn't provisioned, so the first real run is the smoke test.
(2) **Operational values** `dispatch_lease_s=60`, `reconcile_interval_s=15` are `Settings`
(env `SHORTS_MAKER_*`), not `config@1`; the effective values are persisted on every dispatch intent
(`lease_s`, `reconcile_interval_s`) and returned by the reconciler; `worker-cpu` consumes
`cpu,maintenance` with embedded Beat (`workers/cpu/worker.py::WORKER_COMMAND`), no new service.
(3) **v5.0 2.25 amended** in `docs/spec/virality_shorts_plan_v5_0.md` (stage = orchestrated product
stage; asr / language_gate / forced_alignment / sentence_segmentation / diarization are sub-steps of
`ANALYZING`). `transcript_v1` is now `Artifact.stage = "ANALYZING"`; every sub-step run keeps its own
status / version / provenance / retry record and stores `canonical_artifact_id` +
`parent_stage` in `execution_metadata`. The version number was NOT bumped. (4)/(5) GPU interface
additions confirmed; the control plane now **validates** every provider output (descriptor kind /
stage / location prefix for this source video, content hash, JSON Schema, stage, status, config
identity) and the GPU worker enforces exactly-one-`analysis_audio` input and this video's
`transport/.../asr/` prefix for transport inputs; it still only reads the DB. (6) The envelope
schema moved to `packages/schemas/json/internal/` (no generated Python/TS types) and the envelope
never gets an Artifact row. (7) **Transport retention**: `transport_objects` registry +
`workers/shared/transport_retention.py` + beat task `workers.maintenance.sweep_transport_objects`
(successful: 24 h after `transcript_v1` materialization; failed / cancelled: 7 d; running or
dispatched: never). Sweep re-checks no RUNNING stage run / DISPATCHED|RUNNING intent, canonical
artifact materialized and readable, deadline passed; idempotent; refuses non-`transport/` keys;
records `retain_until`, `retention_policy` (effective values + basis), `cleanup_attempts`,
`last_cleanup_attempt_at`, `cleanup_result`, `cleanup_failure_reason`, `deleted_at`; a failure never
touches canonical artifacts. Phase 3 re-entry returns the existing `transcript_v1` first, so a rerun
after envelope deletion is a no-op. Migration `d5a7e2b8c914`. (8)/(9) `media_manifest_v1` and the
exact PTS-based CFR predicate were already in; unchanged.

**Small flags:** the transport sweep cadence (`transport_sweep_interval_s = 3600`) was not specified,
so I chose hourly (operational Setting); `alembic check` still reports one pre-existing drift
(`ix_artifacts_source_video_id`, from Phase 1/2, not touched here); the amendment's diagram puts the
sub-steps inside the "ANALYZING stage" while decision C2 keeps the *job state* `NORMALIZED` until they
finish -- I treated stage and job state as different things (see the owner message).

---

## 2026-10-06 decision log -- G3 runtime freeze applied

`asr_runtime@1`, `alignment_runtime@1`, `diarization_runtime@1` are FROZEN in `config@1` with the owner's
values (ASR on CPU int8 with `language: null`, vendored Silero v6, `facebook/wav2vec2-base-960h` +
`interpolate_method="ignore"`, official community-1 revision `3533c8cf...`). Software versions match
`uv.lock`. Real adapters, offline model verification, the provisioning script, the non-English
fixture and the 10-point `make smoke-real` are written; **none of it has run against real models**
(no GPU, models or network here), so the Phase 3 exit gate is still NOT passed. Details, the list of
what still has to be provisioned and the open owner items: `docs/g3_runtime_freeze_applied_2026-10-06.md`.
Tests: 376 passed, 12 skipped (11 real-model smoke tests + 1 older skip).

---

## Notes for whoever continues this build

- Everything under `docs/spec/` is a **read-only copy** of the two source-of-truth files.
  Re-copy and re-check against this repo if they've since been revised.
- `packages/config/config@1.json` is the **only** place constants may live. Never hardcode a
  literal in business logic; re-derive `config_sha256` via `shorts_config.load_config()` after
  any change.
- `docs/implementation_constraints.md` holds correctness rules decided but not yet enforceable
  by any test, plus the new `thin_vertical_slice_harness` section — check it before implementing
  Phase 2, 5, 9, 10, or 11.
- `prompts/*.txt`, `packages/schemas/python/*.py`, and `packages/schemas/typescript/src/*.ts`
  are all **generated**, never hand-edited. Regenerate after any spec/schema change; all three
  are drift-checked by tests.
- Test naming: `tests/unit/test_phase<N>_<area>.py` (DB-independent) and
  `tests/integration/test_<name>.py` (needs real Postgres/Redis — see `tests/integration/conftest.py`).
- Phase 1 code (`apps/api`, `workers/`) exists and is tested. Phase 2 (normalization) is now
  built and tested too — see the 2026-09-29 decision log above for exactly what's done vs.
  still `BLOCKED_BY_SPEC`. Phase 3 is built to the extent G3 allows (see the 2026-09-30 log: real model backends are
  BLOCKED_BY_SPEC). Phase 4 onward is genuinely not started;
  `workers/cpu/tasks.py`'s remaining task bodies (`reverify_user_edit`, `refresh_reframe_only`)
  still raise `NotImplementedError` on purpose so that fact can never be silently papered over.

---

## Phase 4 — log (2026-10-07) — STATUS: IN PROGRESS, PARTIALLY BLOCKED

**Not `IMPLEMENTATION_COMPLETE`, not `END_TO_END_VALIDATED`.** Owner decision 2026-10-07 §1/§11: Phase 4 is built against
synthetic fixtures and fakes; it may become IMPLEMENTATION_COMPLETE on fake Phase-3 input, and END_TO_END_VALIDATED only after the
real Phase-3 smoke test yields a real `transcript_v1` that Phase 4 consumes. Nothing in Phase 4 has been run on real Phase-3 output
or the real embedding model (no model files/network in the dev sandbox).

### Owner decisions applied (2026-10-07)
1. Start Phase 4 now on fakes/synthetic fixtures; gate stays open until a real `transcript_v1` exists.
2. `embedding_runtime@1` FROZEN in config@1: BAAI/bge-small-en-v1.5 @ 5c38ec7c…, model.safetensors sha256 3c9f3166…, sentence-transformers,
   **CPU fp32 only**, CLS pooling, 384-d, L2-normalized, max_seq_length 512 (one truncated embedding, never chunked), batch 1, 1+1 threads,
   deterministic algorithms, no prefix, no download, no GPU/ONNX/OpenVINO/fallback. Input = exactly `sentence.text`. Two identical runs must be
   bitwise identical or the runtime test fails (`assert_bitwise_deterministic`). **This amends impl plan §1.9** (which said worker-gpu/ROCm for dev embeddings).
3. Shot detection = ContentDetector(27.0, min_scene_len 15 frames, luma_only false) over EVERY decoded frame; `shot_map_v1` frame-accurate;
   `scene_analysis_fps=2` is only the general visual stream. (Amends the impl-plan reading that tied both to 2 fps.)
4. Motion: 2 fps canonical, internal 10 fps probe for the 0.3 s sustain rule, grayscale, max dim 512, Farneback (0.5,3,15,3,5,1.2,0),
   motion = mean(flow magnitude)/frame diagonal. 5. Face: MediaPipe Face Detection model_selection=1, min_conf 0.5, 5 fps.
6. Screen: 1 fps, max dim 1280, existing deterministic Canny/contour detector, box normalized to the original frame.
7. Audio: 16 kHz mono; 25 ms frame / 10 ms hop RMS; 1 s non-overlapping RMS for `local_nonspeech_rms_v1`; centered 60 s edge-truncated baseline;
   silence = contiguous nonspeech 10 ms frames; pause = inter-word gap whose whole interval is nonspeech; peaks on the 10 ms series; dB std for rms_std_db (no LUFS).
8. Six artifact schemas normative (`audio_features_v1`, `visual_features_v1`, `shot_map_v1`, `sentence_embeddings_v1`, `texttiling_depth_v1`, `frame_manifest_v1`).
9. One pgvector table `sentence_embeddings` (see OPEN #6 — NOT created yet). 10. IT-4-5 is a pure Phase-4→Phase-5 artifact-contract test.

### Built and tested (27 new tests; 360 unit/contract + 59 integration pass in the sandbox; Postgres 16 / Redis 7.0 unpinned)
- config@1: `embedding_runtime@1` (FROZEN), 16 Phase-4 constants; `face_runtime@1`, `frame_resize_runtime@1`, `rms_db_runtime@1` present as **BLOCKED_BY_SPEC** (raise `ConfigSpecGap`, never default).
- 6 JSON Schemas + generated Pydantic types.
- `shorts_config.local_nonspeech_rms_v1` (helper #4 of the deferred six).
- `workers/cpu/audio_features.py` (RMS streams, nonspeech mask, silence, pause, peaks, dB bins), `shot_map.py` (verified on the real fixtures),
  `embeddings.py` (protocol, real CPU adapter — NOT run, determinism gate, fail-closed vector validation), `texttiling_stage.py`, `frame_manifest.py`,
  `analysis_artifacts.py` (identity + schema validation), `model_materialization.verify_embedding` + `scripts/materialize_models.py embedding`.

### NOT built (blocked or awaiting owner) — see "Open owner questions"
visual_features extractor (face/motion/screen), frame_manifest wiring (needs resize contract), rms dB stage output (needs epsilon),
pgvector table/migration, Celery/stage wiring + Phase-3→4 trigger, IT-4-5, real-model smoke for embeddings.

### Open owner questions (raised 2026-10-07; none decided by the implementer)
1. **Face detection is impossible as frozen**: locked mediapipe 1.0.1 (and 0.10.30) has no `mediapipe.solutions` and ships no face model; 0.10.21 has
   `solutions` + `face_detection_full_range_sparse.tflite` but pins numpy 1.26.4, conflicting with the numpy 2.x lock (pyannote-audio>=4). Choose: isolated face-detection environment/process on 0.10.21; Tasks API with an externally pinned model file (only short-range BlazeFace is official, so this changes decision §5); or amend the numpy/pyannote stack.
2. Resize: interpolation algorithm and whether frames smaller than the max dimension are upscaled (motion 512 / screen 1280); rounding of the other dimension; stream size for face/scene_context.
3. `epsilon` in 20·log10(max(rms, epsilon)).
4. Motion probe: must the 10 fps probe series be persisted in `visual_features_v1` (Phase 9 needs it for hook.first_motion_ms from artifacts)? And which robust-z baseline is stored as `motion_z` (60 s rolling for peaks vs video-level for `vis.motion_mean_z`/hook)? Also: `motion_change` edge handling when a 5 s window is incomplete.
5. Common identity: `checksum`, `artifact_id`, `created_at` cannot live inside the artifact body (circular / breaks content addressing); implemented as for `transcript_v1` — body carries identity/provenance, the Artifact row carries artifact_id/checksum/created_at/storage_location. Confirm.
6. pgvector uniqueness `(source_video_id, sentence_id, model_revision)` conflicts with several jobs per source video (multi-platform = separate jobs; sentence ids restart per transcript): second job's insert would collide or silently reuse another transcript's embedding. Add `job_id` to the key (or `artifact_id`)? Also: no `pgvector` Python package is in the lock — implement a local SQLAlchemy `vector(384)` type + migration `CREATE EXTENSION vector`?
7. `scene_context` (2 fps) has no defined consumer — kept only as a manifest stream.
8. Phase-3→4 trigger design (who dispatches Phase 4 after the job is ANALYZING).

### Implementer's readings awaiting confirmation (neither document states them)
R1 RMS frames not padded; trailing partial second gives no 1 s frame. R2 10 ms frame i = [10i,10i+10) ms, nonspeech test time = midpoint; silence interval ends at last frame start+10. R3 pause "entire interval" = every 10 ms frame whose midpoint lies in the gap; ALL gaps between two aligned words are stored (consumers filter ≥500/600 ms); gaps across an unaligned word are not emitted. R4 local maximum = x[i]>x[i-1] and x[i]>=x[i+1], interior only; spacing is chronological-greedy from the last ACCEPTED peak. R5 rolling median/MAD centered, edge-truncated, raw MAD into `robust_z_v1`. R6 population std (ddof 0). R7 a 1 s frame belongs to the window iff its center is in [t−30, t+30]; 20th percentile = numpy linear. R8 `rms_mean_db` stored alongside std (Structural Profile needs it). R9 no audio stream ⇒ audio_features `missing_reason = not_applicable`. R10 shot timestamps = round-half-up(frame·1000/fps) with exact `start_frame`/`end_frame` (end exclusive). R11 sample index rule `floor(k·source_fps/sampling_fps)` for frame_manifest. R12 token counts include [CLS]/[SEP]; text used byte-for-byte (no Unicode normalization). R13 TextTiling nulls use missing reason `no_evidence`. R14 embeddings are computed for every sentence, including unusable-timing ones. R15 `rms_samples` stored as float64 dense array.
