# Cross-phase implementation constraints (tracked so they survive to the phase that needs them)

These are correctness rules named explicitly in owner decisions but not yet enforceable by any
test, because the code that could violate them doesn't exist yet. Recorded here per decision 6
(2026-09-23) so they aren't lost between now and the phase that implements them.

## `context_dependency` vs `opening_standalone` (v5.0 2.9.3)

Two distinct signals, never merged into one feature:
- `context_dependency`: deterministic, pre-edit transcript heuristic (2.9.3's `R`/`C`/`P`
  formula) — used by QC-2 (qualification) and opening selection (2.36.8.5).
- `opening_standalone`: post-edit LLM verifier score (2.36.9.3) — what Tier 2 hook group B
  (`hook.requires_prior_context`) consumes.

**Enforce when:** Phase 5 (qualification/opening selection) and Phase 9 (hook analysis) are
implemented. A future test should assert these are computed by different functions, stored under
different field names, and that Tier 2's hook term (2.39.4) never reads `context_dependency`.

## Tier 2 coherence must not be divided by 5 twice (v5.0 C-10 / 2.39.3–2.39.4)

The verifier's raw scores are integers 1–5. `coh.flow`, `coh.reference_resolution`, etc. in the
Tier 2 feature vector (2.39.3) are already normalized to `score/5 ∈ [0,1]` at the point they're
stored. The heuristic ranker's `coherence_term = 0.5·coh.min + 0.5·coh.mean` (2.39.4) must consume
those already-normalized [0,1] values directly — never divide by 5 again.

**Enforce when:** Phase 9 (hook/verifier feature reuse) and Phase 11 (Tier 2 heuristic ranker) are
implemented. A future test should feed a known raw verifier score (e.g. all 5s) through both
stages and assert the final `coherence_term` is `1.0`, not `0.2`.

## Phase 15 pre-requisite gate: EvaluationReport / CalibrationReport / AdoptionDecision field contracts

**Owner decision, 2026-09-23 (final).** `evaluation_report_v1`, `calibration_report_v1`, and
`adoption_decision_v1` (impl plan Phase 15.6) have zero field-level definition anywhere in v5.0
or the implementation plan — only artifact names and one sentence ("split IDs/hashes, config
identity and dataset sampling metadata"). Their JSON Schemas were deliberately **not**
implemented in Phase 0, to avoid inventing fields neither source document specifies.

**This is a hard gate on Phase 15, not a note to work around:** before implementing these three
schemas (or any code that reads/writes them), their field-level contracts must be **explicitly
defined by owner decision** — not inferred from whatever Phase 15's evaluation/calibration/
adoption-pipeline implementation happens to produce along the way. Defining the schema as an
afterthought of the pipeline code would silently turn "the spec is authoritative" into "the
implementation is authoritative," which is exactly backwards per this repo's standing rule.

**Scope of the block:** Phase 15 evaluation reporting, calibration reporting, and the T2-A1/H-G5
adoption-decision record only. No other phase reads or writes these three artifacts (confirmed by
the Phase 0 audit — see README), so this blocks nothing before Phase 15 is reached.

**What "explicitly defined" means in practice:** at minimum, for each of the three, a field
inventory (name, type, required/optional), and confirmation of whether the standard artifact
identity envelope (`schema_version`, `stage_version`, `config_version`, `config_sha256`) applies
to them the way it does to every other behavior-producing artifact. `BoundaryMap`, `EditUnit`, and
`super_unit` (implemented in Phase 0) are the model for what "grounded enough to implement"
actually looks like — a real field list or literal JSON example, not a one-sentence description.

## Phase 2 pre-requisite gate: `media_manifest_v1` field contract, CFR predicate, silent-source WAV semantics — opened 2026-09-29

**Owner decision, 2026-09-29 (blocking, per the standing rule — not resolved unilaterally).**
Three genuine gaps surfaced while building normalization (impl plan Phase 2):

1. **`media_manifest.json` has no field-level schema anywhere.** The implementation plan gives
   only a prose field list (duration, width, height, fps, video codec, audio codec, sample rate,
   channels, rotation, checksums) — not types, required/optional, nullability, or fps
   representation (a plain number vs. a rational `{num, den}`, which matters for deterministic
   media behavior). `NORMALIZING` does **not** write this artifact; `test_normalized_manifest_schema`
   (named explicitly in the impl plan's Phase 2 unit test list) is **not implemented**.
2. **CFR (constant frame rate) has no normative predicate.** "Preserve source FPS only when CFR"
   (§2.2) is unimplementable without one. `r_frame_rate == avg_frame_rate` was proposed and
   explicitly rejected (stream-rate metadata equality is not a timestamp-spacing guarantee).
   `select_normalized_fps` in `workers/cpu/normalization.py` always returns 30 until an owner
   defines: authoritative ffprobe fields, timestamp tolerance, VFR treatment, 29.97/59.94
   treatment, and whether `{24,25,30,50,60}` means exact integer rates only or accepted nominals.
3. **Silent-source `analysis_audio.wav` semantics are unconfirmed.** No-audio sources are
   *supported* (confirmed — not rejected as `PERMANENT_INPUT`, since v5.0's zero-speech/event-led
   path must stay reachable), but whether the pipeline should synthesize a zero-filled WAV (so
   Phase 4's RMS/silence machinery has something deterministic to operate on) or leave the
   artifact genuinely absent is still open. `build_analysis_audio_command` raises `BlockedBySpec`
   if called for a no-audio source, so this can't be silently papered over by a later phase.

**Scope of the block:** these three only. Everything else in Phase 2 (probing, validation,
normalization command construction, artifact persistence, the dispatch/idempotency boundary) is
implemented and tested independent of these gaps.

## BoundaryMap container schema — resolved 2026-09-27

**Owner decision:** defer to Phase 5, as originally recommended. The per-event shape
(`boundary_event.schema.json`) is implemented and unaffected. The container wrapper (id field
name, the array key for the event list, whether it's persisted as a standalone artifact vs. an
in-memory structure passed between discovery steps) is defined when Phase 5 actually implements
discovery and the real consumption pattern settles the ambiguity, rather than guessing now.

**Enforce when:** Phase 5. Do not invent `{boundary_map_id, source_video_id, events: [...]}`
(the inference floated in the original Phase 0 note) without checking it against how 2.36.6
Step 1 actually threads the boundary map through the discovery algorithm first.

## Thin vertical slice (impl plan Phase 0.10) — harness plan, not a completion

**Status:** genuinely could not be run in Phase 0 (2026-09-27). Impl plan 0.10 asks to execute
normalize → ASR/alignment → analysis → discovery → one qualified region → one verified edit
plan → reframe → captions → render as one deterministic path. Every one of those stages except
"normalize" is Phase 2 through Phase 10's actual algorithm — none exist yet in Phase 0/1. There
is no way to "run" this slice without either faking those algorithms (which would misrepresent
what Phase 0 actually verified) or waiting until the real code exists.

**What to do instead, phase by phase — the actual completion plan:**

| After this phase lands | The slice should be extended to include |
|---|---|
| Phase 2 (normalization) | normalize `packages/fixtures/media/fixture_speech_45s.mp4`, assert the manifest matches its `.ground_truth.json` duration |
| Phase 3 (ASR/alignment) | + real ASR/forced-alignment on the normalized output, sanity-check word count is in the neighborhood of the fixture's known 144 words (exact match not expected — ASR isn't perfect, that's fine; the fixture's `exact_transcript` is for grading closeness, not exact-match assertion) |
| Phase 4 (analysis) | + structural profile / boundary map / embeddings on the real ASR output |
| Phase 5 (discovery) | + one qualified Source Region discovered from the fixture (this is also where the BoundaryMap container schema above gets defined) |
| Phase 6 (Tier 1 + style) | + Tier 1 score + content_style for that region |
| Phase 7 (edit planning) | + one Edit Plan for the region |
| Phase 8 (verification) | + one `verified_edit_plan` |
| Phase 9 (hook analysis) | + hook_analysis_v1 on the verified plan |
| Phase 10 (reframe/captions) | + `reframe_plan_v1` + `caption_plan_v1` — **at this point the full slice from the original 0.10 text is actually complete**; write it as one committed integration test (`tests/integration/test_thin_vertical_slice.py`) rather than leaving it as a checklist item, and only then treat 0.10 as done in the literal sense |

**Do not** implement a stubbed/faked version of any stage above merely to produce a green
checkmark on 0.10 before its real phase lands — that would hide exactly the kind of gap this
constraints file exists to keep visible.


## Phase 3 gates — opened 2026-09-30

| Item | Status | Needed from owner |
|---|---|---|
| `asr_runtime@1` / `alignment_runtime@1` values (model id+revision+sha, VAD, beam, temperature, condition_on_previous_text, compute_type, device, batch, chunk/window, language, timestamps) | BLOCKED_BY_SPEC (G3) | frozen values in config@1 `runtime_contracts`, then the WhisperX adapter |
| `diarization_runtime@1` (revision/sha/device) | BLOCKED_BY_SPEC (plan pins only the id) | frozen values |
| fastText vs numpy>=2 | BLOCKED_BY_DEPENDENCY | pick a fix; do not substitute another LID model |
| `lid.176.ftz` + sha256 sidecar | BLOCKED_BY_DEPENDENCY | provision under `models/fasttext/` |
| Tests that need real models: ASR word-timestamp sanity on `fixture_speech_45s.mp4`, ROCm smoke, real forced alignment/diarization, `test_model_manifest_recorded` against real revisions | NOT RUN | run on the RX 7800 XT after G3 |
| Interpretations (1)-(9) in the README 2026-09-30 log | implemented, unconfirmed | confirm or amend |

**Resolved by G6 (2026-09-30):** the Phase 2 "silent-source analysis_audio.wav" question. No audio
stream -> no WAV, `analysis_audio_status = not_applicable`. `media_manifest_v1` and the CFR
predicate remain open.

**Phase 7 heads-up:** `sentence_seg_v1` already splits every sentence to <= 15 s, so the run-on guard of
v5.0 2.36.8.2 (split >15 s units at gaps >= 500 ms) can never fire. Needs an owner ruling before Phase 7.


## Phase 3 gates -- update 2026-10-02

| Item | Status |
|---|---|
| `media_manifest_v1`, PTS-based CFR predicate | RESOLVED and implemented (owner #12, #13) |
| Interpretations (1)-(5), (7)-(9) of the 2026-09-30 log | RESOLVED by owner decisions #1-#9 |
| numpy == 1.26.4 pin | CONTRADICTION: unsatisfiable with pyannote-audio >= 4 / whisperx (verified with `uv lock`); not applied |
| G3 runtime values, `lid.176.ftz` + sha256 | still BLOCKED (see above) |
| Phase 7 run-on guard (#10) | decision recorded; implement + test in Phase 7 |


## Phase 3 exit gate -- status 2026-10-04

| Gate | Status |
|---|---|
| Contract implementation (schemas, state machine, dispatch durability, retention, adapters' interfaces) | COMPLETE -- 348 tests pass |
| Real WhisperX ASR + forced alignment + pyannote diarization | BLOCKED_BY_SPEC: freeze `asr_runtime@1`, `alignment_runtime@1`, `diarization_runtime@1`, then write the adapters |
| fastText language ID (`fasttext_predict_v1` against the real model) | BLOCKED_BY_DEPENDENCY: provision `models/fasttext/lid.176.ftz` + `.sha256` |
| **Exit gate = `make smoke-real` green** | NOT PASSED. Do not mark Phase 3 closed until it is |
| fastText numpy-2 conflict | RESOLVED by owner decision (Option A adapter); numpy 2 stays |


## Phase 3 exit gate -- status 2026-10-06
| Gate | Status |
|---|---|
| asr / alignment / diarization runtime contracts | FROZEN (owner 2026-10-06); adapters written, unverified against real models |
| Model artifacts materialized + hashes verified | NOT DONE: run `make materialize-models` (network + HF_TOKEN) |
| `models/fasttext/lid.176.ftz` | NOT PROVISIONED (sidecar hash committed) |
| NLTK punkt_tab, ROCm PyTorch wheel | NOT PROVISIONED / not in the lock |
| **`make smoke-real` (10 points)** | NOT RUN -- Phase 3 is not closed until it is green |
