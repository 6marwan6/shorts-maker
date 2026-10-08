# Vendored Silero VAD v6 (owner decision 2026-10-06, G3 asr_runtime@1)
`silero_vad_v6.onnx` is the exact file bundled in the `faster-whisper==1.2.1` wheel
(`faster_whisper/assets/silero_vad_v6.onnx`), extracted by the implementer; its SHA-256
`4cbf549b8326f60f80f2536d9eefeb450a9abe83365a098031c89719f1be17d2` equals the owner-supplied
value. WhisperX's own Silero path (`torch.hub.load('snakers4/silero-vad')`) is NOT used.
The loader re-verifies the hash before every load; a mismatch is BLOCKED_BY_DEPENDENCY (never
a silent replacement).
