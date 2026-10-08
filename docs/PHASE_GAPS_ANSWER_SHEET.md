# Remaining gaps (Phases 0–4) — recommended answers
Reply with "A1 yes, A2 yes, ..." or edit any line. Every item below is something I will NOT decide alone.

## Phase 4 (blocking the rest of Phase 4)
A1  Face detection (blocker). Locked mediapipe 1.0.1 has no `solutions` API / no face model; 0.10.21 has it but needs numpy<2 (conflicts with pyannote's numpy>=2).
    RECOMMEND (option 1): run face detection in a SEPARATE uv environment/process pinned to mediapipe 0.10.21 + numpy 1.26.x, exchanging data through
    files (frame manifest in, JSON out). Keeps decision §5 (model_selection=1) intact and does not touch the main lock. Options 2: Tasks API + pinned short-range model
    (changes decision §5). Option 3: downgrade pyannote/numpy stack (breaks Phase 3 freeze) — not recommended.
A2  Resize: RECOMMEND interpolation = cv2.INTER_AREA; downscale only (frames already <= max dim are NOT upscaled); other dimension = round-half-up, then keep as is;
    face and scene_context streams use native size.
A3  dB epsilon: RECOMMEND 1e-10 (below one 16-bit LSB squared, so silence maps to a finite −200 dB).
A4  Motion probe: RECOMMEND persist the 10 fps probe series in visual_features_v1 (field `motion_probe_samples`) plus both baselines:
    `motion_z_rolling_60s` (used for peaks) and `motion_z_video` (used for vis.motion_mean_z and hook.first_motion_ms). motion_change: null (missing=no_evidence) when either 5 s window is incomplete.
A5  Artifact identity: RECOMMEND confirm — artifact_id/checksum/created_at/storage_location live on the Artifact row, as transcript_v1 does.
A6  pgvector key: RECOMMEND unique (job_id, sentence_id, model_revision) with source_video_id kept as a column; local `vector(384)` SQLAlchemy type; migration does CREATE EXTENSION IF NOT EXISTS vector; no ANN index yet.
A7  scene_context: RECOMMEND keep as a manifest stream only. Phase-4 trigger: RECOMMEND Phase 4 stages are dispatched by the same durable-intent mechanism Phase 3 uses, as soon as the job is ANALYZING and transcript_v1 + analysis audio + normalized video exist.
A8  Readings R1–R15 (README "Implementer's readings"): RECOMMEND confirm all unless you object to a specific one.
A9  IT-4-5 (once A1–A8 are answered): I build it as a pure artifact-contract test per decision §10.

## Phase 3 (carried forward; blocks the real exit gate, not the code)
B1  Provision real models and run `make smoke-real` (see RUN_GUIDE §7). This is the ONLY thing that moves Phase 3 to passed and Phase 4 to END_TO_END_VALIDATED.
B2  NLTK punkt_tab identity: RECOMMEND pin the NLTK data package by sha256 under models/nltk_data/ and verify at load time (no runtime download).
B3  ROCm torch for the RX 7800 XT (alignment/diarization on cuda:0): RECOMMEND install the ROCm 7.2.2 PyTorch wheel in a separate env for worker-gpu and record its version in the runtime contract; confirm with a one-line GPU smoke test first.
B4  Inherited whisperx 3.8.6 defaults not owner-specified (best_of, suppress_tokens, ...): RECOMMEND accept the recorded observed defaults as the frozen values (config key observed_library_defaults_not_owner_specified) so G3's "no inherited defaults" rule is satisfied explicitly.
B5  Wildcard-word rule and `resolved_repository` note: RECOMMEND accept as implemented.

## Phases 1–2 (carried forward)
C1  Re-verify on the real pinned stack (PostgreSQL 18.6, pgvector 0.8.2, Redis 7.1, FFmpeg 9.x): run `make test` on your Docker stack and report failures.
C2  media_manifest field-level details / CFR predicate / silent-source semantics were implemented under earlier owner decisions — RECOMMEND no change unless the real-stack run disagrees.
C3  D1 (hosted Railway/R2) halves of the integration tests: not run by design until D1 promotion.
