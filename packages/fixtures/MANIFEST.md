# packages/fixtures — Phase 0.9 committed fixtures

Impl plan 0.9: "Create the committed synthetic fixtures already specified and expected
probe/transcript/boundary snapshots." This directory covers the 10 listed scenarios.

## Media fixtures (`media/`)

All 5 are synthesized **entirely offline** with `ffmpeg`'s built-in `flite` filter (libflite,
no network call, no external TTS API) for speech, and `ffmpeg lavfi` color/noise sources for
everything else. Every fixture is deterministic (fixed text, fixed filter graphs, no
wall-clock metadata: `-map_metadata -1`) and small (704 KB total for all 5). Each `.mp4` has a
matching `<name>.ground_truth.json` recording the exact spoken text, word count, speaker
count/turns, and (for the event fixture) exact onset/settle timestamps — since the text and
timing were authored, not transcribed, this is genuine ground truth, not a guess.

Exact regeneration commands are in `scripts/generate_media_fixtures.sh` (idempotent; reruns
produce byte-different-but-spec-equivalent output because encoder timestamps aren't fully
deterministic across ffmpeg runs — the properties recorded in the ground-truth files, not
byte-identity, are the durable contract).

| File | Task 0.9 item | Duration | Notes |
|---|---|---:|---|
| `fixture_speech_45s.mp4` | speech-led >= 25 words | 46.7s | 144 words, 1 speaker (also the named input for Phase 0.10's thin vertical slice) |
| `fixture_speech_lt25words.mp4` | speech-led < 25 words | 5.1s | 16 words, 1 speaker — below `JUDGE_MIN_WORDS` |
| `fixture_event_6_8s.mp4` | 6–8s event-led candidate | 7.0s | quiet -> onset burst at t=2.0s -> settle at t=2.3s |
| `fixture_multi_speaker.mp4` | multi-speaker reframe | 19.4s | 2 speakers (distinct flite voices), 4 turns, 0.6s gaps |
| `fixture_screen_content.mp4` | screen-content reframe | 11.3s | white quadrilateral sized inside the Phase 4 `screen_content_v1` acceptance bounds |

**Known limitation (documented, not hidden):** the visual tracks are synthetic (solid colors,
drawtext labels, a drawn rectangle) — none contain a real human face. They are valid inputs for
audio/speech/duration/event-timing testing but must NOT be used as positive fixtures for real
face-detection accuracy without regenerating with real footage. This is recorded in each
`ground_truth.json`'s `caveats` field, not just here.

## Scenario fixtures (`scenarios/`)

The remaining 5 task-0.9 items are not media — they are config/request/mock-response shapes,
so they are committed as JSON instead of manufacturing a video that wouldn't actually exercise
anything:

| File | Task 0.9 item |
|---|---|
| `no_diarization_path.json` | no-diarization path (exercises `speaker_id_v1`/`speaker_dependent_feature_v1`, Phase 0.7) |
| `llm_transport_error_path.json` | transport-error LLM path (impl plan §2.4) |
| `llm_invalid_output_path.json` | invalid-output LLM path, with one concrete violation per `validate_judge_semantics@1` / `validate_hook_semantics@1` rule |
| `study_ratio_generation.json` | study-ratio generation (v5.0 2.36.8.7/2.36.9.9) |
| `user_edit_rejection.json` | user-edit rejection (v5.0 2.26.1 terminal `BLOCKED_USER_EDIT` semantics) |

These are **not** yet validated against real stage code (there is no MOCK_LLM provider, edit
planner, or verifier to run them through — those are Phase 7/8/9). They are committed now, in
the exact shape those future stages' contracts already specify, so Phase 7/8/9 tests consume
them rather than re-inventing scenario data mid-phase.

## What "expected probe/transcript/boundary snapshots" (impl plan 0.9) does NOT include yet

Word-level timestamps, sentence boundaries, and boundary-map events are Phase 3/4/5 *output*,
computed by running the real ASR/alignment/discovery pipeline against these fixtures — none of
that pipeline exists yet. Fabricating those snapshots now would mean guessing at real ASR/
alignment behavior (word confidence, exact timestamp jitter, sentence-split points on real
audio) instead of computing it, which is exactly what impl plan 2.3/Q-05-style guidance warns
against for the deterministic primitives. `sentence_seg_v1` and `TextTiling_depth_v1`
themselves are already fully unit-tested against synthetic word/embedding inputs
(`tests/unit/test_phase0_analysis_primitives.py`) — that is the Phase 0.7 contract; running
them against these fixtures' *real* ASR output is Phase 3/4/5's job, once that code exists.
