"""Deterministic analysis primitives, v5.0 2.14.1 (implementation plan 0.7 / 2.3).

These are pure functions operating on already-produced inputs (word timestamps, sentence
embeddings, a boolean diarization-availability flag) so they are testable now, in Phase 0,
with synthetic fixtures -- before Phase 3/4 wire them to real WhisperX/diarization/embedding
output. Per impl plan 2.3: "No local implementation of these functions is permitted in
discovery, ranking, editing, verification, hook, reframe or Tier 2 code" -- this module is
the single permitted implementation location.

Deliberately excluded here (impl plan §0.6, owner decision 2026-09-24): event_safe_cut_v1,
latest_safe_before, earliest_safe_after, local_nonspeech_rms_v1, d_clean_v1,
super_unit_embedding_v1. Those six need Phase 3/4 artifact shapes to avoid guessing I/O and
stay deferred.

No third-party dependencies (no numpy): shorts_config is imported by every worker, including
lightweight CPU-only stages, so vector math here is plain Python.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

# --------------------------------------------------------------------------------------
# sentence_seg_v1 (v5.0 2.14.1)
# --------------------------------------------------------------------------------------

_TERMINAL_PUNCT = (".", "!", "?")
_TERMINAL_TRAILERS = ("\"", "'", "\u201d", "\u2019", ")", "]")


@dataclass(frozen=True)
class Word:
    """One forced-aligned word. speaker_id is optional (None when diarization unavailable)."""
    text: str
    start_ms: int | None  # None = unaligned (owner decision G4: text kept, timing null)
    end_ms: int | None
    speaker_id: str | None = None


@dataclass(frozen=True)
class Sentence:
    word_start_idx: int
    word_end_idx: int  # inclusive
    start_ms: int | None  # None only when the edge word is unaligned (owner #1); never synthesized
    end_ms: int | None
    end_reason: str  # "terminal_punctuation" | "gap_speaker_change" | "gap_uppercase" | "end_of_input" | "hard_split_gap" | "synthetic_split"
    synthetic_boundary: bool


def _ends_with_terminal_punctuation(text: str) -> bool:
    t = text.rstrip()
    while t and t[-1] in _TERMINAL_TRAILERS:
        t = t[:-1]
    return bool(t) and t[-1] in _TERMINAL_PUNCT


def _starts_uppercase(text: str) -> bool:
    stripped = text.lstrip("\"'\u201c\u2018([")
    return bool(stripped) and stripped[0].isalpha() and stripped[0].isupper()


def _initial_boundaries(words: Sequence[Word], sentence_gap_ms: int) -> list[tuple[int, int, str]]:
    """First pass: (start_idx, end_idx, end_reason) using terminal punctuation / gap+trigger rule.

    v5.0: "End it at the earliest terminal punctuation boundary that has a usable word
    timestamp, or at an inter-word gap >= SENTENCE_GAP_MS when either the speaker changes at
    the boundary or the next token begins with an uppercase letter." A terminal-punctuation
    word with no usable end_ms does not count -- scanning continues past it.
    """
    spans: list[tuple[int, int, str]] = []
    n = len(words)
    start = 0
    i = 0
    while i < n:
        w = words[i]
        is_last = i == n - 1
        ends_here = False
        reason = "end_of_input"
        if not is_last:
            if _ends_with_terminal_punctuation(w.text) and w.end_ms is not None:
                ends_here = True
                reason = "terminal_punctuation"
            else:
                nxt = words[i + 1]
                if w.end_ms is not None and nxt.start_ms is not None:
                    gap = nxt.start_ms - w.end_ms
                    if gap >= sentence_gap_ms:
                        speaker_changed = w.speaker_id != nxt.speaker_id and (
                            w.speaker_id is not None or nxt.speaker_id is not None
                        )
                        if speaker_changed:
                            ends_here = True
                            reason = "gap_speaker_change"
                        elif _starts_uppercase(nxt.text):
                            ends_here = True
                            reason = "gap_uppercase"
        else:
            ends_here = True
            reason = "end_of_input"
        if ends_here:
            spans.append((start, i, reason))
            start = i + 1
        i += 1
    return spans


def _gap_ms(words: Sequence[Word], i: int) -> int:
    """Inter-word gap between words[i] and words[i+1]; missing timestamps treat gap as 0
    (never a split candidate) rather than raising -- keeps the splitter total on any input."""
    a, b = words[i], words[i + 1]
    if a.end_ms is None or b.start_ms is None:
        return 0
    return b.start_ms - a.end_ms


def _split_long_span(
    words: Sequence[Word], start: int, end: int, max_span_ms: int, hard_split_min_gap_ms: int
) -> list[tuple[int, int, bool]]:
    """Recursively split [start, end] (inclusive word indices) so every piece is <= max_span_ms.

    Returns [(piece_start, piece_end, synthetic_boundary_at_piece_end), ...] in order.
    The synthetic flag describes ONLY the boundary at the end of that piece; a piece's own
    original end reason (terminal punctuation / gap rule / end of input) is restored by the
    caller onto the final piece, since that boundary was never touched by this split.
    """
    if end <= start:
        return [(start, end, False)]
    # Span is measured between the first and last words that actually have timing; unaligned
    # words are never given interpolated timing (owner decision G4).
    first_t = next((words[i].start_ms for i in range(start, end + 1) if words[i].start_ms is not None), None)
    last_t = next(
        ((words[i].end_ms if words[i].end_ms is not None else words[i].start_ms)
         for i in range(end, start - 1, -1)
         if words[i].end_ms is not None or words[i].start_ms is not None), None)
    span_ms = 0 if first_t is None or last_t is None else last_t - first_t
    if span_ms <= max_span_ms:
        return [(start, end, False)]

    gaps = [(_gap_ms(words, i), i) for i in range(start, end)]
    qualifying = [(g, i) for g, i in gaps if g >= hard_split_min_gap_ms]
    if qualifying:
        best = max(g for g, _ in qualifying)
        split_at = min(i for g, i in qualifying if g == best)  # ties -> earliest gap
        synthetic = False
    else:
        best = max(g for g, _ in gaps)
        split_at = min(i for g, i in gaps if g == best)
        synthetic = True

    left = _split_long_span(words, start, split_at, max_span_ms, hard_split_min_gap_ms)
    right = _split_long_span(words, split_at + 1, end, max_span_ms, hard_split_min_gap_ms)
    ls, le, _ = left[-1]
    left[-1] = (ls, le, synthetic)
    return left + right


def sentence_seg_v1(
    words: Sequence[Word], *, sentence_gap_ms: int, sentence_max_s: int, hard_split_min_gap_ms: int
) -> list[Sentence]:
    """v5.0 2.14.1. Input MUST be forced-aligned word timings (impl plan 3.4/3.5: never coarse
    ASR segment timing). Never splits inside a word -- every split point is an inter-word gap.
    """
    if not words:
        return []
    max_span_ms = sentence_max_s * 1000
    initial = _initial_boundaries(words, sentence_gap_ms)
    out: list[Sentence] = []
    for start, end, reason in initial:
        pieces = _split_long_span(words, start, end, max_span_ms, hard_split_min_gap_ms)
        for idx, (ps, pe, synthetic) in enumerate(pieces):
            is_last_piece = idx == len(pieces) - 1
            piece_reason = reason if is_last_piece else ("synthetic_split" if synthetic else "hard_split_gap")
            piece_synthetic = False if is_last_piece else synthetic
            start_ms = words[ps].start_ms
            end_ms = words[pe].end_ms  # no fallback to start_ms: an unaligned/one-sided word stays null
            out.append(Sentence(ps, pe, start_ms, end_ms, piece_reason, piece_synthetic))
    return out


# --------------------------------------------------------------------------------------
# TextTiling_depth_v1 (v5.0 2.14.1)
# --------------------------------------------------------------------------------------

def _mean_vec(vectors: Sequence[Sequence[float]]) -> list[float]:
    n = len(vectors)
    dim = len(vectors[0])
    return [sum(v[d] for v in vectors) / n for d in range(dim)]


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _gap_at(embeddings: Sequence[Sequence[float]], b: int, window: int) -> float | None:
    """gap(b, W): complete pair of windows required (both L and R exactly size W), else None.

    v5.0's final sentence ("a boundary without a complete pair of windows is null") is read as
    governing gap(b,W) itself, not only the peak search around it -- see this module's README
    note / the implementation plan Q&A this was checked against. Flagged as an interpretation,
    not a literal transcription, per this repo's convention for underspecified edge behavior.
    """
    n = len(embeddings)
    l_start = b - window + 1
    r_end = b + window
    if l_start < 0 or r_end > n - 1:
        return None
    L = _mean_vec(embeddings[l_start : b + 1])
    R = _mean_vec(embeddings[b + 1 : r_end + 1])
    return 1.0 - _cosine(L, R)


def TextTiling_depth_v1(embeddings: Sequence[Sequence[float]], window: int) -> list[float | None]:
    """v5.0 2.14.1. embeddings[i] = sentence i's L2-normalized embedding vector. Returns depth(b,W)
    for every boundary b in range(0, len(embeddings) - 1); None where the pair of windows is
    incomplete ("skipped by downstream change-point logic")."""
    n = len(embeddings)
    if n < 2:
        return []
    n_boundaries = n - 1
    gaps: list[float | None] = [_gap_at(embeddings, b, window) for b in range(n_boundaries)]

    depths: list[float | None] = []
    for b in range(n_boundaries):
        gap_b = gaps[b]
        if gap_b is None:
            depths.append(None)
            continue
        left_candidates = [gaps[i] for i in range(max(0, b - window + 1), b) if gaps[i] is not None]
        right_candidates = [gaps[i] for i in range(b + 1, min(n_boundaries, b + window)) if gaps[i] is not None]
        if not left_candidates or not right_candidates:
            depths.append(None)
            continue
        left_peak = max(left_candidates)
        right_peak = max(right_candidates)
        depths.append(max(0.0, left_peak - gap_b) + max(0.0, right_peak - gap_b))
    return depths


# --------------------------------------------------------------------------------------
# Deterministic embedding provenance (v5.0 2.14.1 / impl plan 4.4)
# --------------------------------------------------------------------------------------

# v5.0 2.14.1: "MVP embedding inference must run deterministically (fixed model, tokenizer,
# precision and deterministic backend settings) or be treated as a build failure." -- these
# four facets, plus model_id/model_revision/checksum/backend (impl plan 4.4), are exactly the
# required provenance fields; nothing invented beyond that sentence + that requirement.
REQUIRED_EMBEDDING_PROVENANCE_FIELDS = (
    "model_id", "model_revision", "checksum", "backend", "tokenizer", "precision", "deterministic",
)


class EmbeddingProvenanceIncomplete(ValueError):
    """v5.0 2.14.1: missing/non-deterministic embedding provenance is a build failure, not a
    warning -- this is raised, never silently defaulted."""


def validate_embedding_provenance_v1(provenance: dict[str, Any], *, expected_model_id: str) -> None:
    missing = [f for f in REQUIRED_EMBEDDING_PROVENANCE_FIELDS if f not in provenance or provenance[f] in (None, "")]
    if missing:
        raise EmbeddingProvenanceIncomplete(f"missing embedding provenance fields: {missing}")
    if provenance["model_id"] != expected_model_id:
        raise EmbeddingProvenanceIncomplete(
            f"embedding model_id {provenance['model_id']!r} != pinned EMBEDDING_MODEL_ID {expected_model_id!r}"
        )
    if provenance["deterministic"] is not True:
        raise EmbeddingProvenanceIncomplete("embedding inference must be deterministic (fixed model/tokenizer/precision/backend)")


# --------------------------------------------------------------------------------------
# No-diarization fallback (v5.0 2.14.1)
# --------------------------------------------------------------------------------------

def speaker_dependent_feature_v1(value: Any, *, diarization_available: bool) -> dict[str, Any]:
    """v5.0 2.14.1: 'when unavailable, speaker_change, qa_start, qa_end and any other
    speaker-dependent feature are returned as null with m = not_available_in_stage; no zero is
    substituted.' Generic {v,m} wrapper for any such feature."""
    if not diarization_available:
        return {"v": None, "m": "not_available_in_stage"}
    return {"v": value, "m": None}


def speaker_id_v1(raw_speaker_id: str | None, *, diarization_available: bool) -> str | None:
    """v5.0 2.14.1: 'speaker_id is likewise null' when diarization is unavailable."""
    if not diarization_available:
        return None
    return raw_speaker_id


# --------------------------------------------------------------------------------------
# Mandatory forced alignment gate (v5.0 2.14.1 / impl plan 3.4)
# --------------------------------------------------------------------------------------

class AlignmentUnavailable(Exception):
    """v5.0 2.14.1: 'fail the analysis stage with alignment_unavailable; do not silently
    substitute coarse segment timings for cut-safety decisions.'"""


def forced_alignment_gate_v1(*, asr_word_count: int, alignment_produced_word_timestamps: bool) -> str:
    """Returns 'not_applicable' (zero-word ASR -> event-led/no-text path is allowed to enter
    ANALYZING) or 'aligned' (transcript-bearing job with real word-level timestamps).
    Raises AlignmentUnavailable when ASR produced words but alignment did not succeed -- the
    job must NOT enter ANALYZING on coarse ASR segment timing in that case."""
    if asr_word_count <= 0:
        return "not_applicable"
    if alignment_produced_word_timestamps:
        return "aligned"
    raise AlignmentUnavailable("alignment_unavailable")


@dataclass(frozen=True)
class CutAnchorUsability:
    """Per-sentence timing usability (owner decision 2026-10-02 #1)."""
    start_usable: bool
    end_usable: bool


def validate_cut_anchor_timing_v1(words: Sequence[Word], sentences: Sequence[Sentence]) -> list[CutAnchorUsability]:
    """Per-sentence / per-boundary usability predicate. NEVER raises and never alters text or timing.

    A sentence edge is a usable cut-safety anchor only when the word at that edge carries a real
    forced-aligned start AND end timestamp. Otherwise the edge is marked unusable: the sentence and
    its text are preserved, no timestamp is synthesized or borrowed from coarse ASR timing, and
    downstream cut generation must not use that boundary. There is deliberately no percentage
    threshold. (The only job-level failure -- no word at all received alignment -- is raised by
    the transcript builder as AlignmentUnavailable, per the v5.0 mandatory-alignment contract.)
    """
    def timed(w: Word) -> bool:
        return w.start_ms is not None and w.end_ms is not None

    return [CutAnchorUsability(timed(words[s.word_start_idx]), timed(words[s.word_end_idx])) for s in sentences]
