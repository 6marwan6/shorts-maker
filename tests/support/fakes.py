"""Deterministic test doubles for Phase 4 (synthetic only -- never presented as real upstream output)."""
from __future__ import annotations

import hashlib

import numpy as np
from workers.cpu.embeddings import DIM, Encoded


class FakeEncoder:
    """Hash-seeded unit vectors. Stands in for the real CPU/fp32 bge encoder, which cannot run in the
    dev sandbox (no model files, no network). Token counts are whitespace-word counts + 2 specials."""
    def __init__(self, max_seq: int = 512, nondeterministic: bool = False):
        self.max_seq, self.nondeterministic, self.calls = max_seq, nondeterministic, 0

    def encode_one(self, text: str) -> Encoded:
        self.calls += 1
        seed = int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")
        if self.nondeterministic:
            seed += self.calls
        v = np.random.default_rng(seed).standard_normal(DIM).astype(np.float32)
        v = (v / np.linalg.norm(v)).astype(np.float32)
        orig = len(text.split()) + 2
        return Encoded(v, orig, min(orig, self.max_seq))

    def backend_versions(self) -> dict[str, str]:
        return {"fake": "0"}
