# fastText language-ID artifact (owner decision G8, 2026-09-30)

`lid.176.ftz` is an immutable, vendored model artifact. It is **never downloaded at runtime**.
Provision it here together with a sidecar `lid.176.ftz.sha256` containing the file's SHA-256
(64 lowercase hex chars, optionally followed by whitespace/filename). The loader
(`workers/cpu/language_gate.py::FastTextLanguageID`) verifies the file against the sidecar and
refuses to run (BLOCKED_BY_DEPENDENCY) if either file is missing or the hash differs.

The `.ftz` binary is not committed by the implementation agent: the sandbox cannot reach the
fastText distribution host and the exact hash must come from the owner's provisioned copy.

## Status 2026-10-05
`lid.176.ftz.sha256` is now committed with the owner-supplied expected hash
`8f3472cfe8738a7b6099e8e999c3cbfae0dcd15696aac7d7738a8039db603e83` (supplied by the owner, NOT
independently verified by the implementer -- the sandbox cannot reach the fastText host). If the real
file does not match, the loader refuses it (`language_id_model_checksum_mismatch`); the checksum
check is not weakened. `lid.176.ftz` itself is still NOT provisioned: place the official file at
`models/fasttext/lid.176.ftz`. Until then the build stays BLOCKED_BY_DEPENDENCY.
