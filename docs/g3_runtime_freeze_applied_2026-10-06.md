# G3 freeze applied -- 2026-10-06

The owner's 2026-10-06 values supersede the 2026-10-05 proposal and are now `FROZEN` in `config@1`
`runtime_contracts` (asr_runtime@1, alignment_runtime@1, diarization_runtime@1). Software versions equal
the locked environment (checked by a test). Every previously reported blocker is resolved by the
decisions: lock versions kept; ASR on CPU int8; vendored Silero v6 (no torch.hub); the CT2 repo
`mobiuslabsgmbh/faster-whisper-large-v3-turbo`; `language: null`; `interpolate_method="ignore"` plus the
wildcard guard.

## What was built (not yet run against real models)
`workers/gpu/real_backends.py` (WhisperX ASR + vendored-Silero VAD wrapper, HF-CTC aligner, pyannote
diarizer), `workers/gpu/model_materialization.py` (offline verification of every artifact),
`scripts/materialize_models.py` (provisioning tool, needs network + HF token),
`models/silero/silero_vad_v6.onnx` (vendored; the exact file inside the faster-whisper 1.2.1 wheel,
SHA-256 = owner value), `tests/real_models/test_phase3_real_smoke.py` (the 10 acceptance points),
`packages/fixtures/media/fixture_speech_non_english_fr.mp4` (synthetic eSpeak French).

## Still needed before `make smoke-real` can run
1. `make materialize-models` (network + `HF_TOKEN` accepted for pyannote) -> models/whisper, alignment, diarization.
2. `models/fasttext/lid.176.ftz` (sidecar hash already committed).
3. NLTK `punkt_tab` (english) under `models/nltk_data/` -- needed by `whisperx.align()`; see open items.
4. A ROCm build of PyTorch for the RX 7800 XT (alignment + diarization use `cuda:0`); the lock's torch 2.8.0 is the PyPI build.

## Open items needing the owner (none block the code; all affect the real gate)
- Unlisted whisperx 3.8.6 defaults (best_of, suppress_tokens, suppress_blank, without_timestamps, ...) are
  inherited, which G3 forbids; they are recorded in config@1 as `observed_library_defaults_not_owner_specified`.
- `whisperx.align()` needs NLTK punkt_tab and otherwise downloads it at runtime; the contract pins no identity.
- Alignment device `cuda:0` comes from the freeze message's section 4, not the alignment block.
- Wildcard rule: a word is untimed only when EVERY character is outside the alignment dictionary
  ("$50", "2026", "..."); mixed words ("2nd", "U.S.") keep whisperx timing even though an edge character
  may be wildcard-derived.
- `resolved_repository: dropbox-dash/...` is recorded but unused; the provisioning script fetches `model_id`.
