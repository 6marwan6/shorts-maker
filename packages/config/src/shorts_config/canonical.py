"""Canonical JSON + hashing: canonical_json@1 (owner decision, 2026-09-23).

Contract (fixed, not a per-developer library default):
  - object keys: sorted (Python default string/codepoint order)
  - encoding: UTF-8
  - whitespace: compact separators, no incidental formatting -- (",", ":")
  - unicode: kept as literal UTF-8 (ensure_ascii=False), not \\uXXXX-escaped
  - numbers: Python's json module default float/int repr. Owner decision (2026-09-23) gave
    this exact contract directly rather than adopting JCS/RFC 8785 (which the methodology
    request had raised for evaluation) -- so JCS is not in use here, by decision, not by omission.
  - NaN / Infinity: rejected (allow_nan=False) -- a config hash must be exactly reproducible
  - arrays: order preserved (no reordering is performed)
  - hash input: the exact returned bytes, never an in-memory object

This is the sole permitted config/artifact-identity serializer. Do not independently
JSON-serialize a config or identity object elsewhere for hashing purposes.

NOTE: no TypeScript `canonical_json` implementation exists yet. The frontend itself IS now
scaffolded (impl plan 0.3, apps/web) and packages/schemas/typescript generates TS *types* from
these same JSON Schemas -- but a TS port of this specific serializer (for any future
client-side hashing/identity need) is a separate, still-open piece of work. Cross-language
fixture tests (same bytes, same hash, in both languages) are pending until that exists; see
tests/unit/test_phase0_canonical_json_v1.py for the fixtures a TS implementation must match.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

CANONICAL_JSON_VERSION = "canonical_json@1"


def canonical_json(obj: Any) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
