# Short-Form Virality Shorts Tool — Executable Implementation Plan

**Document:** Development + Production Implementation Plan v1.2  
**Product specification:** `virality_shorts_plan_v5_0.md`  
**Supersedes:** `virality_shorts_implementation_plan_v1_1.md`  
**Date:** 2026-09-21  
**Status:** **AGREED / EXECUTABLE**

---

## 0. Purpose and implementation rule

This file is the implementation specification for the system described by `virality_shorts_plan_v5_0.md`.

The **only two project specification/source-of-truth files are**:

1. `virality_shorts_plan_v5_0.md` — normative product behavior, algorithms, constants, schemas, evaluation rules, gates and owner decisions.
2. `virality_shorts_implementation_plan_v1_2.md` — normative technology choices, repository structure, implementation order, persistence/API mappings, tests, deployment and operational execution.

Legacy plans, audit notes, earlier implementation plans and generated prompt/schema files are not authoritative. They may exist in the repository for history, but the implementation AI must not use them to infer behavior. When this file says “the product plan”, it means `virality_shorts_plan_v5_0.md`.

The product plan remains the source of truth for **what the product must do**. This file is the source of truth for **how the agreed MVP is implemented**. Where an implementation detail is not explicitly fixed here, use the exact normative contract in the product plan; do not invent an alternative.

There are **no open technology, architecture, behavior or lifecycle decisions in this file**. An implementation AI must not invent alternative models, frameworks, storage systems, queues, hosting providers, APIs, artifact fields, constants, thresholds, prompts, retry semantics, or ranking behavior.

If a dependency becomes unavailable, deprecated, or incompatible during implementation:

1. do not silently substitute another technology;
2. mark the build as `BLOCKED_BY_DEPENDENCY`;
3. report the exact dependency and failing contract;
4. continue only with work that does not depend on the blocked component.

A package patch version may be updated only when required for security or compatibility. The replacement patch version must be the latest compatible patch in the same major/minor line and must be committed to the lockfile. A major/minor technology change is not allowed without an explicit update to this implementation plan.

All behavior-producing artifacts must include the configuration identity required by v5.0:

```text
config_version
config_sha256
stage_version
schema_version
```

All model-producing artifacts must additionally include:

```text
model_id
model_revision
prompt_version        # for LLM components
model_input_sha256
```

**Normative precedence rule:** if any implementation text in this file appears to disagree with `virality_shorts_plan_v5_0.md`, the implementation is blocked until the conflict is resolved in favor of the v5.0 normative behavior. Do not “pick whichever seems more reasonable”.



# 1. Fixed technology decisions

## 1.1 Repository and language layout

Use one GitHub monorepo named:

```text
shorts-maker
```

Repository branches:

```text
main
feature/<short-description>
```

Do not use long-lived development branches.

Monorepo layout:

```text
shorts-maker/
├─ apps/
│  ├─ web/                         # Next.js frontend
│  └─ api/                         # FastAPI HTTP API
├─ workers/
│  ├─ cpu/                         # Celery CPU worker tasks
│  ├─ gpu/                         # Local ROCm GPU worker + production Modal adapter
│  └─ render/                      # Celery rendering tasks
├─ packages/
│  ├─ schemas/                     # JSON Schema + generated TS/Python types
│  ├─ config/                      # Versioned configuration contracts
│  └─ fixtures/                    # Small deterministic test media and artifacts
├─ prompts/
│  ├─ style_prompt@1.txt
│  ├─ verifier_prompt@2.txt
│  └─ hook_analysis_prompt@1.txt
├─ infra/
│  ├─ terraform/
│  └─ docker/
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  ├─ contract/
│  └─ e2e/
├─ scripts/
├─ docs/
├─ Makefile
├─ pyproject.toml
├─ package.json
├─ pnpm-lock.yaml
└─ README.md
```

## 1.2 Frontend

Use:

- Next.js 16.3
- React 19.2
- TypeScript with strict mode
- pnpm
- Tailwind CSS 4
- Zod for client-side validation
- TanStack Query for server-state fetching/caching
- HTML5 video for preview
- Canvas only where needed for crop/reframe preview

Development hosting:

```text
Vercel Hobby / preview deployments
```

Commercial production hosting:

```text
Vercel Pro
```

The Hobby plan is development-only. It is not the production plan because Vercel's current Hobby terms restrict it to personal/non-commercial use.

Use the Next.js App Router.

Do not put video-processing logic in the frontend.

Do not call the LLM, GPU worker, database, Redis, or R2 with credentials directly from browser code. Browser media transfer is permitted only through presigned R2 URLs issued by the API.

## 1.3 Backend API

Use:

- Python 3.12
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x async API
- asyncpg
- Alembic
- `httpx` for outbound HTTP
- `redis-py` asyncio client
- Argon2id password hashing

Development execution:

```text
Local machine
Docker Compose for PostgreSQL + Redis
FastAPI runs locally
```

Hosted staging and production execution:

```text
Railway
```

Railway is the only hosted application/backend platform in this plan.

The API is stateless. Persistent state lives in PostgreSQL, Redis, and R2.

## 1.4 Queue and background processing

Use:

- Celery 5.6
- Redis OSS 7.1 as broker/result backend

Development Redis:

```text
Local Docker Redis
```

Hosted staging/production Redis:

```text
Railway Redis service
```

Celery queues are fixed:

```text
io
cpu
llm
gpu_dispatch
render
maintenance
```

No stage executes synchronously inside an HTTP request except request validation, authorization and creation of the job record.

Queue ownership is fixed:

```text
io            -> upload verification, artifact I/O, metadata fetch
cpu           -> normalization, analysis, discovery, qualification, Tier 1, edit planning, verification orchestration, ranking
llm           -> Kimi K3 / DeepSeek V4 Pro runtime calls
gpu_dispatch  -> invoke/wait for the configured GPU execution provider
render        -> FFmpeg render jobs
maintenance   -> cleanup, metric collection, scheduled evaluations
```

Development placement:

```text
FastAPI/API             -> local machine
worker-cpu + beat      -> local machine
worker-gpu              -> local RX 7800 XT machine
worker-render           -> local machine
Redis                   -> local Docker
```

Hosted staging/beta placement:

```text
FastAPI/API             -> Railway
PostgreSQL              -> Railway
Redis                   -> Railway
worker-cpu + beat      -> local machine
worker-gpu              -> local RX 7800 XT machine
worker-render           -> local machine
```

Production placement:

```text
FastAPI/API             -> Railway
worker-cpu + beat      -> Railway
worker-render           -> Railway
worker-gpu              -> Modal L4 through gpu_dispatch
Redis                   -> Railway
PostgreSQL              -> Railway
```

The application code uses the same queue names in every environment. Only the worker execution location changes.

## 1.5 Primary database

Use:

```text
PostgreSQL 18.6
pgvector 0.8.2
```

Development database:

```text
Local Docker PostgreSQL
```

Hosted staging/production database:

```text
Railway PostgreSQL
```

Use PostgreSQL for:

- users
- source videos
- processing jobs
- stage runs
- artifact metadata
- source regions
- edit plans
- verified edit plans
- hook/style outputs
- reframe plans
- short candidates
- scores/ranks
- review actions
- publication/outcome metadata
- experiment assignments
- audit events

Use pgvector only for sentence/topic embeddings and later trend metadata retrieval. Do not introduce another vector database.

## 1.6 Object storage

Use:

```text
Cloudflare R2
```

R2 is hosted from the first cloud-integration phase because it is the canonical object store and the browser upload architecture depends on presigned object URLs.

Local development also supports a filesystem adapter for unit tests and fully local pipeline tests. The filesystem adapter is never the authoritative production storage implementation.

Python services access R2 through `boto3` configured with:

```text
region = auto
S3-compatible R2 endpoint
```

Node/frontend code never receives R2 credentials.

R2 is the canonical media and immutable-artifact store in staging and production.

Required buckets:

```text
shorts-source-staging
shorts-source-production
shorts-artifacts-staging
shorts-artifacts-production
shorts-renders-staging
shorts-renders-production
```

All browser uploads use R2 presigned URLs issued by the API.

The API never proxies the full source-video upload body.

## 1.6.1 Fixed service boundaries

Run exactly these logical services:

```text
web
api
worker-cpu
worker-gpu
worker-render
worker-beat
```

`web` talks only to `api`, except for direct R2 transfers using presigned URLs.

`api` owns authentication, authorization, job creation, artifact metadata and signed URL generation.

`worker-cpu` owns deterministic media analysis, discovery, qualification, Tier 1, edit planning, verification orchestration, hook/reframe CPU work, Tier-2 CPU work and dataset preparation.

`worker-gpu` owns only GPU-backed ML inference tasks explicitly assigned to it.

`worker-render` owns FFmpeg rendering and render verification.

`worker-beat` is a logical queue scheduler, not a separately deployed Railway service. In D0/D1/D2 it runs embedded with `worker-cpu` using Celery Beat. In P0 it also runs embedded with the production `worker-cpu` deployment. It never performs video processing itself.

No separate microservice may be introduced for the MVP.

## 1.6.2 Local development environment

Use Docker Compose for local infrastructure:

```text
postgres
redis
api
worker-cpu
worker-gpu
worker-render
worker-beat
web
```

The local GPU worker runs on the user's:

```text
AMD Radeon RX 7800 XT
16 GB VRAM
RDNA3 / gfx1101
```

The supported local ML environment is fixed to:

```text
Ubuntu 24.04 LTS
ROCm 7.2.2
PyTorch ROCm build compatible with ROCm 7.2.2
```

The RX 7800 XT is an officially supported Radeon GPU in the current ROCm documentation. The exact PyTorch wheel and package lock must be frozen in Phase 0 after the GPU smoke test succeeds.

Important AMD constraint:

```text
Do not assume CUDA-only acceleration works on the RX 7800 XT.
```

For local development, PyTorch/ROCm workloads must use the RX 7800 XT only where the selected package is verified to run correctly under ROCm. WhisperX transcription is allowed to run on CPU locally if its selected transcription backend cannot use ROCm reliably. This is not a product behavior change: the transcript artifact schema remains identical.

## 1.6.3 Hosted staging environment

The first hosted environment is intentionally hybrid and keeps all compute-heavy workers local:

```text
Vercel                     -> web
Railway                    -> api + PostgreSQL + Redis
Cloudflare R2              -> staging objects/artifacts/renders
Local worker-cpu + beat    -> CPU processing + scheduling
Local RX 7800 XT           -> GPU worker
Local worker-render        -> FFmpeg rendering
Kimi K3 / DeepSeek V4 Pro  -> external LLM API calls when LIVE_STAGING is enabled
```

The local GPU worker connects to the hosted staging control plane only through outbound authenticated connections. No inbound port is opened to the user's home network.

The GPU worker consumes GPU tasks from the staging queue and writes artifacts to the staging R2 buckets.

## 1.6.4 Controlled beta environment

Use the same hybrid environment as hosted staging:

```text
Vercel Hobby/preview        -> frontend
Railway Trial               -> API + PostgreSQL + Redis while credits remain
Cloudflare R2               -> staging media
Local worker-cpu + beat     -> CPU processing + scheduling
Local RX 7800 XT            -> GPU worker
Local worker-render         -> FFmpeg rendering
Real Kimi/DeepSeek API      -> limited runtime calls
```

Beta access is allowlisted and limited to a small test group.

When the Railway trial expires before the production gate passes, do not upgrade merely to continue development. Switch the backend/database/Redis back to local Docker and continue the beta as a local/closed demonstration. The production upgrade happens only at the production promotion gate defined later in this file.

## 1.6.5 Production environment

Production is the first environment where recurring hosting and cloud-GPU spending is permitted.

```text
Vercel Pro                  -> web
Railway Hobby               -> api + PostgreSQL + Redis + worker-cpu + worker-render + worker-beat
Cloudflare R2               -> production media/artifacts/renders
Modal L4                    -> worker-gpu execution
Kimi K3                     -> style/hook runtime LLM
DeepSeek V4 Pro             -> semantic verifier runtime LLM
```

Railway Hobby is the fixed initial production plan. Upgrade to Railway Pro only when the explicit scaling gate in Phase 18 requires it.

Modal L4 is the fixed cloud GPU provider for production. It is never called from the development path unless a dedicated production-like cloud-GPU smoke test is explicitly executed.

## 1.7 CPU media processing

Use:

```text
FFmpeg 9.x
PySceneDetect 0.7.x
OpenCV
MediaPipe
librosa
NumPy
SciPy
```

FFmpeg is the canonical tool for:

- probing
- normalization
- audio extraction
- frame extraction
- clipping
- concatenation
- audio joins
- subtitle burning
- final muxing
- loudness normalization

PySceneDetect `ContentDetector` is the canonical initial shot-boundary detector.

## 1.8 Speech recognition and diarization

### ASR

Use:

```text
WhisperX
openai/whisper-large-v3-turbo
```

WhisperX is responsible for:

- ASR
- word timestamps
- sentence alignment
- text/word timing artifacts

Development execution:

```text
worker-gpu on RX 7800 XT when the pinned WhisperX stack is ROCm-compatible
otherwise worker-cpu
```

The development implementation must detect compatibility at startup and expose a health result. It must not silently install CUDA libraries or use an unsupported backend.

Production execution:

```text
Modal L4
```

The exact model snapshot is frozen in the model manifest. Runtime workers must never download an unpinned alias.

### Diarization

Use:

```text
pyannote/speaker-diarization-community-1
```

The model access token is stored in Railway/Modal secret storage and never in source control.

Diarization is required for multi-speaker inputs and is executed for all speech-bearing source videos because speaker turns are a boundary feature.

## 1.9 Embeddings

Use:

```text
BAAI/bge-small-en-v1.5
```

Use SentenceTransformers for inference.

Development execution:

```text
worker-gpu on RX 7800 XT using ROCm-compatible PyTorch
```

If the exact SentenceTransformers/PyTorch combination is CPU-only on the pinned environment, CPU execution is used. No alternative embedding model is permitted.

Production execution:

```text
worker-cpu or Modal L4 depending on the fixed deployment profile in Phase 18
```

The output dimensionality and normalization are fixed and stored in the artifact schema.

## 1.10 Structural computer vision

Use:

```text
OpenCV optical flow (Farneback)
MediaPipe face detection
```

Fixed sampling rates:

```text
face_sample_fps     = 5
motion_sample_fps   = 2
scene_analysis_fps  = 2
screen_analysis_fps = 1
```

No video-language model is used for MVP discovery, qualification, Tier 1 or Tier 2.

## 1.11 LLMs and development coding agents

There are two distinct uses of LLMs in this project.

### A. Implementation/coding agents

The user has access to:

```text
Kimi K3
DeepSeek V4 Pro
```

These models are approved implementation agents. They may inspect code, implement the current phase, write tests, diagnose failures and update documentation.

They are not trusted as the authority for product behavior. The v5.0 specification and this implementation plan remain authoritative.

### B. Product runtime LLMs

Use exactly:

| Product component | Model | Role |
|---|---|---|
| `content_style_v1` | `kimi-k3` | content style classification |
| `hook_analysis_v1` | `kimi-k3` | final short hook analysis |
| semantic verifier | `deepseek-v4-pro` | semantic verification |

Do not add a third runtime LLM in the MVP.

Do not automatically switch providers after an error. Provider errors are explicit stage failures and follow the standard retry policy.

### Runtime LLM interface

Implement one provider-neutral interface:

```python
class LLMProvider(Protocol):
    async def generate_structured(
        self,
        *,
        model_id: str,
        prompt_version: str,
        input_data: dict,
        output_schema: dict,
        request_id: str,
    ) -> LLMResult:
        ...
```

Implement exactly two providers:

```text
KimiProvider
DeepSeekProvider
```

Both providers are accessed through their documented OpenAI-compatible APIs.

Fixed model IDs:

```text
kimi-k3
deepseek-v4-pro
```

Development runtime modes:

```text
MOCK_LLM
LIVE_STAGING
LIVE_PRODUCTION
```

`MOCK_LLM` is the default for unit/integration tests because it creates no external API cost and produces deterministic fixtures.

`LIVE_STAGING` is used only for explicit LLM contract tests, prompt evaluation and controlled beta jobs.

`LIVE_PRODUCTION` is enabled only in Phase 18.

Never put API keys in repository files, frontend code or Docker images.

### Structured output

The provider adapter must convert the provider response into the canonical internal schema and validate it before business logic sees it.

The provider adapter may translate between provider-specific JSON/structured-output syntax, but it must never alter field meaning.

## 1.12 Production GPU hosting

Development and beta use:

```text
AMD Radeon RX 7800 XT locally
```

Production uses:

```text
Modal L4 24 GB
```

The two providers implement the same interface:

```python
class GPUExecutionProvider(Protocol):
    async def submit(...): ...
    async def get_status(...): ...
    async def cancel(...): ...
```

Implement exactly:

```text
LocalROCmGPUProvider
ModalGPUProvider
```

`LocalROCmGPUProvider` is enabled for development/staging/beta.

`ModalGPUProvider` is enabled for production.

No application component may contain an `if production then ...` branch inside model business logic. Provider selection happens only in the infrastructure/configuration layer.

## 1.13 Infrastructure as code

Use:

```text
Terraform
```

Terraform manages only infrastructure that is actually applicable to the selected hosted platform.

Required staging/production infrastructure definitions:

```text
Railway project/service definitions
R2 bucket configuration
secrets configuration
DNS configuration where required
monitoring configuration
```

Do not introduce an additional cloud platform beyond the fixed Railway + Vercel + Cloudflare R2 + Modal production stack defined in this file.

Modal app configuration is stored with the repository's deployment configuration and deployed separately from Railway services.

## 1.14 CI/CD

Use GitHub Actions.

Required workflows:

```text
ci.yml
security.yml
frontend.yml
backend.yml
staging-deploy.yml
modal-deploy.yml
production-deploy.yml
```

`main` requires all unit, contract, integration and relevant fixture e2e tests to pass before deployment.

Production deployment requires the Phase 18 production gate to be manually satisfied.

## 1.15 Observability

Use:

- Sentry for application exceptions and distributed traces
- Railway logs/metrics for hosted services
- Modal logs/metrics for production GPU jobs
- local structured JSON logs for development

Required correlation identifiers:

```text
request_id
job_id
stage_run_id
artifact_id
source_video_id
provider_job_id
```

Every worker log must include:

```text
service
environment
job_id
stage_name
stage_run_id
attempt
```


---

# 1.16 Deployment modes and promotion lifecycle

The implementation has exactly four deployment modes. They are not alternative architectures; they are sequential states of the same architecture.

## Mode D0 — Local Core

Purpose: implement and test the product without recurring hosting costs.

```text
Next.js                 -> local
FastAPI                 -> local
PostgreSQL + pgvector   -> local Docker
Redis                   -> local Docker
Celery CPU worker       -> local
RX 7800 XT GPU worker   -> local
FFmpeg renderer         -> local
Filesystem              -> local test adapter
R2                      -> not required for ordinary local tests
LLM                     -> MOCK_LLM by default
```

Use D0 for Phases 0–4 and for any work that does not require a real hosted upload/auth/network boundary.

## Mode D1 — Hybrid Staging

Purpose: test the real hosted boundaries while keeping GPU compute free.

```text
Vercel                  -> hosted frontend
Railway Trial           -> hosted API/PostgreSQL/Redis/CPU/render/beat workers
Cloudflare R2           -> hosted staging storage
RX 7800 XT              -> local GPU worker
Kimi/DeepSeek API       -> LIVE_STAGING only for LLM contract/evaluation jobs
```

Enter D1 only after `IT-4-5` passes.

The local GPU worker connects outbound to the hosted queue/control plane. Never expose the home GPU directly to the internet.

## Mode D2 — Controlled Beta

Purpose: let a small allowlist of real users exercise the system safely before recurring production infrastructure is purchased.

Use the same topology as D1 with these limits:

```text
max beta users                 = 10
max active jobs per user       = 2
max total concurrent jobs      = 2
max source duration             = 20 min
max source size                 = 2 GB
production publication          = disabled by default
external LLM calls              = rate-limited and logged
```

Beta data uses staging buckets and staging database only.

Do not allow beta users to access production secrets or production objects.

If Railway trial credits expire during D2, move the backend, DB and Redis back to D0. Do not start recurring Railway billing before the production gate.

## Mode P0 — Paid Production

Purpose: public/real-user operation with a supported hosted control plane and cloud GPU execution.

```text
Vercel Pro               -> frontend
Railway Hobby            -> API + PostgreSQL + Redis + CPU/render/beat workers
Cloudflare R2            -> production objects
Modal L4                 -> production GPU
Kimi K3                  -> style/hook runtime
DeepSeek V4 Pro          -> verifier runtime
```

P0 is entered only after every Phase 18 gate passes.

## Promotion rules

```text
D0 -> D1 : after Phase 4 exit gate + IT-4-5 + local GPU smoke test pass
D1 -> D2 : after Phases 0-13 exit gates pass in D1 + security suite + hosted parity pass
D2 -> P0 : after Phases 14-17 exit gates + Phase 18 hardening + cost model + user safety review pass
```

No skipping from D0 directly to P0.

No production credentials are used in D0, D1 or D2.

No production data is used in fixture/unit tests.

## What changes at each promotion

Only deployment configuration changes. The following application contracts do not change:

```text
API schemas
artifact schemas
Celery queue names
job state machine
stage names
model IDs
prompt versions
render profile
verification logic
ranking logic
lineage rules
```

The implementation must prove this with contract tests before each promotion.

# 2. Fixed system constants and limits

This section is the implementation-side registry of all named values that the product plan marks as initial/configurable. The implementation must load them from one immutable `config@1` snapshot and must never scatter literal copies through business logic. If the product plan defines a value as calibrated, the initial value below is the starting value until its gate permits a versioned replacement.

## 2.1 Core registry

```text
# Source / language / discovery
MAX_SOURCE_DURATION_S           = 5400
MAX_SOURCE_SIZE_BYTES           = 4_000_000_000
LANGUAGE_SAMPLE_S               = 60
LANGUAGE_ID_MODEL_ID             = fasttext/lid.176.ftz
LANGUAGE_MIN_WORDS              = 20
LANGUAGE_CONF_MIN               = 0.90
PROFILE_BIN_S                   = 10
CP_WINDOW_BINS                  = 6
CP_SIGMA                        = 1.5
CP_MIN_DIST                     = 1.0
CP_MIN_SEGMENT_S                = 60
CP_MIN_VIDEO_S                  = 180
NORM_WPM                        = 140
NORM_CUT_RATE                   = 12
NORM_MOTION                     = 0.15
NORM_PEAK_RATE                  = 3
S_sem / S_vis / S_evt           = 0.30 / 0.35 / 0.35
WEIGHT_FLOOR                    = 0.1
DEPTH_ABS_MIN semantic/topic    = 0.08 / 0.06
START_MIN / END_MIN             = 0.35 / 0.35
SEEDS_PER_10MIN                 = 10
LOOKBACK_S                      = 20
PREFERRED_EVENT_LEADIN_S        = 6
EVENT_MAX_LEADIN_S              = 15
LEADOUT_MIN_S                   = 4
MAX_EVENT_S                     = 45
TOPIC_STOP                      = 0.6
CONT_MIN                        = calibrated by the v5.0 25th-percentile rule

# Event-safe boundaries
EVENT_SAFE_PAUSE_MIN_S          = 0.5
EVENT_SAFE_SILENCE_MIN_S        = 1.5
EVENT_ONSET_MARGIN_S            = 1.0
EVENT_MIN_FINAL_S               = 6
EVENT_EDIT_MAX_RATIO            = 1.5
SETTLE_TAIL_MIN_S               = 1.5
SETTLE_SNAP_MAX_S               = 3.0

# Region / compression
MIN_REGION_SPEECH               = 10
MIN_REGION_EVENT                = 6
MAX_COMPRESSION_RATIO           = 4.0
STUDY_MAX_RATIO                 = 8.0
MAX_REGION_S                    = 240
SINGLE_IDEA_EXTENSION           = 1.25
ABSOLUTE_REGION_CEILING         = 360
MAX_SINGLE_IDEA_REGION_S        = 300
R_DISC                          = 1.0 per minute
R_T1                            = 0.4 per minute
R_EDIT                          = 0.25 per minute
N_SHOW                          = 10
MAX_PLANS_PER_REGION            = 3 production plans

# Edit planning / cleanup
MAX_INTERVALS                   = 6
MIN_KEEP_INTERVAL_S             = 3 speech / 2 event
DP_POOL                         = 20
DP_BUCKET_S                     = 0.1
LONG_UNIT_S                     = 15
SPLIT_PAUSE_MS                  = 500
LAMBDA_CUT                      = 0.15
DENSITY_NORM                    = 2.5
PAYOFF_DECAY_UNITS              = 8
OPENING_CANDIDATES              = 3
CTX_MAX                         = 0.5
OPENING_OBJ_TOL                 = 0.10
AGGR_FACTOR                     = 0.7
PLAN_DEDUP_DURATION_REL         = 0.10
MINIMAL_CLEANUP_RATIO_CAP       = 1.10
PAUSE_SHORTEN_THRESHOLD_S       = 0.7
PAUSE_TARGET_S                  = 0.35
MICRO_EDIT_MAX_DENSITY          = 1 per 2 s
FILLER_WORD_REMOVAL_CONFIDENCE  = 0.8 (LATER; unused in MVP)

# Verification / judge
PASS_MIN_SCORE                  = 4
PASS_MEAN_STANDARD              = 4.2
PASS_MEAN_STRICT                = 4.5
HARD_SCORE_MAX                  = 2
STANDARD_RATIO_MAX              = 2.0
STRICT_MINOR_ISSUES_MAX         = 1
VERIFY_ALL_PLANS                = true
EARLY_STOP_ACCEPTED_PLANS      = disabled
PLAN_VERIFY_ORDER               = minimal, balanced, aggressive; study adds ratio targets 4.5/5/6/7/8
JUDGE_MIN_WORDS                 = 25
CONTEXT_BEFORE_S                 = 30
JUDGE_MAX_EVIDENCE_WORDS        = 20
CUT_GAP_MIN_MS                  = 20
CROSSFADE_MS                    = 30
MIN_XFADE_MS                    = 10
LOUDNESS_STEP_MAX_DB            = 12
LOUDNESS_XFADE_MS               = 100
EXT_XFADE_MIN_MS                = 60
BRIDGE_MARGIN                   = 0.05
REPAIR_DUPLICATE_OVERLAP        = 0.9
REPAIR_RESTORE_DEPTH             = 1
MAX_REPAIR_ITERATIONS_PER_PLAN  = 1
MAX_JUDGE_CALLS_PER_PLAN        = 2
MAX_JUDGE_CALLS_PER_REGION      = 6
STUDY_MAX_JUDGE_CALLS_PER_REGION= 10
LLM_CALL_TIMEOUT_S              = 30
LLM_MAX_TRANSPORT_RETRIES       = 2
STAGE_MAX_ATTEMPTS              = 3

# Deterministic analysis
ROBUST_Z_ZERO_MAD               = 6.0
RMS_MAD_FLOOR                   = 0.01
MOTION_MAD_FLOOR                = 0.01
DEPTH_MAD_FLOOR                 = 0.01
REL_MAD_FLOOR                   = 0.05
LOCAL_NONSPEECH_WINDOW_S        = 60
LOCAL_NONSPEECH_PERCENTILE      = 20
SENTENCE_GAP_MS                 = 500
SENTENCE_MAX_S                  = 15
HARD_SPLIT_MIN_GAP_MS           = 20
TEXTTILING_SEMANTIC_W           = 5
TEXTTILING_TOPIC_W              = 25
EMBEDDING_MODEL_ID              = BAAI/bge-small-en-v1.5
SHOT_CONTENT_THRESHOLD           = 27.0
SHOT_MIN_SCENE_FRAMES            = 15

# Hook / style
OPENING_WINDOW_S                = 3.0
OPENING_MIN_WORDS               = 15
OPENING_MAX_WORDS               = 40
HOOK_LLM_MIN_WORDS              = 8
HOOK_MAX_TYPES                  = 2
HOOK_TYPE_CONF_MIN              = 0.6
MIN_TYPE_POSITIVES              = 5
STYLE_CONF_MIN                  = 0.6
STYLE_MAX_INPUT_TOKENS           = 4000
STYLE_HEAD_TOKENS               = 2000
STYLE_TAIL_TOKENS               = 1900
STYLE_TOKENIZER_VERSION         = 1
STYLE_CACHE_VERSION              = 1
HOOK_CANONICAL_INPUT_VERSION     = 1
TIMELINE_MAPPING_VERSION         = 1
HOOK_SEMANTIC_VALIDATOR_VERSION   = 1
AUDIO_SIGNAL_Z / MOTION_SIGNAL_Z = 2.0 / 2.0
FACE_SAMPLE_FPS                 = 5
BOOTSTRAP_B                     = 2000
VIS_FACE_MIXED_MIN              = 0.20
VIS_SCREEN_MIXED_MIN            = 0.20
VIS_SCREEN_MIN                   = 0.50
VIS_FACE_MIN                     = 0.20

# Tier 1
T1_MIN_SCORE                    = 0.25
T1_OVERLAP_IOU                  = 0.5
duration_fit levels               = 1.0 / 0.7 / 0.4 / 0
BACKFILL_BATCH                  = 3
BACKFILL_MAX_ROUNDS             = 2
T1_MIN_VIDEOS                   = 8
T1 weights                       = hook .15, boundary .20, completeness .15, standalone .15, density .10, energy .10, duration_fit .10, live_air .05

# Reframe / captions / render
REFRAME_GRID_PX                 = 16
REFRAME_MAX_CENTER_JUMP_PX      = 120
REFRAME_MEDIAN_WINDOW_FRAMES    = 5
REFRAME_CONF_MIN                = 0.6
CAPTION_MAX_CHARS_PER_LINE      = 32
CAPTION_SAFE_ZONE               = x 0.05–0.95, y 0.78–0.93
LOUDNESS_TARGET_LUFS            = -14
TRUE_PEAK_MAX_DBTP              = -1.0
CAPTION_FONT_FAMILY              = Noto Sans
CAPTION_FONT_SIZE_PX             = 64
CAPTION_TEXT_COLOR               = #FFFFFF
CAPTION_OUTLINE_COLOR            = #000000
CAPTION_OUTLINE_WIDTH_PX         = 4
CAPTION_ALIGNMENT                = center
BLACK_FRAME_SAMPLE_FPS           = 2
BLACK_FRAME_LUMA_THRESHOLD       = 16/255
BLACK_FRAME_MAX_FRACTION         = 0.02
BLUR_BACKGROUND_SIGMA            = 24

# Evaluation / Task 3 / Task 4
T4_BASE_PAIRS                   = 400 dev pairs
T4_SEALED_PAIRS                 = 160 sealed pairs
T4_DEV_MIN_VIDEOS               = 32
T4_SEALED_MIN_VIDEOS            = 12
T4_MAX_VIDEO_SHARE              = 0.10
T4_MIN_CROSS_REGION_SHARE       = 0.50
T4_CROSS_CLASS_PAIRS            = 40
T4_CROSS_CLASS_MIN_VIDEOS       = 8
T4_SAMPLING_SEED                = 20260920
STUDY_MIN_REGIONS               = 15
STUDY_MIN_VIDEOS                = 8
STUDY_MAX_VIDEO_SHARE           = 0.25
STUDY_TARGET_RATIOS             = {4.5, 5.0, 6.0, 7.0, 8.0}
STUDY_TARGET_TOL                = 0.05
STUDY_TARGET_SLACK_S            = 0.5
STUDY_MAX_PLANS_PER_REGION      = 5

# Tier 2
T2_MIN_COVERAGE                 = 0.5
WPM_TARGET / WPM_TOL            = 150 / 75
PAUSE_RATIO_REF                 = 0.25
REL_MIN_POP                     = 8
MMR_LAMBDA / DISPLAY_MAX_OVERLAP= 0.7 / 0.30
T2 weights                      = coherence .20, hook .20, completeness .10, density .10, pacing .10, energy .10, visual .05, edit .10, reframe .05
H5_MARGIN                       = 0.03
HOOK_GROUPS_ENABLED             = []
CROSS_CLASS_MERGE_ENABLED       = false
TREND_FEATURES_ENABLED          = false
```

**Profile rule:** each job uses exactly one immutable `export_profile_v1`; MVP ships the YouTube Shorts profile. The profile hash is persisted on the job and every plan-level artifact. Multi-platform output means separate jobs, not one job with multiple profiles. Discovery remains profile-agnostic with `MAX_REGION_S = 240`.

**Critical config rule:** every value above that is behavior-producing is present in the canonical config snapshot. Do not duplicate these constants in Python/TypeScript modules except as generated/read-only bindings.

## 2.2 Export profiles

Required initial profiles in the config registry:

| Profile | min_s | primary_range_s | extended_range_s | max_s |
|---|---:|---|---|---:|
| `youtube_shorts` | 8 | 20–60 | 60–120 | 180 |
| `tiktok_default` | 8 | 20–60 | 60–120 | verify before enabling |
| `instagram_reels_default` | 8 | 15–60 | 60–90 | verify before enabling |

Only the selected profile is active for a job. Do not use non-YouTube profiles in production until their `max_s` is verified against official current platform documentation and the config snapshot is version-bumped.

## 2.3 Deterministic analysis primitives

Implement exactly once under `packages/config` / `packages/schemas` and import from all downstream stages:

- `robust_z_v1(x, center, mad, floor)` with the finite zero-MAD fallback `ROBUST_Z_ZERO_MAD = 6.0`;
- `event_safe_cut_v1(t)`;
- `latest_safe_before(t)` and `earliest_safe_after(t, max_lookahead)`;
- `local_nonspeech_rms_v1(t)`;
- `d_clean_v1(region, export_profile_id)`;
- `super_unit_embedding_v1`;
- `sentence_seg_v1`;
- `TextTiling_depth_v1`.

No local implementation of these functions is permitted in discovery, ranking, editing, verification, hook, reframe or Tier 2 code.

## 2.4 LLM retry taxonomy

For every runtime LLM (`content_style_v1`, `hook_analysis_v1`, semantic verifier):

```text
transport_error = timeout, connection failure, HTTP 429, HTTP 5xx, provider unavailable
invalid_output  = response received but schema/semantic validation fails
```

`transport_error` retries with exponential backoff up to `LLM_MAX_TRANSPORT_RETRIES = 2` and does **not** consume a judge lineage budget. Exhausted transport retries yield a stage-level `RETRYABLE_TRANSPORT_ERROR`; never fabricate a semantic result.

`invalid_output` consumes the current lineage call and permits the single bounded output retry defined by the relevant product-plan contract. A second invalid response yields `invalid_output` / `J_INVALID_OUTPUT` as applicable.

All calls also observe `LLM_CALL_TIMEOUT_S = 30` and `STAGE_MAX_ATTEMPTS = 3`.



# 3. Non-negotiable architectural contracts

## 3.1 Artifact immutability

Artifacts are content-addressed and never overwritten.

Storage path:

```text
artifacts/{source_video_id}/{artifact_type}/{artifact_id}/{artifact_sha256}.json
```

Every stage writes a new artifact version rather than mutating prior JSON. Mutable database rows may point at the current artifact; historical artifact bytes remain immutable.

## 3.2 Stage idempotency

Every stage implements:

```python
run_stage(input_artifact_ids, config_identity) -> output_artifact_ids
```

Before computation:

1. canonicalize input artifact IDs;
2. compute `stage_input_sha256`;
3. query successful stage run with identical `(stage_version, stage_input_sha256, config_sha256)`;
4. reuse it when present;
5. otherwise execute and persist a new stage run.

## 3.3 Queue idempotency

Celery task IDs are deterministic from:

```text
job_id + stage_name + stage_input_sha256
```

At-least-once delivery is assumed; every worker is safe to execute twice.

## 3.4 Failure taxonomy

Generic stage failures are exactly:

```text
TRANSIENT
PERMANENT_INPUT
PERMANENT_MODEL
PERMANENT_VALIDATION
CANCELLED
TIMEOUT
BLOCKED_BY_DEPENDENCY
```

Runtime LLM calls use the explicit `transport_error` / `invalid_output` taxonomy in §2.4. A transport failure must never be converted into a semantic verdict or neutral score.

Generic retry policy:

```text
TRANSIENT/TIMEOUT: exponential backoff, max 3 stage attempts
PERMANENT_*: no retry
CANCELLED: no retry
BLOCKED_BY_DEPENDENCY: no automatic retry
```

## 3.5 Event-safe boundary authority

`event_safe_cut_v1` is the only authority for event-led start/end timestamps. It must be used by discovery, qualification, event edit planning and Layer 1. Event code must never manufacture a timestamp through raw arithmetic from onset/settle/max-duration values.

## 3.6 Verified edit authority

After verification, `verified_edit_plan` is the **only** content/timeline/audio-join authority. Later stages never read an older raw Edit Plan for retained content, ordering, output timing or authoritative joins.

`verified_edit_plan` must not store downstream `hook_analysis_id`, `reframe_plan_id` or `caption_plan_id`; those IDs are downstream Short Candidate/render dependencies.

## 3.7 Reframe authority

`reframe_plan_v1` is the only vertical-composition authority. It is computed from the verified retained timeline and `final_visual_format`, not the coarse Source Region visual format.

## 3.8 Caption authority

`caption_plan_v1` is the only caption timing/text segmentation authority. It is generated from verified output-timeline word timings using the v5.0 line-length and safe-zone rules. The renderer consumes it and must not reconstruct caption timing from source timestamps.

## 3.9 Render authority

A render request consumes exactly:

```text
verified_edit_plan
reframe_plan_v1
render_profile_v1
caption_plan_v1   # required when caption_mode != none; null otherwise
```

The three/four inputs are immutable and each ID + SHA-256 is persisted on the render request. No render-time override may alter retained source content, timing/order, joins, crop/reframe, export format, caption placement/timing or loudness policy.

## 3.10 Export-profile authority

Every job has exactly one immutable `export_profile_id` selected at job creation. The profile and its hash are copied into every plan-level artifact. Discovery is profile-agnostic; edit planning, verification, reframing and rendering consume the selected profile. A multi-platform request is implemented as multiple jobs.

## 3.11 Evaluation-data separation

Task 4 has three logically isolated pools:

1. `dev`: 400 same-class pairs used for tuning/adoption decisions and H-G5 dev evaluation;
2. `sealed`: 160 same-class pairs from sealed-test videos, opened once for final confirmation only;
3. `cross_class`: at least 40 pairs across at least 8 videos, never used for training or tuning.

No sealed result can trigger a weight, threshold or feature decision.



# 4. Repository implementation contracts

## 4.1 Python dependency groups

`pyproject.toml` must contain these groups:

```text
api
worker
media
ml
observability
test
```

The local/Docker render image must also install the OS package `fonts-noto-core`; the active caption font is `Noto Sans`. A render fails closed if the configured font family cannot be resolved.

Minimum required packages:

```text
fastapi
uvicorn
pydantic
pydantic-settings
sqlalchemy
asyncpg
alembic
celery
redis
httpx
boto3
cryptography
argon2-cffi
numpy
scipy
opencv-python
mediapipe
librosa
soundfile
pyscenedetect
sentence-transformers
torch
transformers
whisperx
faster-whisper
jsonschema
orjson
pytest
pytest-asyncio
hypothesis
```

The lockfile freezes all versions.

## 4.2 TypeScript dependency groups

Minimum required packages:

```text
next
react
react-dom
typescript
zod
@tanstack/react-query
tailwindcss
```

## 4.3 Schema strategy

Create JSON Schemas under:

```text
packages/schemas/json/
```

Generate:

```text
packages/schemas/typescript/
packages/schemas/python/
```

Do not maintain duplicated handwritten API types when they can be generated from the canonical schemas.

---

# 5. Phase implementation plan

## 5.0 Universal execution rules

These rules apply to every phase:

1. Unit tests run entirely in D0 and must not require live cloud services.
2. Unit tests must use `MOCK_LLM` and deterministic local fixtures.
3. Each phase's next-phase integration test runs first in D0.
4. After D1 promotion, the same integration contract is re-run against the hosted components available in D1.
5. R2 is used for D1/D2 hosted media; local filesystem storage is used for D0 tests.
6. D1/D2 compute-heavy CPU, GPU and render workers remain local. Only API/PostgreSQL/Redis are hosted on Railway during D1/D2.
7. Real Kimi/DeepSeek calls are never used in unit tests.
8. Live LLM calls are permitted only in explicit contract/evaluation tests and D2 beta jobs.
9. Production model/provider credentials are forbidden outside P0.
10. A passing local test is not a substitute for the D1 hosted parity test.
11. The implementation AI must use only `virality_shorts_plan_v5_0.md` plus this file as specification sources.
12. Generated prompts/schemas/config bindings are artifacts derived from those two files, never independent sources of truth.
13. Study-mode artifacts never enter production ranking; study judge calls have their separate budget.

For Phases 5–13, D0 remains the implementation environment. D1 is the hosted parity environment. A phase is not marked hosted-ready until its D1 parity test passes.

For Phases 14–17, D2 is mandatory because these phases depend on controlled real-user/outcome data.

Phase 18 is P0-only.

Each phase below has:

1. exact implementation tasks;
2. unit tests for that phase;
3. an integration test that proves compatibility with the **next** phase;
4. a sign-off gate.

A phase cannot be marked complete until its own unit tests **and** next-phase integration tests pass.

---

# Phase 0 — Repository, contracts, local reproducibility

**Execution mode:** D0 Local Core only.

## Objective

Create a reproducible project skeleton and make every v5.0 contract executable before media stages are built.

## Tasks

### 0.1 Create repository

Create the monorepo tree from §1.1 and add:

```text
.pre-commit-config.yaml
.editorconfig
.gitattributes
.gitignore
Makefile
README.md
```

### 0.2 Configure Python

Use Python 3.12 with Ruff, Pytest and MyPy. Lock all dependencies.

### 0.3 Configure frontend

Create Next.js 16.3 App Router with strict TypeScript.

### 0.4 Canonical schemas

Create machine-checkable JSON Schemas for at least:

```text
User
SourceVideo
UploadSession
ProcessingJob
StageRun
ArtifactRef
BoundaryMap
SourceRegion
QualificationRecord
EditUnit
EditPlan
VerifiedEditPlan
HookAnalysis
ContentStyle
ReframePlan
CaptionPlan
RenderProfile
ShortCandidate
Tier1Score
Tier2Score
DisplaySelection
ReviewAction
OutcomeRecord
EvaluationReport
CalibrationReport
AdoptionDecision
```

Every schema contains the exact product-plan fields where the v5.0 artifact schema is defined. Generate Python and TypeScript types from the JSON Schemas; do not maintain competing handwritten models.

### 0.5 Config registry

Implement one immutable `config@1` snapshot with canonical JSON ordering and UTF-8 serialization. Implement:

```python
canonical_json(obj) -> bytes
sha256_bytes(data) -> str
config_identity(config) -> (config_version, config_sha256)
```

All constants in §2 are loaded from this registry.

### 0.6 Shared helper package

Implement and unit-test the exact shared primitives in §2.3. The helper package is the only permitted implementation location for these functions.

### 0.7 Deterministic analysis contracts

Implement the exact v5.0 contracts for `sentence_seg_v1`, mandatory forced alignment, `TextTiling_depth_v1`, deterministic embedding provenance and no-diarization behavior as testable library contracts before wiring them into pipeline workers.

### 0.8 Prompt artifacts

Create these files directly from the exact normative blocks in `virality_shorts_plan_v5_0.md`, byte-for-byte except for a trailing newline:

```text
prompts/style_prompt@1.txt
prompts/verifier_prompt@2.txt
prompts/hook_analysis_prompt@1.txt
```

Do not paraphrase the prompts. The product plan remains the authority for prompt text; these files are generated implementation artifacts only.

### 0.9 Fixtures and snapshots

Create the committed synthetic fixtures already specified and expected probe/transcript/boundary snapshots. Add fixtures for:

```text
speech-led >= 25 words
speech-led < 25 words
6–8 s event-led candidate
multi-speaker reframe
screen-content reframe
no-diarization path
transport-error LLM path
invalid-output LLM path
study-ratio generation
user-edit rejection
```

### 0.10 Thin vertical slice

Before scaling the evaluation dataset, execute one complete deterministic path on `fixture_speech_45s.mp4`: normalize → ASR/language gate/alignment → analysis → discovery → one qualified region → one verified edit plan → reframe → captions → render. Persist all artifacts and hashes. This is a build-health slice, not a substitute for the full phase gates.

## Unit tests

```text
test_schema_required_fields
test_schema_unknown_field_policy
test_config_canonicalization_is_stable
test_config_sha256_is_stable
test_shared_helpers_are_singleton_imports
test_sentence_seg_v1
test_texttiling_depth_v1
test_embedding_provenance
test_no_diarization_missingness
test_prompt_files_match_v5_source
test_artifact_id_determinism
test_stage_input_hash_determinism
```

## Integration test for Phase 1

`IT-0-1`: start PostgreSQL/Redis, run migrations, create a user, create one job with one `export_profile_id`, and enqueue a placeholder `NORMALIZING` task. Assert all IDs/config hashes/schema versions validate.

## Exit gate

Schemas, config identity, helpers, prompts, migrations and fixture manifests are deterministic on a clean clone.



# Phase 1 — Infrastructure, authentication, upload and job control

**Execution mode:** D0 Local Core. D1 hosted parity follows the D1 promotion rule.

## Objective

Provide secure user/API/job infrastructure, one storage abstraction, immutable export-profile selection and the coarse job state machine.

## Tasks

### 1.1 Environment bootstrap

D0: Docker Compose PostgreSQL + Redis + API + workers. Prepare D1 Vercel/Railway/R2 configuration without moving compute-heavy workers to Railway.

### 1.2 Database migrations

Create at least:

```text
users
refresh_tokens
source_videos
upload_sessions
processing_jobs
stage_runs
artifacts
source_regions
qualification_records
edit_plans
verified_edit_plans
hook_analyses
content_styles
reframe_plans
caption_plans
short_candidates
tier1_scores
tier2_scores
display_selections
review_actions
outcomes
audit_events
```

`processing_jobs` must store:

```text
export_profile_id
export_profile_sha256
config_version
config_sha256
```

The selected profile is immutable for the job.

### 1.3 Authentication

Keep the authentication contract defined in §1.3 unchanged: local email/password, Argon2id, rotating refresh tokens, CSRF protection and strict cookie attributes.

### 1.4 API endpoints

Implement exactly these MVP HTTP endpoints:

```text
POST /v1/auth/register
POST /v1/auth/login
POST /v1/auth/refresh
POST /v1/auth/logout
GET  /v1/me

POST /v1/uploads
POST /v1/uploads/{upload_id}/complete

POST /v1/jobs
GET  /v1/jobs/{job_id}
POST /v1/jobs/{job_id}/cancel
GET  /v1/jobs/{job_id}/artifacts
GET  /v1/jobs/{job_id}/candidates

POST /v1/candidates/{candidate_id}/edit
POST /v1/candidates/{candidate_id}/reframe
POST /v1/candidates/{candidate_id}/accept
POST /v1/candidates/{candidate_id}/reject
POST /v1/jobs/{job_id}/rerank
```

Authentication, upload and job endpoints use the schemas in §6. Candidate mutation endpoints are authorized to the owning user only and are the only API entry points for candidate lifecycle actions.

`POST /v1/jobs` requires `export_profile_id`; the MVP enabled profile is `youtube_shorts`. Reject an unknown or disabled profile. The API must never allow a second profile to be attached to an existing job.

`POST /v1/candidates/{candidate_id}/edit` accepts only a deterministic edit instruction defined by the review UI: a new source-range trim or removal of one or more existing retained intervals, never arbitrary timestamp invention. The server snaps the requested boundaries using the same safety rules as Phase 8, creates `plan_origin=user_edit`, and sends the new lineage through verification. It never mutates the parent candidate.

`POST /v1/candidates/{candidate_id}/reframe` changes only composition parameters exposed by the UI and creates a reframe-only lineage; it does not create a new content Edit Plan and does not rerun content verification.

`POST /v1/candidates/{candidate_id}/accept` and `/reject` append immutable `review_actions` and drive the candidate state machine defined in Phase 12.

`POST /v1/jobs/{job_id}/rerank` is the only operation allowed to create a new immutable `display_selection_v1` revision. It does not modify the prior selection artifact.

### Candidate mutation request bodies

`POST /v1/candidates/{candidate_id}/edit` body:

```json
{
  "operations": [
    {"type": "trim_start", "requested_source_ms": 0},
    {"type": "trim_end", "requested_source_ms": 0},
    {"type": "remove_retained_interval", "output_segment_id": "uuid"}
  ]
}
```

At least one operation is required. Operations are applied in array order against a working copy of the parent's verified timeline. `trim_start` and `trim_end` snap to the nearest legal sentence boundary for speech-led content or `event_safe_cut_v1` boundary for event-led content. `remove_retained_interval` names an existing retained output segment; no raw timestamp is invented. If the working edit becomes empty or violates a hard plan constraint, the edit is rejected and the parent remains unchanged. A successful request creates one `plan_origin=user_edit` lineage.

`POST /v1/candidates/{candidate_id}/reframe` body:

```json
{
  "strategy": "auto | fixed_center | face_aware | multi_speaker | blurred_background"
}
```

`auto` uses the deterministic v5.0 strategy order. Any non-`auto` value requests only that composition strategy; if the strategy cannot produce a valid composition, no fallback strategy is substituted and the reframe edit is rejected. The edit does not change verified content/timing and creates a new reframe lineage.

`POST /v1/candidates/{candidate_id}/accept` and `/reject` accept:

```json
{ "reason": "optional-free-text-for-audit" }
```

The reason is review metadata only and is never a model/ranking feature.

### 1.5 Storage

D0 local filesystem adapter. D1/D2 R2. All browser uploads use API-issued presigned URLs.

### 1.6 Job orchestration

Use the coarse v5.0 job states exactly. Candidate lifecycle is independent and is implemented in Phase 12; do not overload the job state machine with per-candidate states.

## Unit tests

Include these tests in the Phase 1 authentication test suite:

```text
test_job_requires_valid_export_profile
test_export_profile_immutable
test_profile_hash_persisted_on_job
test_job_cannot_attach_second_profile
test_candidate_state_not_stored_as_job_state
```

## Integration test for Phase 2

`IT-1-2`: create the same fixture job in D0 and D1. Verify the job carries one profile ID/hash and all subsequent stage/artifact records inherit it.

## Exit gate

Secure job creation, profile selection, storage abstraction and state transitions are deterministic and tested.



# Phase 2 — Media normalization and probing

**Execution mode:** D0 Local Core. D1 storage/media parity is executed after the D1 promotion gate.

## Objective

Convert every accepted source to one deterministic media representation and generate the canonical media manifest.

## Canonical normalized format

```text
video codec: H.264
pixel format: yuv420p
frame rate: preserve source FPS only when the source is CFR and FPS is one of {24, 25, 30, 50, 60}; otherwise transcode to constant 30 FPS
audio: AAC, 48 kHz, stereo when source has multiple channels; mono for analysis copy
container: MP4
```

Also create analysis audio:

```text
WAV
mono
16 kHz
PCM s16le
```

## Tasks

### 2.1 Probe

Use `ffprobe -of json` and validate:

```text
duration
width
height
fps
video codec
audio codec
audio sample rate
channels
rotation metadata
```

### 2.2 Normalize

Run FFmpeg with exactly these normalization semantics:

```text
video: libx264, CRF 18, preset medium, single-threaded, yuv420p
frame rate: CFR at the selected normalized FPS from the canonical-format rule
audio: AAC, 192 kbps, 48 kHz; 2 channels when source has >=2 channels, otherwise 1
container: MP4
timestamps: make_zero
metadata: strip container metadata and chapters
```

Use `-threads 1` for FFmpeg encode and fixed filter ordering. Never embed wall-clock creation metadata. Preserve the original object unchanged.

Write:

```text
normalized.mp4
analysis_audio.wav
media_manifest.json
```

### 2.3 Normalize orientation

Apply rotation metadata to pixels so downstream geometry always sees upright frames.

### 2.4 Duration validation

Reject source if:

```text
duration <= 0
 duration > 5400
```

### 2.5 Checksums

SHA-256 every normalized object.

## Unit tests

```text
test_probe_fixture_speech
 test_probe_rotation_metadata
 test_reject_zero_duration
 test_reject_over_90_min
 test_normalized_manifest_schema
 test_audio_is_16khz_mono
 test_video_pixel_format_is_yuv420p
 test_normalization_idempotency
```

## Integration test for Phase 3

`IT-2-3`:

Run normalization on all three fixtures, then invoke the ASR/diarization dispatch contract using the generated manifest. In D0, resolve artifact objects through the local storage adapter. After D1 promotion, re-run the same test with R2 signed URLs. Assert that Phase 3 locates normalized media only through artifact IDs and provider-issued storage access, never through hard-coded local paths.

## Exit gate

All fixtures produce valid canonical normalized artifacts and a phase-3-compatible manifest.

---

# Phase 3 — ASR, forced word alignment, sentence timing and diarization

**Execution mode:** D0 Local Core. D1 hosted-control-plane parity follows promotion.

## Objective

Produce aligned transcript/timing/speaker artifacts that satisfy the exact v5.0 analysis primitives.

## Tasks

### 3.1 GPU execution

Use the fixed providers/models in §1.8/§1.12.

### 3.2 ASR

Run pinned `WhisperX` with `openai/whisper-large-v3-turbo`. Persist ASR words, confidence and detected language.

### 3.3 English language gate

Use the pinned `LANGUAGE_ID_MODEL_ID = fasttext/lid.176.ftz`. After ASR produces the sample, apply the v5.0 language gate using the first `LANGUAGE_SAMPLE_S = 60 s` or available duration, requiring at least `LANGUAGE_MIN_WORDS = 20` words and `LANGUAGE_CONF_MIN = 0.90`. Store the model file SHA-256 in the model manifest.

Failure reasons are exactly `unsupported_language` or `language_uncertain`; do not invent a third language reason. A rejected language never proceeds to transcript-dependent analysis.

### 3.4 Mandatory forced alignment

For any transcript-bearing MVP job (ASR produces at least one word), run `forced_alignment_v1` and block `ANALYZING` until word-level aligned timestamps exist. Coarse ASR segment timing must never be substituted for cut-safety decisions.

A zero-word ASR result may continue as alignment `not_applicable` and is restricted to the event-led/no-text path.

If alignment is unavailable after the standard bounded provider/transport attempts, fail the analysis stage with `alignment_unavailable`.

### 3.5 Sentence segmentation `sentence_seg_v1`

Implement the v5.0 contract exactly:

1. input = forced-aligned word timings + optional speaker turns;
2. start a sentence at the first word of the span;
3. end at the earliest terminal-punctuation boundary with a usable word timestamp, or at an inter-word gap `>= SENTENCE_GAP_MS` when either the speaker changes or the next token begins uppercase;
4. if a span exceeds `SENTENCE_MAX_S = 15 s`, split at the largest inter-word gap `>= HARD_SPLIT_MIN_GAP_MS = 20 ms`, ties earliest;
5. if no qualifying gap exists, split at the largest available inter-word gap and set `synthetic_boundary = true`;
6. never split a word.

Do not implement an alternative “precedence” algorithm.

### 3.6 Diarization

Run `pyannote/speaker-diarization-community-1` for speech-bearing multi-speaker inputs. Speaker IDs are deterministic by first appearance.

Diarization is optional for single-speaker footage. When unavailable, set `speaker_id = null` and all speaker-dependent features to `{v:null,m:"not_available_in_stage"}`. Never substitute zero.

### 3.7 Output artifact

Write `transcript_v1.json` with language, words, sentences, speaker turns, forced-alignment provenance, model manifest, input hash and config identity.

## Unit tests

```text
test_asr_word_timestamps_monotonic
test_forced_alignment_required_for_words
test_alignment_unavailable_fails_closed
test_sentence_seg_v1_exact_rules
test_sentence_max_duration_split
test_sentence_synthetic_boundary
test_never_split_inside_word
test_diarization_ids_deterministic
test_no_diarization_nulls_speaker_features
test_zero_word_event_only_path
test_model_manifest_recorded
```

## Integration test for Phase 4

`IT-3-4`: feed only Phase-3 artifacts into Phase 4; it must not read the raw MP4 to reconstruct word/sentence timing. Verify sentence embeddings can be attached deterministically to each sentence.

## Exit gate

All transcript-bearing jobs have forced alignment; all no-text jobs are explicitly identified and constrained to the event/no-text path.



# Phase 4 — Audio, visual, shot, TextTiling and embedding analysis

**Execution mode:** D0 Local Core. Output unlocks D1 promotion.

## Objective

Create all cheap deterministic signals required by Structural Profile, Boundary Map and downstream edit/reframe/Tier 2 logic.

## Tasks

### 4.1 Audio signal extraction

Compute RMS, peaks, silence/pause intervals and robust-z-derived signals using the shared `robust_z_v1`. For nonspeech thresholds use only `local_nonspeech_rms_v1(t)` = 20th percentile of 1 s RMS frames in the rolling 60 s window centered at `t`, edge-truncated.

### 4.2 Visual frame extraction

Use the fixed rates from §1.10. Produce deterministic frame manifests.

### 4.3 Face, motion, screen and shot signals

Use MediaPipe face detection, Farneback optical flow and PySceneDetect `ContentDetector` for shot boundaries. Instantiate `ContentDetector` with `threshold=SHOT_CONTENT_THRESHOLD = 27.0`, `min_scene_len=SHOT_MIN_SCENE_FRAMES = 15` frames, and `luma_only=false`.

Implement `screen_content_v1` deterministically because the v5.0 reframe contract consumes screen-content boxes/masks:

1. convert the sampled frame to grayscale;
2. run Canny with `threshold1=50`, `threshold2=150`, `apertureSize=3`, `L2gradient=false`;
3. find external contours with `RETR_EXTERNAL` + `CHAIN_APPROX_SIMPLE`;
4. approximate each contour with `approxPolyDP(epsilon=0.02 * perimeter)` and keep quadrilaterals with exactly four vertices, convexity, area fraction in `[0.10, 0.95]` of frame area, and aspect ratio in `[0.60, 2.50]`;
5. choose the largest remaining quadrilateral; ties use lexicographically smallest `(y, x, width, height)` of the bounding box;
6. require the same candidate box (IoU >= 0.80) in at least 3 of the previous 5 sampled frames to emit a detection; otherwise emit `no_detection`.

Persist the screen box/mask and detector version in the visual artifact. Do not use OCR or an LLM for MVP screen detection.

### 4.4 Sentence embeddings

Encode every sentence with pinned `BAAI/bge-small-en-v1.5`. Persist normalized embeddings as versioned artifacts and pgvector rows. Store model ID/revision/checksum/backend in config provenance.

The same sentence embeddings are reused by cohesion, TextTiling depth, novelty and repair bridge tests. No downstream stage may silently re-embed with another model.

### 4.5 `TextTiling_depth_v1`

Implement exactly:

```text
L = mean of up to W sentence embeddings ending at boundary b
R = mean of up to W sentence embeddings beginning at b+1
gap(b,W) = 1 - cosine(L,R)
left_peak  = max gap over previous W-1 complete boundaries
right_peak = max gap over next W-1 complete boundaries
depth(b,W) = max(0, left_peak-gap) + max(0, right_peak-gap)
```

Incomplete windows produce `null` and are skipped downstream. Use `W=5` for semantic and `W=25` for topic.

### 4.6 Artifact set

Write:

```text
audio_features_v1
visual_features_v1
shot_map_v1
sentence_embeddings_v1
texttiling_depth_v1
```

## Unit tests

```text
test_local_nonspeech_rms_rolling_window
test_robust_z_zero_mad
test_texttiling_depth_exact
test_texttiling_incomplete_window_null
test_embedding_model_identity
test_embedding_determinism
test_super_unit_embedding_shape
test_feature_bin_alignment
test_face_ratio_bounds
test_motion_nonnegative
test_shot_boundaries_monotonic
```

## Integration test for Phase 5

`IT-4-5`: construct global/local Structural Profiles and Boundary Map from artifacts only. Verify every consumed signal has a defined `{value, missing_reason}` and no direct z-score implementation exists outside the shared helper module.

## Exit gate

All required deterministic analysis artifacts exist and are reproducible without raw-media re-analysis.



# Phase 5 — Structural Profile, Boundary Map and deterministic discovery

**Execution mode:** D0 implementation + D1 hosted parity after promotion.

## Objective

Implement v5.0 discovery, qualification and region budgeting exactly, including event-safe boundaries and deterministic tie handling.

## Tasks

### 5.1 Global/local Structural Profile

Implement 10-second bins, robust scaling, change points, minimum segment merging, the <180 s single-segment rule and additive strategy activation exactly as the product plan specifies.

### 5.2 Boundary scores and missingness

Implement every boundary family with exact `{score, missing_reason}` semantics. A family is null **only** when its input signal is unavailable. A computed zero is numeric zero. No diarization means speaker-dependent families are null with `not_available_in_stage`.

Zero-evidence `StartScore`/`EndScore` returns finite `0.0` with `no_evidence`.

### 5.3 Event-safe cuts

Implement `event_safe_cut_v1`, `latest_safe_before` and `earliest_safe_after` from §2.3. All event starts/ends must be resolver-produced.

### 5.4 Discovery seeds and starts

Implement v5.0 Step 1–2 exactly:

```text
speech seeds: QA, HOOK, TOPIC
 event seeds: EVENT
10 seeds per 10-minute window
speech: own sentence start + best other safe start in the 20 s lookback
at most 2 starts per seed
event: latest safe boundary <= onset
reject event lead-in > 15 s
```

Record actual event lead-in and whether preferred lead-in was met. Never invent a start timestamp by arithmetic.

### 5.5 End candidates and event settle

Implement the exact v5.0 Step 3 decision order, including:

- STOP is always an included natural completion candidate even if `EndScore < END_MIN`;
- speech stop/reach logic and the separate 300 s single-idea extension;
- event settle search bounded by `MAX_EVENT_S`;
- detected settle => start-of-stable-interval `settle_ms`, `settle_source=detected`, safe end after required settle tail;
- no settle => `settle_ms=null`, `settle_source=capped`, safe end only after onset;
- unsafe event end => `no_safe_event_end`.

### 5.6 Qualification

Implement `QC-1` through `QC-6` exactly. No LLM qualification. Preserve rejected regions as artifacts. Apply the event-specific applicability rules from v5.0.

### 5.7 Dedup / budget / determinism

Implement `R_DISC`, nested regions, source overlap/dedup thresholds, and deterministic total ordering. Every sort ends with the v5.0 tie-break sequence; no stable-sort behavior may depend on runtime/library implementation.

### 5.8 Baselines

Implement `baseline_uniform`, `baseline_fixed_window` and the required adaptive comparison using the exact one-to-one matcher and cluster bootstrap metrics.

## Unit tests

```text
test_startscore_missingness
test_zero_evidence_is_not_weak_evidence
test_event_safe_cut_never_unsafe
test_event_lead_in_limit
test_event_settle_bounded
test_event_detected_settle_branch
test_event_capped_settle_branch
test_stop_point_always_candidate
test_single_idea_extension_reachability
test_qc_1_to_qc_6
test_context_dependency_exact
test_total_order_ties
test_nested_region_dedup
test_rdisc_budget
```

## Integration test for Phase 6

`IT-5-6`: run discovery/qualification on all fixtures, then pass only qualified regions to Tier 1. Assert no unsafe event endpoint, no stale qualification namespace, and no profile-dependent discovery cap.

## Exit gate

Adaptive discovery is reproducible, profile-independent and passes the discovery gate before deeper candidate processing is enabled.



# Phase 6 — Tier 1 prioritization and style classification

**Execution mode:** D0 implementation + D1 hosted parity after promotion.

## Objective

Rank qualified Source Regions cheaply, classify style before edit planning, and implement the monotonic backfill semantics.

## Tasks

### 6.1 Tier 1 feature vector

Implement the exact v5.0 Tier 1 features, normalization, missingness and fixed weights. `t1.duration_fit` must consume the shared `d_clean_v1(region, export_profile_id)` result and use the **production** compression ceiling, never the study ceiling. Event final-duration fit uses `EVENT_MIN_FINAL_S = 6`.

### 6.2 Selection and backfill

Implement the ranked cursor exactly:

- one monotonic cursor over the whole ranked Tier-1 population;
- every candidate is considered at most once globally;
- overlap-skipped candidates are permanently skipped once the cursor passes them;
- accepted candidates are not reconsidered;
- cursor advances on every candidate;
- at most `BACKFILL_BATCH = 3` per round and `BACKFILL_MAX_ROUNDS = 2`;
- return to `CLASSIFYING_STYLE` for backfill candidates;
- total edit-planned regions never exceeds `K_T1`.

### 6.3 Style classifier

Run `content_style_v1` before edit planning. Use exact `style_prompt@1`, deterministic head/tail truncation and one schema retry. Transport failures follow §2.4 and do not become style guesses. Low confidence falls back to `other`.

### 6.4 Visual format

Implement final/source `visual_format` rules exactly, including explicit missing-signal handling:

```text
mixed            iff face >= 0.20 AND screen >= 0.20
screen_capture   iff screen >= 0.50
 talking_head    iff face >= 0.20
other_visual     otherwise
```

When both rates are missing, return `other_visual` with `visual_format_missing`; when only one is missing, skip rules requiring the missing signal rather than substituting zero.

The S-G1 calibration report must cover missing-branch behavior and final visual format vs reframe outcomes.

## Unit tests

```text
test_tier1_duration_uses_dclean
test_tier1_ignores_study_ceiling
test_monotonic_backfill_cursor
test_overlap_candidate_permanently_skipped
test_backfill_round_limit
test_style_runs_before_edit_planning
test_style_transport_error_not_fabricated
test_style_truncation_head_tail
test_visual_format_missing_signal
```

## Integration test for Phase 7

`IT-6-7`: feed ranked/style-labeled regions into edit planning. Assert every planner input has exactly one style artifact and one immutable export profile.

## Exit gate

Only the bounded Tier-1 population reaches expensive edit planning, and backfill cannot reintroduce candidates previously skipped.



# Phase 7 — Edit units, constrained edit planning and DP

**Execution mode:** D0 implementation + D1 hosted parity after promotion.

## Objective

Generate the three production plan intensities with exact DP feasibility, event trim semantics and study-only ratio-target plans.

## Tasks

### 7.1 Speech edit units

Construct sentence units, run-on guards, glue groups G1/G2 and super-units. G0 is retired. Opening positions may only be super-unit starts.

### 7.2 Event-led plans

Event-led plans are trim-only. They receive no speech pause micro-edits. Their generation ratio cap is `EVENT_EDIT_MAX_RATIO = 1.5`; their final-duration minimum is `EVENT_MIN_FINAL_S = 6`.

### 7.3 Unit value

Implement the exact bounded v5.0 value function and versioned filler/stopword vocabularies. Use `super_unit_embedding_v1` for novelty and bridge-test inputs.

### 7.4 Forced opening/completion

`minimal` retains the whole Source Region after canonical cleanup. `balanced` and `aggressive` use the opening-candidate procedure. The completion unit is always the final super-unit. Opening tie tolerance is `OPENING_OBJ_TOL = 0.10`.

### 7.5 Production DP

Implement state:

```text
f[i][k][b][s][q]
```

where `i` = processed unit index, `k` = kept units, `b` = bucketed retained duration (`DP_BUCKET_S = 0.1`), `s` = last-unit/interval state, and `q` = current retained interval-length bucket capped at the minimum-interval threshold.

Base state:

```text
f[0][0][0][0][0] = 0
```

All other initial states are `-∞`.

Each DP state stores up to `DP_POOL = 20` distinct kept-unit-id sequences. Objectives are rounded to `1e-6` before comparison and tied by lexicographic kept-unit-id sequence. The interval-length state must prevent generating intervals shorter than `MIN_KEEP_INTERVAL_S`; this constraint is not a post-filter-only rule.

### 7.6 Exact duration/join reserve

Use `DP_BUCKET_S = 0.1` and reserve authoritative join overlap:

```text
join_reserve_ms = (MAX_INTERVALS - 1) * max(0, LOUDNESS_XFADE_MS - CROSSFADE_MS)
```

Generation checks account for this reserve. Exact post-filtering is performed on the millisecond timeline after authoritative joins. The final ratio must satisfy the hard v5.0 cap; do not add an arbitrary production tolerance.

### 7.7 Production build order

Use exactly:

```text
minimal
balanced (primary cap)
balanced (extended cap, only when D_clean > extended_max and style allows)
aggressive
```

Deduplicate by retained-duration relative difference or retained-time Jaccard, then keep at most three production plans.

### 7.8 Cleanup

`d_clean_v1` is the canonical minimal-cleanup computation. Apply its exact deterministic pause-shortening walk once before production content DP and never recompute a hypothetical cleanup elsewhere.

### 7.9 Study-only ratio targets

When `STUDY_MODE = true`, after normal production plans, generate speech-led study plans for every feasible target in `{4.5,5,6,7,8}` using the exact target window, tolerance and slack in v5.0.

Study plans:

```text
intensity = study_ratio
study_target_ratio = target
STUDY_MAX_PLANS_PER_REGION = 5
```

They are not counted against the three production plans, are never shown or sent to production ranking, and are used only to populate Task 3 compression-band evaluation. Study judge calls use a separate region budget of 10.

## Unit tests

```text
test_super_unit_integrity
test_event_trim_only
test_event_ratio_cap_1_5
test_dclean_exact_walk
test_dp_state_has_interval_dimension
test_dp_base_state_exact
test_dp_k_best_per_state
test_dp_tie_break_deterministic
test_dp_interval_minimum
test_dp_join_reserve
test_exact_ms_postfilter
test_production_plan_build_order
test_plan_dedup
test_study_ratio_targets_reachable
test_study_plans_not_in_production_pool
```

## Integration test for Phase 8

`IT-7-8`: generate production and study plans for fixtures, run Layer 1, and verify production plans never exceed the production cap while study plans can populate >4:1 bands without entering the production candidate pool.

## Exit gate

Every qualified region either produces a valid production plan set or a precise failure reason; no DP state can manufacture an invalid interval.



# Phase 8 — Layer 1 verification, semantic judge and deterministic repair

**Execution mode:** D0 implementation + D1 hosted parity after promotion.

## Objective

Guarantee deterministic temporal/audio validity, exact event/user-edit semantics, controlled semantic judgment, and one-pass repair.

## Tasks

### 8.1 Layer 1 order

Run exactly:

```text
1 schema validation
2 source-range validation
3 cut boundary safety
4 retained-interval ordering
5 audio join validation
6 timeline recomputation
7 duration checks
8 compression checks using the selected mode/profile
9 event-specific checks
10 final timeline-derived feature computation
```

For event-led plans, enforce final duration >= 6 s and ratio <= 1.5. For speech-led plans, use the selected export profile's `min_s/max_s` and the effective compression ceiling.

### 8.2 Audio joins and timeline authority

Generator joins are provisional. Layer 1 computes `applied_crossfade_ms` and rewrites the authoritative final timeline. `verified_edit_plan` contains the verified joins/timeline only.

### 8.3 Layer 2 applicability

Run the semantic verifier **only** for speech-led plans with retained transcript word count >= `JUDGE_MIN_WORDS = 25`.

Event-led plans and speech-led plans below 25 words skip Layer 2 and may end as `LAYER1_ONLY_PASS`. They are class B and are not semantically equivalent to `TRANSCRIPT_VERIFIED_PASS` plans.

### 8.4 Viewer-only judge

Use exact `verifier_prompt@2` with `deepseek-v4-pro`. Judge input contains only the edited transcript, `[CUT k]` markers and allowed output-timeline metadata. No pre-region context and no repair-engine inputs are sent to the judge.

### 8.5 LLM output validation and failure handling

Run schema validation then `validate_judge_semantics@1`. Transport and invalid-output semantics follow §2.4. Invalid output consumes the lineage call budget; transport retries do not. Store raw output unmodified and canonical normalized input + hash.

### 8.6 Verdict and budget

Production:

```text
MAX_PLANS_PER_REGION = 3
MAX_JUDGE_CALLS_PER_PLAN = 2
MAX_JUDGE_CALLS_PER_REGION = 6
VERIFY_ALL_PLANS = true
```

Invalid-output retry may be the second call; Stage R does not reset the lineage budget. Study-only plans use the separate 10-call region budget.

### 8.7 Repair

Implement `plan_repair` + apply + Layer 1 + duplicate check as one deterministic Stage-R pass. Use exact issue mapping, bridge test, stale-target semantics and stable `cut_id` targets from v5.0. No arbitrary “earlier sentence” interpretation of R2.

`REPAIR_RESTORE_DEPTH = 1`. Record `repair_insufficient` according to the v5.0 diagnostic rule. No second automatic repair.

### 8.8 User content edits

A user content edit creates a new `EditPlan` lineage with `plan_origin = user_edit` and `parent_edit_plan_id`; it is snapped to sentence-safe boundaries for speech-led content or `event_safe_cut_v1` for event-led content.

Layer 1 applies the same selected profile/final-duration/interval/compression constraints. Layer 2 runs only for speech-led >=25 words.

`PASS` -> verified descendant. `REPAIRABLE` and `HARD_FAIL` are terminal for the user edit: set candidate state `BLOCKED_USER_EDIT`, create no repaired descendant, and keep the previous accepted plan intact. User edits are never auto-repaired.

Reframe-only changes never create a content-edit lineage and skip content verification.

## Unit tests

```text
test_layer1_order
test_event_final_minimum_6s
test_event_ratio_cap_1_5
test_audio_join_authority
test_timeline_recompute
test_effective_compression_cap
test_layer2_only_for_speech_25_words
test_event_layer1_only_pass
test_judge_viewer_only_input
test_judge_semantic_validator
test_transport_retry_does_not_consume_budget
test_invalid_output_consumes_budget
test_verify_all_plans
test_repair_cut_id_mapping
test_repair_bridge_test
test_repair_one_pass
test_user_edit_creates_lineage
test_user_edit_repairable_terminal
test_reframe_only_skips_content_verification
```

## Integration test for Phase 9

`IT-8-9`: run production and event-led verification, then hook analysis. Assert event-led outputs have `LAYER1_ONLY_PASS`, class B semantics, and no hook LLM invocation.

## Exit gate

Every downstream-eligible plan is represented by one immutable `verified_edit_plan`, and all user-edit failures are terminal and auditable.



# Phase 9 — Hook analysis and content-style finalized features

**Execution mode:** D0 implementation + D1 live-LLM contract test.

## Objective

Compute region/opening and final-short hooks with exact output-timeline semantics, validation, missingness and adoption controls.

## Tasks

### 9.1 Two hook computations

Use `hook_lexical@1` only for opening selection and Tier 1. Use `hook_analysis_v1` for the final verified plan.

### 9.2 Exact final hook input

Build the output-timeline `signal_window` and `text_window` exactly from v5.0. Never reconstruct output time from source timestamps.

### 9.3 Event-led rule

Do **not** call the hook LLM for event-led/class-B plans in MVP. Their text-dependent hook features are `not_applicable`; deterministic non-text signals may still be recorded as allowed by v5.0.

### 9.4 Missingness and semantic validation

Implement the exact feature missingness table and `validate_hook_semantics@1`. `no_detection` is valid negative evidence. `not_applicable`, `extraction_failed`, `invalid_output`, `not_available_in_stage` and `not_run` are unavailable states, not equivalent to zero.

### 9.5 Exact prompt

Copy `hook_prompt@1` **verbatim** from the v5.0 product plan into `prompts/hook_analysis_prompt@1.txt`. The code must use that versioned file; do not embed a modified prompt string elsewhere.

### 9.6 Adoption units

Hook adoption units are:

```text
{A+B}
{C}
```

Evaluate on speech-led, text-eligible Task 3 openings with leave-one-video-out training, training-fold median imputation plus missingness indicators, fixed inner-LOO ridge penalty selection, Spearman correlation and video-cluster bootstrap (`BOOTSTRAP_B=2000`). H-G4 requires A+B to beat lexical and C to beat A+B with the bootstrap lower bound above 0. H-G5 is the separate Tier-2 non-degradation gate.

There is no separate A-vs-B adoption decision. `HOOK_GROUPS_ENABLED = []` by default. No `hook_lexical@1` fallback is allowed in Tier 2.

## Unit tests

```text
test_hook_lexical_only_for_opening_tier1
test_hook_output_timeline_mapping
test_hook_text_window_precedence
test_hook_semantic_validator
test_no_detection_is_negative
test_event_led_skips_hook_llm
test_hook_transport_failure_handling
test_hook_cache_key_includes_all_inputs
test_hook_prompt_hash
```

## Integration test for Phase 10

`IT-9-10`: pass verified plans through hook, reframe and Short Candidate construction. Assert event/class-B plans contain no semantic-hook LLM result and Tier 2 reads only permitted hook groups.

## Exit gate

Hook artifacts are immutable, versioned, validated and tied to the verified output timeline.



# Phase 10 — Reframe planning, caption planning and Short Candidate construction

**Execution mode:** D0 implementation + D1 hosted parity after promotion.

## Objective

Produce deterministic vertical composition, captions and the complete Tier-2-ready Short Candidate from verified artifacts only.

## Tasks

### 10.1 Final visual format

Compute `final_visual_format` from the verified retained timeline. Apply the exact v5.0 threshold and missing-signal rules from Phase 6. Do not reuse coarse Source Region visual format when the final timeline differs.

### 10.2 Reframe deterministic crop search

Consume only `verified_edit_plan`, `final_visual_format`, output-timeline mapping, per-frame face boxes and screen-content boxes/masks.

For each sampled output frame:

1. build required points from up to two dominant faces when faces are required and the dominant screen-content centroid when screen is required;
2. enumerate valid 9:16 crop centers on a `REFRAME_GRID_PX = 16` source-pixel grid plus each clamped required-point centroid;
3. score inclusion of required points/boxes;
4. ties -> minimum distance to previous center, then smallest `(y,x)`;
5. smooth centers with a 5-frame median;
6. limit per-frame center jumps to 120 px.

### 10.3 Strategy order and confidence

Implement exactly:

```text
multi_speaker if two dominant faces are simultaneously required and one crop cannot retain both
otherwise face_aware when a required face exists
otherwise fixed_center when required screen/content fits
otherwise blurred_background
```

If no required signal exists, use `fixed_center` and record `reframe_signal_missing`.

For each frame, confidence = 1.0 when all required points/boxes are inside, 0.5 when the primary required item is inside but a secondary item is partly outside, else 0.0. Mean the frame scores. `status=ok` iff strategy is fixed_center/face_aware/multi_speaker and confidence >= .6; `degraded` for blurred_background/no-signal/below threshold; `infeasible` only when all allowed strategies fail.

### 10.4 `multi_speaker`

Render as two vertically stacked portrait panels of `1080x960`, one per dominant face, no stretching, unused pixels filled with the deterministic blurred-background procedure below.

### 10.5 Blurred-background fallback

When `blurred_background` is selected, create the background by scaling the retained source frame to fill 1080x1920, center-cropping to 9:16, then applying Gaussian blur with `BLUR_BACKGROUND_SIGMA = 24`. Overlay the un-stretched source frame scaled to fit entirely inside 1080x1920 and centered. Do not add borders or decorative graphics.

### 10.6 Reframe artifact

Write exact `reframe_plan_v1` fields including lineage fields, `verified_edit_plan_id`, `content_unchanged`, `final_visual_format`, strategy, status, confidence, reasons and config identity.

### 10.7 Caption plan

Generate `caption_plan_v1` from verified output-timeline word timings. Group consecutive words into 1–2 lines, prefer sentence boundaries, otherwise nearest word boundary respecting `CAPTION_MAX_CHARS_PER_LINE = 32`. Every cue stores `output_start_ms`, `output_end_ms`, text, line count and safe-zone placement. Safe zone:

```text
x = 0.05–0.95
 y = 0.78–0.93
```

The renderer consumes this artifact without reconstructing timing.

### 10.8 Short Candidate

Construct `short_candidate_v1` with `verified_edit_plan_id`, Source Region/source video IDs, plan origin/parent/replacement IDs, export profile ID/hash, `hook_analysis_id`, `content_style_id`, `reframe_plan_id`, `caption_plan_id`, comparability class, features and eligibility/exclusion reason.

No downstream IDs are stored inside `verified_edit_plan` itself.

## Unit tests

```text
test_final_visual_format_from_verified_timeline
test_reframe_grid_search
test_reframe_tie_break
test_reframe_median_smoothing
test_reframe_jump_limit
test_reframe_strategy_order
test_reframe_confidence_status
test_multi_speaker_layout
test_caption_plan_output_timeline
test_caption_32_char_limit
test_caption_safe_zone
test_short_candidate_downstream_ids
test_reframe_lineage
```

## Integration test for Phase 11

`IT-10-11`: build candidates from verified fixture plans, ensure inapplicable features are marked correctly, and run Tier 2 heuristic scoring.

## Exit gate

Every eligible verified plan has immutable reframe and caption artifacts or an explicit exclusion reason, and a complete `short_candidate_v1` can be constructed without obsolete artifacts.



# Phase 11 — Tier 2 heuristic ranking, uncertainty, MMR and display selection

**Execution mode:** D0 implementation + D1 hosted parity after promotion.

## Objective

Implement the normative v5.0 Tier 2 eligibility, feature vector, heuristic score, comparability classes and display-selection system.

## Tasks

### 11.1 Eligibility X1–X6

Evaluate in exact order. Excluded candidates remain stored with `exclusion_reason`.

```text
X1 final_status in {TRANSCRIPT_VERIFIED_PASS, LAYER1_ONLY_PASS}
X2 not study mode
X3 hook_analysis.status != failed
X4 reframe.status in {ok, degraded}
X5 coverage >= 0.5
X6 no required feature group is not_run/not_available_in_stage
```

`infeasible` reframe is excluded. Study-mode plans are excluded from production Tier 2.

### 11.2 Feature vector and applicability

Implement every v5.0 feature exactly. All features use `{v,m}`.

Important class semantics:

- Class A = `TRANSCRIPT_VERIFIED_PASS`;
- Class B = `LAYER1_ONLY_PASS` (event-led and speech <25 words).

For event-led/class-B plans, mark coherence and text-dependent groups `not_applicable` exactly as the v5.0 subset specifies. Disabled hook groups are also N/A.

### 11.3 Coverage

```text
coverage = present_weight / applicable_weight
```

N/A terms are excluded from numerator and denominator. `extraction_failed`/`invalid_output` remain applicable and reduce coverage. `no_detection` is informative negative evidence, not missingness.

### 11.4 Heuristic v0

Implement the exact weights, terms and rounding from v5.0. Coherence is already normalized to [0,1] and must not be divided by 5 again.

Tier 1 `region_priority_score` is excluded by default; `T2-A1` is the only permitted path to add it.

### 11.5 Candidate-relative features

Reference population = all eligible Short Candidates from the same source video before final ranking. Use shared robust-z with `REL_MIN_POP=8` and `REL_MAD_FLOOR=.05`.

### 11.6 Score order vs display order

Store `score_rank` before display optimization. `display_rank` is the position shown to the user. They are different fields and different decisions.

### 11.7 Display selection

Per region keep the best plan under the v5.0 class-A-over-B rule; retain other plans as alternates. Within each class use retained-source-interval MMR with `MMR_LAMBDA=.7` and hard overlap exclusion at `.30`. Persist immutable `display_selection_v1` with both rank orders, slot allocation, overlap comparisons and all config identity.

### 11.8 Class separation

Class A and B rank separately. Cross-class merge is disabled until T2-G3 passes. Do not invent a class-B penalty.

### 11.9 T2-A1 and Task-4 gates

Implement the Tier-1-score-feature ablation on the **dev** Task 4 pool only. The sealed pool confirms once. No sealed result drives tuning.

## Unit tests

```text
test_x1_x6_order
test_study_plan_excluded
test_reframe_infeasible_excluded
test_event_class_b_feature_subset
test_n_a_coverage
test_failure_reduces_coverage
test_no_detection_informative
test_coherence_not_double_normalized
test_t1_score_excluded_by_default
test_t2_a1_dev_sealed_separation
test_same_video_relative_population
test_class_a_b_separation
test_mmr_retained_intervals
test_display_selection_immutable
test_score_rank_vs_display_rank
```

## Integration test for Phase 12

`IT-11-12`: rank a complete fixture video, display candidates, edit one candidate, and verify the parent display selection remains unchanged unless the user explicitly requests a rerank revision.

## Exit gate

Tier 2 ranking and display selection are deterministic, class-aware and auditable from immutable artifacts.



# Phase 12 — Review UI and candidate-level lifecycle

**Execution mode:** D0 implementation + D1 hosted end-to-end review flow.

## Objective

Expose candidates and implement the independent candidate lifecycle and exact user-edit semantics.

## Candidate state machine

Implement exactly:

```text
DISPLAYED → USER_EDITING → REVERIFYING → DISPLAYED
                                      └→ BLOCKED_USER_EDIT
DISPLAYED → ACCEPTED → RENDERING → RENDERED
```

This state machine is independent of job-level processing states.

## User content edits

A trim/simplification:

```text
DISPLAYED
→ USER_EDITING
→ new EditPlan lineage (plan_origin=user_edit)
→ safe-boundary snap
→ Layer 1
→ Layer 2 only when speech-led and >=25 words
→ PASS => new verified descendant
→ REPAIRABLE/HARD_FAIL => BLOCKED_USER_EDIT; parent remains intact
→ hook/reframe/Tier2 refresh
→ DISPLAYED
```

The verified candidate records `replaces_short_candidate_id` so the new candidate replaces its parent **in place** in the current display slot.

Do not rerun display selection automatically.

## Reframe-only edits

Create a new reframe lineage referencing the same verified edit plan. Do not create a content Edit Plan lineage and do not rerun content verification.

## Explicit rerank

Only an explicit user-requested rerank creates a new immutable revision of `display_selection_v1`. The prior selection artifact remains immutable.

## UI

Keep the routes and candidate card fields defined in §6, adding visible state, exclusion reason and whether semantic validation was performed. Show event-led/class-B candidates as “not semantically validated”.

## Unit tests

```text
test_candidate_state_machine_exact
test_job_state_independent_from_candidate_state
test_user_content_edit_lineage
test_user_edit_safe_boundary_snap
test_user_edit_repairable_terminal
test_parent_candidate_remains_intact
test_user_edit_replaces_parent_in_place
test_reframe_only_lineage
test_reframe_only_no_content_verification
test_display_selection_not_rerun_automatically
test_explicit_rerank_creates_selection_revision
```

## Integration test for Phase 13

`IT-12-13`: accept a candidate, render it, and verify render request IDs/hashes match the verified plan + reframe plan + render profile + caption plan when applicable.

## Exit gate

Users can edit/accept candidates without bypassing verification, silently reshuffling the display, or mutating historical artifacts.



# Phase 13 — Rendering and immutable final outputs

**Execution mode:** D0 implementation + D1 hosted render/upload parity.

## Objective

Produce final MP4 outputs from exactly the verified content/timeline, reframe, caption and export-profile authorities.

## Fixed MVP render profile

Use the immutable selected `render_profile_v1`; the default YouTube Shorts values are:

```text
platform       = youtube_shorts
aspect_ratio   = 9:16
resolution     = 1080x1920
frame_rate     = 30
video_codec    = H.264
pixel_format   = yuv420p
audio_codec    = AAC
container      = MP4
caption_mode   = burned_in
loudness_policy= source_normalized
```

## Caption rendering

Use deterministic ASS rendering with this fixed active MVP style:

```text
font: Noto Sans
font size: 64 px at 1080x1920
maximum lines: 2
maximum characters per line: 32
safe zone: x=.05–.95, y=.78–.93
text color: #FFFFFF
outline color: #000000
outline width: 4 px
alignment: centered
word-by-word animation: disabled
```

The `youtube_shorts` MVP profile uses `caption_mode=burned_in`. `none` is schema-valid and renders with no caption input. `sidecar` is schema-valid but disabled in the MVP profile; do not expose it in the UI until a later explicit profile/config change.

Consume `caption_plan_v1` directly. Do not generate a new ASS timing plan from source words inside the renderer. The caption plan already enforces:

```text
1–2 lines
max 32 chars/line
safe zone x=.05–.95, y=.78–.93
```

Do not add word-by-word animation in MVP.

## Render authorities and pipeline

1. resolve signed source object;
2. load exactly one `verified_edit_plan`;
3. load exactly one `reframe_plan_v1`;
4. load exactly one immutable `render_profile_v1`;
5. load `caption_plan_v1` when caption mode is not `none`;
6. construct FFmpeg filter graph from the verified timeline and reframe plan;
7. apply verified authoritative audio joins;
8. render captions from the caption plan;
9. normalize loudness toward `-14 LUFS` with true peak `<= -1.0 dBTP`;
10. encode according to the render profile;
11. probe final output;
12. compute SHA-256 and write immutable render artifact.

The renderer may not alter timing/content/order/crop/profile/loudness/caption timing outside these artifacts.

## Render validation

At minimum reject:

```text
resolution mismatch
codec/container/profile mismatch
A/V duration mismatch > 20 ms
invalid sample rate
black-frame fraction > BLACK_FRAME_MAX_FRACTION
missing checksum
missing required render input hash
```

Black-frame validation samples the rendered output at `BLACK_FRAME_SAMPLE_FPS = 2` and marks a frame black when its mean luma is `< BLACK_FRAME_LUMA_THRESHOLD = 16/255`. Reject only when the fraction of black sampled frames exceeds `BLACK_FRAME_MAX_FRACTION = 0.02`.


## Unit tests

```text
test_render_profile_schema
test_render_profile_immutable
test_caption_plan_consumed_without_retiming
test_caption_32_char_limit
test_caption_safe_zone
test_loudness_minus14_lufs_target
test_true_peak_minus1_db_max
test_render_authority_ids
test_reframe_transform_order
test_output_duration_matches_verified_timeline
test_render_hash
```

## Integration test for Phase 14

`IT-13-14`: render a fully accepted fixture candidate, persist immutable output, create publication/outcome metadata and verify all authority IDs/hashes and config identity.

## Exit gate

A render is reproducible from exactly the immutable render authorities and contains no renderer-invented timing or caption decisions.



# Phase 14 — Publication metadata, performance collection and outcome dataset

**Execution mode:** D2 Controlled Beta only.

## Objective

Create the first-party dataset required for later learned ranking without confusing exposure with performance.

## Tasks

### 14.1 Publication record

Record:

```text
published
published_video_id
publication_platform
publication_timestamp
published_title
published_description
published_caption
published_hashtags
account_size_snapshot
promotion_status
render_profile_id
```

### 14.2 YouTube OAuth

Use official OAuth 2.0 authorization.

Store encrypted refresh tokens in Railway secret-backed storage for the hosted backend. Never expose refresh tokens to the frontend.

Request minimum required scopes.

### 14.3 Metrics

Store public metrics where available:

```text
views
likes
comments
```

Store authorized Analytics metrics only when OAuth permission exists:

```text
average_view_duration
average_view_percentage
retention metrics where accessible
```

Missing metrics remain missing; do not impute them as zero.

### 14.4 Exposure metadata

Record:

```text
whether_shown
whether_selected
whether_published
score_rank
```

Unpublished clips are not negative-performance labels.

## Unit tests

```text
test_outcome_schema
 test_missing_metric_is_not_zero
 test_oauth_token_encryption
 test_public_vs_authorized_metric_separation
 test_unpublished_not_negative
 test_publication_metadata_capture
```

## Integration test for Phase 15

`IT-14-15`:

Create a synthetic set of published/unpublished/selected/unselected candidates and run dataset export. Assert split logic groups by creator/source video and never uses future performance snapshots for earlier examples.

## Exit gate

A leakage-safe outcome dataset is produced from real product activity.

---

# Phase 15 — Evaluation, calibration and learned-ranker readiness

**Execution mode:** D2 Controlled Beta only, with sealed confirmation read only at the final confirmation step.

## Objective

Run the complete v5.0 evaluation program without leaking sealed test data into tuning.

## 15.1 Evaluation dataset

Build exactly:

```text
56 source videos
7 structural types
40 dev videos
16 sealed-test videos
creator-disjoint split
stratified by structural type
```

No feasible split is silently relaxed. The deterministic split procedure and minima are exactly those of v5.0 §2.36.1.

Task 4 pools:

```text
Dev:    400 same-video, same-class pairs
        >= 32 distinct dev videos
        <= 10% pairs from one video
        >= 50% cross-region
        sibling pairs tracked separately

Sealed: 160 same-video, same-class pairs
        >= 12 distinct sealed videos
        same share/cross-region constraints
        opened once for final confirmation only

Cross-class: >= 40 pairs across >= 8 videos
             separate evaluation set
             never used for training/tuning
```

### 15.2 Task 1/2 labels

Implement the exact v5.0 labeling protocol. Labels longer than `MAX_SINGLE_IDEA_REGION_S` are split at a strong internal boundary or marked out-of-scope and reported.

### 15.3 Task 3

Generate:

```text
100 speech-led plans
>= 20 in each of the 5 compression bands
>= 15 event-led or low-speech plans
```

Band assignment always uses the final verified compression ratio. Event/low-speech results are reported separately from speech-led semantic-judge precision.

### 15.4 Discovery/Tier-1/verification/hook/Tier-2 gates

Run all v5.0 gates using the exact metrics and video-cluster bootstrap (`BOOTSTRAP_B=2000`). Do not replace cluster bootstrap with independent-plan intervals.

### 15.5 Sealed-data rule

All decisions involving weights, thresholds, hook adoption, Tier-1 scoring, Tier-2 feature adoption or merge behavior are made using dev data only. The sealed set is opened exactly once for confirmation and cannot trigger tuning.

### 15.6 Calibration outputs

Write immutable:

```text
evaluation_report_v1.json
calibration_report_v1.json
adoption_decision_v1.json
```

Each contains split IDs/hashes, config identity and dataset sampling metadata.

## Unit tests

```text
test_dataset_56_videos
test_creator_disjoint_stratified_split
test_split_fails_closed_when_infeasible
test_task4_dev_400_pairs
test_task4_sealed_160_pairs
test_task4_dev_video_share
test_task4_cross_region_share
test_cross_class_separate
test_sealed_cannot_modify_config
test_task3_final_band_assignment
test_cluster_bootstrap_seeded
test_gate_calculation
```

## Integration test for Phase 16

`IT-15-16`: export the permitted dev training/evaluation dataset, prove no sealed/cross-class rows enter training, train the fixed learned-ranker implementation and persist dataset/split hashes.

## Exit gate

Every reported decision can be reproduced from the dev pool; sealed data is untouched until final confirmation.



# Phase 16 — Learned Tier 2 ranker

**Execution mode:** D2 Controlled Beta only.

## Objective

Enable LightGBM pairwise ranking only after the v5.0 heuristic/Tier-2 gates and data conditions are satisfied.

## Fixed model

```text
LightGBM
objective = lambdarank / pairwise ranking
```

## Training data

Allowed:

```text
400-pair same-class Task 4 DEV pool
same-class first-party preference data after sufficient volume
```

Never train on:

```text
160-pair sealed pool
cross-class Task 4 evaluation pairs
unpublished candidates as negatives
future outcomes
same-source-video leakage across train/test
```

The sealed pool is confirmation only.

## Split

Group by `creator_id` and `source_video_id` and respect publication time. No video may occur in both a training and held-out measurement fold.

## Features

Use the exact v5.0 Tier-2 feature vector, including relative features and missingness indicators. Do not add `region_priority_score` unless `T2-A1` is explicitly adopted through its dev+sealed gate.

## Training artifact

Persist:

```text
ranker_id
model_revision
feature_schema_version
training_dataset_sha256
train_split_sha256
hyperparameter_manifest
config_version
config_sha256
```

## Unit tests

```text
test_training_excludes_sealed
test_training_excludes_cross_class
test_group_split_no_video_leakage
test_temporal_split
test_feature_schema_matches_training
test_t2_a1_feature_default_excluded
test_model_artifact_manifest
test_ranker_deterministic_seed
```

## Integration test for Phase 17

`IT-16-17`: serve learned ranking beside heuristic v0, run both on the same held-out candidates, record metrics and confirm no sealed data was used for fitting.

## Exit gate

Learned ranking remains disabled until all adoption gates pass and provenance proves leakage-free training.



# Phase 17 — Trend metadata experiment

**Execution mode:** D2 Controlled Beta only.

## Objective

Keep trends entirely optional and prove value before enabling.

## Fixed implementation

Use:

```text
YouTube public metadata only where legally/technically accessible
PostgreSQL + pgvector
scheduled metadata collector
```

Initial stored trend fields:

```text
title
description
tags when available
category/topic
publication_timestamp
public engagement metrics
```

Do not build:

```text
unauthorized caption download
third-party audio downloading
web scraping as a product dependency
```

## Experiment

Compare:

```text
core
core + trend metadata retrieval
```

Use fixed evaluation split and report delta with video-cluster bootstrap intervals.

## Unit tests

```text
test_trend_record_schema
 test_no_audio_download_path
 test_trend_feature_vector_version
 test_pgvector_retrieval_shape
 test_feature_cache_key
```

## Integration test for Phase 18

`IT-17-18`:

Run trend-enabled and trend-disabled candidate ranking on the same source videos and confirm that the only feature difference is the trend feature group.

## Exit gate

Trend system remains disabled by default unless the v5.0 ablation gate is passed, and no unauthorized audio/caption download path may be introduced.

---

# Phase 18 — Production hardening and scale

**Execution mode:** P0 Paid Production only.

## Objective

Turn the validated MVP into a resilient service without changing product behavior.

## Tasks

### 18.1 Security

Implement:

- least-privilege Railway service credentials;
- private service-to-service access where supported;
- encrypted secrets;
- signed short-lived media URLs;
- upload/content-type validation;
- object quarantine before processing;
- malware scanning before normalization;
- strict CORS allowlist;
- security headers;
- request body limits;
- audit logs.

### 18.2 Reliability

Implement:

```text
heartbeat every 15 s
worker lease timeout 60 s
stage retry max 3
job resume from last successful artifact
```

### 18.3 Cancellation

Cancellation must:

1. mark job `CANCELLED`;
2. revoke queued downstream work where possible;
3. let already-running worker finish or self-cancel at its next checkpoint;
4. never delete immutable historical artifacts automatically.

### 18.4 Monitoring

Required alarms:

```text
API 5xx rate
queue latency
queue depth
worker failure rate
GPU task duration
LLM error rate
R2 error rate
Railway PostgreSQL CPU/storage/connections
Railway Redis memory/evictions
render failure rate
```

### 18.5 Data retention

Implement source-video deletion workflows while retaining only the minimum metadata required by policy and published-outcome records.

## Unit tests

```text
test_retry_idempotency
 test_job_resume
 test_cancel_transition
 test_artifact_not_deleted_by_retry
 test_security_headers
 test_upload_quarantine_state
 test_alarm_payloads
```

## Integration test

`IT-18-PROD`:

Run a complete production-like job with injected transient failures at every stage boundary and verify successful recovery without duplicate artifacts or invalid state transitions.

## Exit gate

The system recovers deterministically from expected operational failures and retains artifact lineage.

---

# 5.1 v5.0 implementation-conformance matrix

This matrix is mandatory. Each row names the implementation obligation and its tests. The implementation AI must not close the row until the cited conformance test passes.

| v5.0 change | Implementation obligation | Required conformance |
|---|---|---|
| V5-01 | 40-dev / 16-sealed dataset; 400-dev / 160-sealed Task-4 pools; sealed confirmation only | `test_creator_disjoint_stratified_split`, `test_sealed_cannot_modify_config` |
| V5-02 | config snapshot + shared helpers + schemas built in Phase 0 | `test_shared_helpers_are_singleton_imports`, schema/config suite |
| V5-03 | forced alignment, sentence segmentation, TextTiling, embedding provenance, no-diarization nulls | Phase 3/4 exact primitive tests |
| V5-04 | immutable one-profile-per-job; discovery profile-independent | `test_export_profile_immutable`, `test_profile_hash_persisted_on_job` |
| V5-05 | event lead-in/settle/STOP/final-min semantics; safe-cut-only | event discovery + Layer 1 tests |
| V5-06 | study target-ratio generation and separate study judge budget | `test_study_ratio_targets_reachable`, `test_study_plans_not_in_production_pool` |
| V5-07 | 0.1s k-best 5D DP, interval state, join reserve | DP test suite |
| V5-08 | event trim-only and 1.5 ratio cap | event edit/L1 tests |
| V5-09 | transport vs invalid-output LLM retry semantics | LLM retry tests |
| V5-10 | candidate lifecycle, terminal user-edit failure, in-place replacement, explicit rerank revision | Phase 12 state/lineage tests |
| V5-11 | event-led Layer-1-only/class-B/no hook LLM | Phase 8/9 tests |
| V5-12 | deterministic reframe/caption/loudness authorities | Phase 10/13 tests |
| V5-13 | exact hook prompt + semantic validator + adoption units | hook tests + prompt hash |
| V5-14 | Tier-2 applicability, missingness, T2-A1 dev/sealed split | Phase 11/15 tests |
| V5-15 | current identifiers/artifact-ID placement/no duplicate style hash | schema compatibility tests |
| V5-16 | language gate, alignment boundary, backfill, study budgets, downstream-ID placement | Phase 1/3/6/8/10 tests |
| V5-17 | consolidated render/reframe/caption constants | config registry + render tests |

**No-row-is-optional rule:** a phase is incomplete when an applicable matrix row lacks both a passing test and persisted artifact/config provenance.

# 6. API contract summary

## Jobs

### Create job

```http
POST /v1/jobs
Idempotency-Key: <client-generated UUID>
Content-Type: application/json
```

Body:

```json
{
  "source_video_id": "uuid",
  "export_profile_id": "youtube_shorts"
}
```

Response:

```json
{
  "job_id": "uuid",
  "state": "CREATED"
}
```

## Job status

```http
GET /v1/jobs/{job_id}
```

Response contains:

```text
job_id
state
progress
current_stage
stage_runs
error
created_at
updated_at
```

## Candidate retrieval

```http
GET /v1/jobs/{job_id}/candidates
```

Returns candidates sorted by:

```text
display_rank
```

while exposing:

```text
score_rank
```

separately.

---

# 7. Database schema summary

Minimum key relationships:

```text
users
  └─ source_videos
       └─ processing_jobs
            └─ stage_runs
                 └─ artifacts

source_videos
  └─ source_regions
       └─ edit_plans
            └─ verified_edit_plans
                 └─ hook_analyses
                 └─ reframe_plans
                  └─ caption_plans
                 └─ short_candidates
                      └─ review_actions
                      └─ publication_records
                           └─ outcome_snapshots
```

User-authored content edits create new lineage records rather than mutating historical plans.

Reframe-only edits create a new `reframe_plan` lineage.

---

# 8. Exact test hierarchy

Every pull request runs:

```text
1. schema tests
2. unit tests
3. contract tests
4. integration tests with Postgres + Redis
5. fixture pipeline tests
6. frontend type/build tests
```

Nightly CI runs:

```text
full fixture pipeline
GPU smoke test
LLM contract test
render smoke test
```

Weekly evaluation job runs:

```text
regression metrics
candidate-recall regression
verification-failure regression
hook regression
Tier-2 ranking regression
render regression
```

---

# 9. Phase handoff matrix

| Completed phase | Must hand off to next phase |
|---|---|
| 0 | schemas + config identity + migrations + test harness |
| 1 | authenticated source-video job with R2 object |
| 2 | normalized media manifest |
| 3 | transcript/word/sentence/speaker artifact |
| 4 | cheap feature + embedding artifacts |
| 5 | qualified Source Regions |
| 6 | Tier-1-ranked, style-classified regions |
| 7 | raw Edit Plans |
| 8 | verified Edit Plans |
| 9 | hook/style analysis |
| 10 | Short Candidates + reframe plans |
| 11 | ranked/displayed candidates |
| 12 | accepted/rejected/re-edited candidates |
| 13 | immutable rendered shorts |
| 14 | publication/outcome dataset |
| 15 | reproducible calibrated evaluation dataset |
| 16 | learned ranker artifact |
| 17 | measured trend experiment |
| 18 | production-hardened system |

A downstream phase must never silently manufacture a missing upstream artifact.

---

# 10. Definition of Done for the MVP

The MVP is complete only when all conditions below are true:

1. A user can upload a video directly to R2.
2. The job survives API/worker restarts.
3. A source video is normalized deterministically.
4. ASR + forced-aligned word timing are produced for transcript-bearing jobs; speaker timing is produced when diarization is available, otherwise speaker-dependent features are null.
5. Structural/audio/visual/embedding artifacts are produced.
6. Candidate discovery and qualification run according to v5.0.
7. Tier 1 prioritization runs deterministically.
8. Style classification runs before editing.
9. Three production edit intensities are generated; study-only `study_ratio` plans exist only in evaluation/study mode and are never emitted to production ranking.
10. Layer 1 and semantic verification produce immutable `verified_edit_plan`s.
11. Hook analysis runs on the verified timeline.
12. Reframing creates `reframe_plan_v1` from `final_visual_format`.
13. Tier 2 produces score rank and display rank separately.
14. User edits re-enter verification.
15. Accepted candidates render to 1080×1920 MP4.
16. Render provenance points to exactly the required authorities: verified edit plan, reframe plan, render profile, plus caption plan when caption mode is not `none`.
17. Evaluation fixtures pass all required regression tests.
18. Failure injection proves stage idempotency and recovery.
19. No component has an undocumented alternate implementation.
20. No `OPEN`, `PROPOSED`, `EXPERIMENTAL` or `SUPERSEDED` product behavior is accidentally implemented as a default production path.

---

# 11. Explicit non-MVP exclusions

These are intentionally not implemented in the initial production path:

```text
URL import from arbitrary third-party platforms
multi-language product behavior
video-language-model discovery
LLM-driven candidate discovery
LLM-driven Tier 1 ranking
LLM-driven Tier 2 scoring
automatic user-edit repair
cross-class Tier 2 merge before T2-G3
trend features by default
unauthorized third-party caption/audio collection
fine-tuning custom virality models
automatic title/caption generation
```

These exclusions are implementation constraints, not future design questions.

---

# 12. Exact implementation order

An implementation AI must work in this order and must not skip ahead:

```text
Phase 0
  ↓
Phase 1
  ↓
Phase 2
  ↓
Phase 3
  ↓
Phase 4
  ↓
Phase 5
  ↓
Phase 6
  ↓
Phase 7
  ↓
Phase 8
  ↓
Phase 9
  ↓
Phase 10
  ↓
Phase 11
  ↓
Phase 12
  ↓
Phase 13
  ↓
Phase 14
  ↓
Phase 15
  ↓
Phase 16
  ↓
Phase 17
  ↓
Phase 18
```

The only allowed internal parallelism is work that is explicitly independent within a phase. Cross-phase parallel implementation is not allowed until the next-phase integration test already passes against the upstream contract.

---

# 13. Implementation AI operating instructions

The implementation AI must follow this exact operating contract.

1. Read `virality_shorts_plan_v5_0.md` and this file before changing code.
2. Do not consult legacy v4.x plans, audits, cached prompt text, generated schema files, old implementation plans, or external architecture suggestions as sources of product behavior.
3. Treat `virality_shorts_plan_v5_0.md` as the authority for product behavior and this file as the authority for technology, implementation order and tests.
4. Never invent a missing constant. If a value is normative, load it from the config registry. If it is not specified by either source file, stop with `BLOCKED_BY_DEPENDENCY_OR_SPEC_GAP` and report the exact missing decision rather than guessing.
5. Never invent a prompt. Copy prompts verbatim from the v5.0 plan into versioned prompt artifacts.
6. Never invent a schema field name when the product plan defines the artifact. Implement the exact v5.0 field names and enum values.
7. Never change a stage's producer/consumer authority. In particular: verified edit plan owns content/timing/joins; reframe plan owns composition; caption plan owns caption timing; render profile owns export format.
8. Never compute event timestamps outside `event_safe_cut_v1` and its two resolvers.
9. Never substitute coarse ASR timestamps for forced-aligned word timing in transcript-bearing MVP jobs.
10. Never substitute zero for unavailable speaker/visual evidence when the v5.0 contract says `null` + a missing reason.
11. Never send pre-region context to the semantic verifier or deleted transcript text to the judge.
12. Never automatically repair a user-authored content edit.
13. Never let study-mode plans or sealed evaluation data leak into production ranking/training.
14. Never let a transport failure masquerade as invalid semantic output or a neutral score.
15. Every behavior-producing artifact must persist config/version/model/prompt provenance required by the source contracts.
16. Every phase must add and pass its exact unit tests plus its next-phase integration test before moving on.
17. When a test discovers a contradiction between implementation and v5.0, change the implementation to the v5.0 contract. Do not alter behavior merely to make a failing test green.
18. Do not replace a dependency/model/provider because another implementation is easier. Use `BLOCKED_BY_DEPENDENCY` and document the exact failure.
19. Before marking MVP complete, run the full static checks, unit suite, contract suite, integration suite, fixture e2e suite, evaluation harness tests, and deployment promotion checklists in this file.
20. The final repository must contain enough generated schemas, prompts, configs, migrations and fixtures produced from the two source-of-truth documents that a clean clone can build and run the complete D0 test pipeline without any third specification file.



# 14. Final technology decision record

There are no alternative technologies for the MVP implementation. The following is the final development/production split.

| Area | D0 Local Core | D1 Hybrid Staging | D2 Controlled Beta | P0 Paid Production |
|---|---|---|---|---|
| Frontend | local Next.js | Vercel Hobby/preview | Vercel Hobby/preview | Vercel Pro |
| API | local FastAPI | Railway | Railway | Railway Hobby |
| PostgreSQL | local Docker | Railway PostgreSQL | Railway PostgreSQL | Railway PostgreSQL |
| Redis | local Docker | Railway Redis | Railway Redis | Railway Redis |
| CPU worker | local | Railway | Railway | Railway |
| GPU worker | RX 7800 XT | RX 7800 XT | RX 7800 XT | Modal L4 |
| Render worker | local | Railway | Railway | Railway |
| Beat/scheduler | embedded in worker-cpu | embedded in local worker-cpu | embedded in local worker-cpu | embedded in Railway worker-cpu |
| Object storage | local filesystem adapter for unit tests | Cloudflare R2 staging | Cloudflare R2 staging | Cloudflare R2 production |
| Runtime LLM | deterministic mock | Kimi K3 / DeepSeek V4 Pro, capped | Kimi K3 / DeepSeek V4 Pro, capped | Kimi K3 / DeepSeek V4 Pro |
| IaC/config | repository config + Docker Compose | Railway + R2 + Modal deployment config | same as D1 | same as D1 + production secrets |
| CI | GitHub Actions | GitHub Actions | GitHub Actions | GitHub Actions |
| Error tracking | Sentry local/dev | Sentry | Sentry | Sentry |

## 14.1 Fixed product runtime models

```text
content_style_v1 -> kimi-k3
hook_analysis_v1  -> kimi-k3
semantic_verifier -> deepseek-v4-pro
```

No automatic model fallback exists.

## 14.2 Fixed implementation-agent usage

Kimi K3 and DeepSeek V4 Pro are the approved coding agents for implementing this plan. An implementation agent must use the current phase's tests and contracts as the authority and must not replace a technology because it prefers another stack.

## 14.3 Fixed production upgrade trigger for Railway

Start P0 on Railway Hobby.

Upgrade Railway to Pro only when at least one of the following measured conditions becomes true for two consecutive weekly measurements:

```text
Railway compute usage exceeds the Hobby included credit
OR
sustained workload requires more than the Hobby resource envelope
OR
production reliability requirements cannot be met on Hobby
```

The upgrade is an operational action, not an application architecture change.

## 14.4 Fixed production GPU rule

P0 uses Modal L4 from the beginning of public production.

D0/D1/D2 never require paid cloud GPU execution.

The local RX 7800 XT remains the canonical development/beta GPU and is retained as a regression/smoke-test environment after production launch.

## 14.5 Fixed production storage rule

R2 is used for production source videos, immutable artifacts and final renders.

Local files are never used as production persistent storage.

# 15. Development-to-production execution checklist

This section is mandatory. An implementation AI must not move a component to the next hosting mode without the corresponding checklist passing.

## 15.1 D0 checklist

Required:

```text
[ ] Docker Compose starts PostgreSQL and Redis
[ ] API health check passes
[ ] Celery health check passes
[ ] RX 7800 XT ROCm smoke test passes
[ ] GPU provider health is recorded
[ ] Local fixture upload adapter works
[ ] Local normalization works
[ ] ASR/timing artifacts can be produced
[ ] Structural analysis works
[ ] Candidate discovery works
[ ] Edit planning works
[ ] Verification works
[ ] Reframe works
[ ] Tier 2 works
[ ] Review UI works
[ ] Rendering works
[ ] Required unit tests pass
```

D0 exit condition: `IT-4-5` and all prior phase gates pass.

## 15.2 D1 checklist

Required:

```text
[ ] Vercel preview deployment works
[ ] Railway API deployment works
[ ] Railway PostgreSQL migrations work
[ ] Railway Redis connectivity works
[ ] R2 presigned upload works
[ ] Browser -> R2 -> API upload path works
[ ] Hosted API -> queue -> local GPU worker path works
[ ] Local GPU worker uses outbound-only connectivity
[ ] Hosted artifacts are readable through signed URLs only
[ ] Staging secrets are isolated from local and production secrets
[ ] End-to-end hosted fixture job passes
```

D1 exit condition: all Phases 0–13 gates pass locally, then the D1 parity/hosted integration suite passes for the same commit and schemas.

## 15.3 D2 checklist

Required:

```text
[ ] allowlist authentication enabled
[ ] beta quotas enforced
[ ] production publication disabled
[ ] upload validation tested with malformed files
[ ] authorization tested across users
[ ] rate limiting tested under burst traffic
[ ] job cancellation tested
[ ] restart recovery tested
[ ] external LLM failures tested
[ ] GPU worker offline behavior tested
[ ] storage cleanup tested
[ ] user-edit verification path tested
[ ] at least one complete beta regression cycle passes
```

D2 exit condition: security/reliability/user-acceptance gate passes and Phase 14/15 data collection can run without violating lineage or privacy rules.

## 15.4 P0 promotion checklist

The implementation team must explicitly record:

```text
[ ] Phase 18 security tests pass
[ ] Phase 18 failure-injection test passes
[ ] Production environment variables are present
[ ] Production R2 buckets are separate from staging
[ ] Production database is separate from staging
[ ] Production Redis is separate from staging
[ ] Production LLM keys are separate from staging keys
[ ] Modal production app is deployed
[ ] Modal production smoke test passes
[ ] Vercel production deployment passes
[ ] Railway production deployment passes
[ ] Backup/restore drill passes
[ ] Data deletion drill passes
[ ] Rate limits are enabled
[ ] Cost ceilings/alerts are enabled
[ ] User-facing privacy/data-retention policy is present
[ ] No test fixture or staging secret is reachable from production
```

P0 production is not approved until every checkbox is satisfied.

# 16. External technology verification record

The implementation choices in this file were checked against current vendor documentation on 2026-09-21.

### Vercel

The Vercel Hobby plan is free but restricted to personal/non-commercial use; Vercel Pro is the production plan for professional developers, freelancers and businesses. The plan therefore uses Hobby for development and Pro only for commercial production.

### Railway

Railway's current trial provides a one-time $5 grant for up to 30 days. Trial resources are limited, so this file uses the trial only for D1/D2 staging and explicitly avoids treating it as permanent production hosting. Railway's current Free plan provides $1/month in included credit; Railway Hobby is the fixed initial production plan at $5/month plus usage above included credit.

### Cloudflare R2

R2 provides an S3-compatible API and presigned URLs for temporary object access. This is why browser uploads bypass the API and go directly to R2 using short-lived signed URLs.

### AMD ROCm

AMD's current ROCm documentation lists the Radeon RX 7800 XT (RDNA3, gfx1101) as supported for compute workloads in the current ROCm support documentation. The implementation therefore fixes Ubuntu 24.04 LTS + ROCm 7.2.2 for the local GPU worker and requires an actual smoke test before any GPU model integration is accepted.

### Kimi K3

Kimi's official API documentation describes `kimi-k3`, supports structured output/function calling and documents OpenAI-compatible API integration. Kimi Open Platform API billing is separate from Kimi Code/Membership billing. The implementation therefore treats coding-agent access and product runtime API access as separate credentials/configurations.

### DeepSeek V4 Pro

DeepSeek's official API documentation lists `deepseek-v4-pro` and supports structured JSON/schema output. The product runtime adapter therefore uses the OpenAI-compatible protocol and performs an additional canonical-schema validation before business logic consumes the output.

# 17. Final implementation invariant

The system is implemented as a sequence of versioned, immutable, test-gated artifacts rather than one monolithic video-processing job.

The invariant is:

```text
raw source
→ normalized media
→ analysis artifacts
→ candidate regions
→ qualified regions
→ Tier 1
→ style
→ constrained edit plans
→ verified edit plans
→ hooks
→ reframe
→ Short Candidates
→ Tier 2
→ review
→ render
→ outcome
```

Every arrow has:

```text
one producer
one canonical schema
one artifact lineage boundary
one next-phase integration test
one explicit failure taxonomy
```

Deployment is a separate concern:

```text
D0 Local Core
      ↓
D1 Hybrid Staging
      ↓
D2 Controlled Beta
      ↓
P0 Paid Production
```

The application behavior does not change when crossing these deployment boundaries. Only the infrastructure provider for the same logical capability changes.

There is no implicit product, algorithm, schema, constant, prompt, lifecycle or evaluation design work left for the implementation agent.
