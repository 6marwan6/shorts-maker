"""Content-addressed artifact object keys (impl plan §3.1, extended per owner decision
2026-09-28: binary media artifacts use the SAME namespace but keep their real extension).

    artifacts/{source_video_id}/{artifact_type}/{artifact_id}/{artifact_sha256}.{ext}

Phase 3+ must locate media only via artifact ID -> storage_location (Artifact row) -> storage
adapter; never via a hard-coded path (IT-2-3)."""
from __future__ import annotations

import re
import uuid

# artifact_type -> the only extension it may use. JSON schema-backed artifacts default to json.
BINARY_ARTIFACT_EXTENSIONS: dict[str, str] = {
    "normalized_media": "mp4",
    "analysis_audio": "wav",
}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TYPE = re.compile(r"^[a-z][a-z0-9_]*$")


def artifact_storage_key(
    *, source_video_id: uuid.UUID | str, artifact_type: str, artifact_id: uuid.UUID | str,
    sha256: str, extension: str | None = None,
) -> str:
    if not _TYPE.match(artifact_type):
        raise ValueError(f"invalid artifact_type: {artifact_type!r}")
    if not _SHA256.match(sha256):
        raise ValueError("sha256 must be 64 lowercase hex chars")
    expected = BINARY_ARTIFACT_EXTENSIONS.get(artifact_type, "json")
    ext = extension or expected
    if ext != expected:
        raise ValueError(f"artifact_type {artifact_type!r} must use extension {expected!r}, got {ext!r}")
    return f"artifacts/{source_video_id}/{artifact_type}/{artifact_id}/{sha256}.{ext}"


def transport_storage_key(*, source_video_id: uuid.UUID | str, stage: str, sha256: str) -> str:
    """Internal transport-envelope objects (owner 2026-10-02 #6): NOT artifacts, no Artifact row,
    no lineage. Content-addressed so a retried GPU task rewrites byte-identical bytes to the same
    key (idempotent). Descriptors are recorded in stage_runs.execution_metadata."""
    if not _TYPE.match(stage):
        raise ValueError(f"invalid stage: {stage!r}")
    if not _SHA256.match(sha256):
        raise ValueError("sha256 must be 64 lowercase hex chars")
    return f"transport/{source_video_id}/{stage}/{sha256}.json"
