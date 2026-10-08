"""Phase 4 texttiling_depth_v1 content (owner decision 2026-10-07 s8): the exact v5.0 2.14.1
TextTiling_depth_v1 primitive (Phase 0) applied to sentence_embeddings_v1; no alternate
implementation. Incomplete window pairs are explicit nulls with missing reason `no_evidence`
(flagged reading: the vocabulary has no 'incomplete_window' entry; adding one needs a v5.0 amendment)."""
from __future__ import annotations

from typing import Any

from shorts_config import Config, TextTiling_depth_v1
from shorts_config.analysis_primitives import _gap_at


def compute_texttiling(sentence_ids: list[str], embeddings: list[list[float]], cfg: Config) -> dict[str, Any]:
    ws, wt = cfg["TEXTTILING_SEMANTIC_W"], cfg["TEXTTILING_TOPIC_W"]
    n = len(sentence_ids)
    if n != len(embeddings):
        raise ValueError("sentence_ids and embeddings must align one-to-one")
    sem_d = TextTiling_depth_v1(embeddings, ws)
    top_d = TextTiling_depth_v1(embeddings, wt)
    bounds = []
    for b in range(max(0, n - 1)):
        sg, tg = _gap_at(embeddings, b, ws), _gap_at(embeddings, b, wt)
        bounds.append({
            "sentence_id_left": sentence_ids[b], "sentence_id_right": sentence_ids[b + 1],
            "semantic_gap": sg, "topic_gap": tg, "semantic_depth": sem_d[b], "topic_depth": top_d[b],
            "semantic_missing_reason": None if sem_d[b] is not None else "no_evidence",
            "topic_missing_reason": None if top_d[b] is not None else "no_evidence",
        })
    return {"semantic_window": ws, "topic_window": wt, "boundaries": bounds,
            "missing_reason": None if bounds else "no_content"}
