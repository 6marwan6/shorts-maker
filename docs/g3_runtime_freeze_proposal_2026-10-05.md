# SUPERSEDED 2026-10-06 -- see 'G3 freeze applied' below. Kept as the evidence trail.

# G3 runtime-contract freeze -- PROPOSAL received 2026-10-05 (NOT applied)

`config@1` `runtime_contracts` stay `BLOCKED_BY_SPEC`. The proposal was checked against the locked
environment (`uv.lock`) and the pinned library sources. Findings below; each blocker needs an owner
decision before `asr_runtime@1` / `alignment_runtime@1` / `diarization_runtime@1` can be FROZEN.

## Proposed values (as received)
asr: whisperx 3.8.4 (095b36b), faster-whisper 1.2.1, ctranslate2 4.8.0 (ROCm 7.2.x), model
openai/whisper-large-v3-turbo @ 41f01f3fe87f28c78e2fbf8b568835947dd65ed9, device cuda:0, float16,
batch 8, task transcribe, language en, beam 5, patience 1.0, length_penalty 1.0, temperature [0.0],
best_of 5, condition_on_previous_text false, compression 2.4, logprob -1.0, no_speech 0.6,
suppress_tokens [-1], suppress_blank, without_timestamps, word_timestamps true,
max_initial_timestamp 0.0, VAD silero v6 (chunk 30, onset 0.5, offset 0.363).
alignment: whisperx 3.8.4, WAV2VEC2_ASR_BASE_960H (torchaudio 2.8.0), 16 kHz,
interpolate_unaligned_words false.
diarization: pyannote.audio 4.0.0, community-1 (revision + snapshot sha256 BLOCKED), 16 kHz mono,
no speaker-count hints, first-appearance speaker ids.
fastText: lid.176.ftz sha256 8f3472cf...3e83 (sidecar written; model file not provisioned).

## Verified against the repo lock and library sources
| # | Finding | Evidence |
|---|---|---|
| 1 | Versions differ from the lock: whisperx 3.8.4 vs **3.8.6**, ctranslate2 4.8.0 vs **4.8.2**, pyannote-audio 4.0.0 vs **4.0.7** (faster-whisper 1.2.1 and torchaudio 2.8.0 match). | `uv.lock` |
| 2 | Re-locking to the proposed versions resolves, but forces collateral downgrades of unrelated packages: protobuf 7.36 -> 5.29 (major), opentelemetry-* 1.44 -> 1.34, torchvision removed. | `uv lock` in a scratch copy |
| 3 | **No ROCm CTranslate2 on PyPI.** The ctranslate2 4.8.0 wheel contains CPU + CUDA libs and no HIP symbols; `gpu_backend: rocm` needs a different build that is not in the lock. On the RX 7800 XT the locked wheel cannot do `device: cuda`. | wheel inspection |
| 4 | **Silero VAD is not the packaged v6 model.** whisperx 3.8.4 `vads/silero.py` calls `torch.hub.load('snakers4/silero-vad', 'silero_vad', onnx=False, trust_repo=True)`: a runtime GitHub download of an unpinned repo head. It does not use faster-whisper's bundled `silero_vad_v6.onnx`. This breaks the impl plan's "workers must never download an unpinned alias" rule, and `offset 0.363` is unused by that class. | whisperx source |
| 5 | **Model repo mismatch.** faster-whisper maps `large-v3-turbo` to `mobiuslabsgmbh/faster-whisper-large-v3-turbo` (a CTranslate2 conversion). `openai/whisper-large-v3-turbo` is a transformers checkpoint faster-whisper cannot load directly; using it needs a pinned CT2 conversion step (converter version + quantization) that the contract does not define. | faster-whisper 1.2.1 `utils.py` |
| 6 | **`language: en` at ASR defeats the language gate.** The gate (v5.0 2.14) runs fastText on ASR text; forcing English decoding turns foreign speech into English-looking text that passes. | v5.0 2.14 |
| 7 | **`interpolate_unaligned_words: false` is not achievable by calling `whisperx.align()`.** It always interpolates timestamps for words with no alignable characters (hard-coded block, `alignment.py` ~L365-374; `interpolate_method` only picks the method). Interpolated words can be recognised afterwards because genuinely aligned words carry a `score` and unaligned ones do not. | whisperx source |
| 8 | Alignment weights are downloaded at runtime by torchaudio (`get_model(dl_kwargs=...)`) without a checksum. The contract gives no revision/sha256 for the alignment checkpoint or the VAD, which `required_fields` demands. | whisperx source |
| 9 | Key names differ from the library: `temperature` -> `temperatures`; `temperature_increment_on_fallback` is not a valid option (would raise `TypeError`); `word_timestamps` is inert in the batched pipeline (word timing comes from alignment). Mechanical mapping only. | whisperx `asr.py` |
| 10 | Diarization `revision` / `snapshot_sha256` are BLOCKED (acknowledged in the proposal). `exclusive_diarization` as a pipeline parameter is unverified. | -- |

Not verifiable here (no Hugging Face / GitHub access): the model commit hash `41f01f3...`, the
whisperx git revision `095b36b`, the fastText hash.
