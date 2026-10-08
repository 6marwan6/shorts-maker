"""Phase 4 sentence embeddings (owner decision 2026-10-07 s2, embedding_runtime@1).

CPU fp32 only, batch size 1, one intra-op and one inter-op thread, deterministic PyTorch
algorithms, CLS pooling, L2-normalized, 384 dims, no prefix, no download, no backend fallback.
One sentence -> one embedding of exactly sentence.text.

Implementer's readings (flagged): token counts include the special tokens ([CLS]/[SEP]) because
the 512 limit applies to the full model input; input text is used byte-for-byte as stored in
transcript_v1 (no Unicode normalization)."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np
from shorts_config import Config, canonical_json, sha256_bytes

DIM = 384
MAX_SEQ = 512


@dataclass(frozen=True)
class Encoded:
    vector: np.ndarray        # float32, shape (384,), L2-normalized
    original_token_count: int
    embedded_token_count: int


class SentenceEncoder(Protocol):
    def encode_one(self, text: str) -> Encoded: ...
    def backend_versions(self) -> dict[str, str]: ...


class EmbeddingDeterminismError(RuntimeError):
    """Two runs on the same input were not bitwise identical (owner s2: fail, no tolerance)."""


class SentenceTransformersCPUEncoder:
    """Real adapter. Loads ONLY the locally materialized, hash-verified snapshot (local_files_only);
    never touches the network. Exercised by `make smoke-real` on a provisioned machine -- it cannot
    run in the dev sandbox (no model, no network), so it is NOT covered by unit tests."""

    def __init__(self, cfg: Config, model_dir: str):
        import torch
        from sentence_transformers import SentenceTransformer

        c = cfg.runtime_contract("embedding_runtime@1")
        ex = c["execution"]
        torch.set_num_threads(ex["torch_num_threads"])
        torch.set_num_interop_threads(ex["torch_num_interop_threads"])
        torch.use_deterministic_algorithms(ex["deterministic_algorithms"])
        self._torch = torch
        self._model = SentenceTransformer(model_dir, device="cpu", local_files_only=True)
        self._model.max_seq_length = c["tokenizer"]["max_seq_length"]
        self._model.to(torch.float32)
        self._tok = self._model.tokenizer
        self._max = c["tokenizer"]["max_seq_length"]
        self._normalize = c["output"]["normalize"]

    def encode_one(self, text: str) -> Encoded:
        orig = len(self._tok(text, add_special_tokens=True, truncation=False)["input_ids"])
        with self._torch.inference_mode():
            v = self._model.encode([text], batch_size=1, convert_to_numpy=True,
                                   normalize_embeddings=self._normalize, show_progress_bar=False)[0]
        return Encoded(np.asarray(v, dtype=np.float32), orig, min(orig, self._max))

    def backend_versions(self) -> dict[str, str]:
        import sentence_transformers
        import transformers
        return {"sentence_transformers": sentence_transformers.__version__,
                "torch": self._torch.__version__, "transformers": transformers.__version__}


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def assert_bitwise_deterministic(encoder: SentenceEncoder, texts: list[str]) -> None:
    """Run the same inputs twice; any differing bit raises (no tolerance-based determinism)."""
    a = [encoder.encode_one(t).vector.tobytes() for t in texts]
    b = [encoder.encode_one(t).vector.tobytes() for t in texts]
    if a != b:
        raise EmbeddingDeterminismError("embedding runtime is not bitwise deterministic")


def compute_sentence_embeddings(sentences: list[dict[str, Any]], encoder: SentenceEncoder, cfg: Config) -> dict[str, Any]:
    """Content fields of sentence_embeddings_v1. Every transcript sentence is embedded, including
    sentences whose timing is unusable (embedding depends on text only). Validates each vector
    (384 float32, finite, unit norm) and fails closed otherwise."""
    c = cfg.runtime_contract("embedding_runtime@1")
    out, hashes = [], []
    for s in sentences:
        enc = encoder.encode_one(s["text"])
        v = enc.vector
        if v.shape != (DIM,) or v.dtype != np.float32 or not np.isfinite(v).all():
            raise ValueError(f"bad embedding for {s['sentence_id']}: shape {v.shape} dtype {v.dtype}")
        if abs(float(np.linalg.norm(v.astype(np.float64))) - 1.0) > 1e-4:
            raise ValueError(f"embedding for {s['sentence_id']} is not L2-normalized")
        h = text_sha256(s["text"])
        hashes.append(h)
        out.append({"sentence_id": s["sentence_id"], "input_text_sha256": h,
                    "original_token_count": enc.original_token_count,
                    "embedded_token_count": enc.embedded_token_count,
                    "truncated": enc.original_token_count > c["tokenizer"]["max_seq_length"],
                    "embedding": v.astype(np.float64).tolist()})
    return {
        "embedding_model_id": c["model"]["model_id"], "model_revision": c["model"]["revision"],
        "model_sha256": c["model"]["model_sha256"], "tokenizer_revision": c["model"]["revision"],
        "embedding_dimension": DIM, "dtype": "float32", "pooling": c["pooling"]["mode"],
        "normalized": c["output"]["normalize"], "max_seq_length": c["tokenizer"]["max_seq_length"],
        "backend": c["backend"]["library"], "batch_size": c["execution"]["batch_size"],
        "runtime_sha256": cfg.runtime_contract_sha256("embedding_runtime@1"),
        "backend_versions": encoder.backend_versions(),
        "sentence_count": len(out), "input_sentence_ids": [s["sentence_id"] for s in sentences],
        "input_text_sha256": sha256_bytes(canonical_json(hashes)),
        "sentences": out, "missing_reason": None if out else "no_content",
    }
