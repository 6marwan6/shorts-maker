"""Assemble transcript_v1 (impl plan Phase 3 3.5-3.7; owner decisions G1/G2/G4/G5).

Pure and deterministic: identical inputs give a byte-identical document. No I/O, no model calls.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from shorts_config import (
    AlignmentUnavailable,
    Config,
    Word,
    forced_alignment_gate_v1,
    sentence_seg_v1,
    validate_cut_anchor_timing_v1,
)

from workers.cpu.speaker_assignment import ASSIGNMENT_VERSION, assign_word_speaker, build_turns

STAGE_VERSION = "transcript@1"


def word_id(i: int) -> str:
    return f"W{i:06d}"


def sentence_id(i: int) -> str:
    return f"S{i:06d}"  # owner G2: S + six-digit 1-based ordinal, assigned after sentence_seg_v1


def _words_from_alignment(aligned: Sequence[dict]) -> list[dict]:
    out = []
    for w in aligned:
        s, e = w["start_ms"], w["end_ms"]
        if (s is None) != (e is None):
            # One-sided timing is not usable timing (owner G4: never interpolate/complete it).
            s = e = None
        out.append({"text": w["text"], "start_ms": s, "end_ms": e, "confidence": w.get("confidence")})
    return out


def build_transcript_v1(
    *, cfg: Config, source_video_id: str, input_sha256: str, language: dict,
    audio_availability: str, asr: dict, alignment_words: Sequence[dict] | None,
    alignment: dict, diarization: dict, model_manifest: dict,
) -> dict[str, Any]:
    """`asr` = provenance dict (status, runtime_id, runtime_sha256, segment_count, word_count).
    `alignment_words` = forced-aligned words or None (alignment not_applicable).
    `diarization` = provenance dict + optional "turns" (raw turns) when status == succeeded.
    Raises AlignmentUnavailable ONLY when ASR produced words but no word received forced-aligned timing
    (the overall mandatory-alignment contract, v5.0 2.14.1). A sentence edge whose boundary word is
    unaligned is kept and marked timing-unusable (owner decision 2026-10-02 #1) -- never a job failure."""
    asr_word_count = asr["word_count"]
    gate = forced_alignment_gate_v1(
        asr_word_count=asr_word_count, alignment_produced_word_timestamps=alignment_words is not None)
    words_in = _words_from_alignment(alignment_words or [])
    if gate == "not_applicable" and words_in:
        raise ValueError("alignment words supplied although ASR produced zero words")

    turns = build_turns(diarization.get("turns") or []) if diarization["status"] == "succeeded" else []
    diar_ok = diarization["status"] == "succeeded"

    words_out: list[dict] = []
    seg_words: list[Word] = []
    for i, w in enumerate(words_in, start=1):
        spk = assign_word_speaker(w["start_ms"], w["end_ms"], turns) if diar_ok else None
        words_out.append({
            "word_id": word_id(i), "text": w["text"], "start_ms": w["start_ms"], "end_ms": w["end_ms"],
            "timing_status": "aligned" if w["start_ms"] is not None else "unaligned",
            "confidence": w["confidence"], "speaker_id": spk,
        })
        seg_words.append(Word(w["text"], w["start_ms"], w["end_ms"], spk))

    spans = sentence_seg_v1(
        seg_words, sentence_gap_ms=cfg["SENTENCE_GAP_MS"], sentence_max_s=cfg["SENTENCE_MAX_S"],
        hard_split_min_gap_ms=cfg["HARD_SPLIT_MIN_GAP_MS"])
    if seg_words and not any(w.start_ms is not None for w in seg_words):
        raise AlignmentUnavailable("alignment_unavailable: no word received forced-aligned timing")
    usability = validate_cut_anchor_timing_v1(seg_words, spans)

    sentences: list[dict] = []
    for i, (sp, use) in enumerate(zip(spans, usability, strict=True), start=1):
        members = words_out[sp.word_start_idx: sp.word_end_idx + 1]
        # sentence.speaker_id = the first word's speaker (null if unassigned) -- convenience metadata
        # only (owner decision 2026-10-02 #4); word-level speaker_id stays authoritative.
        sentences.append({
            "sentence_id": sentence_id(i), "start_ms": sp.start_ms, "end_ms": sp.end_ms,
            "text": " ".join(m["text"] for m in members),
            "word_ids": [m["word_id"] for m in members],
            "speaker_id": members[0]["speaker_id"],
            "start_timing_usable": use.start_usable, "end_timing_usable": use.end_usable,
            "end_reason": sp.end_reason, "synthetic_boundary": sp.synthetic_boundary,
        })

    unaligned = sum(1 for w in words_out if w["timing_status"] == "unaligned")
    doc = {
        "schema_version": 1, "stage_version": STAGE_VERSION,
        "config_version": cfg.config_version, "config_sha256": cfg.config_sha256,
        "source_video_id": source_video_id, "input_sha256": input_sha256,
        "language": language,
        "words": words_out, "sentences": sentences,
        "speaker_turns": [
            {"turn_id": t.turn_id, "start_ms": t.start_ms, "end_ms": t.end_ms,
             "speaker_id": t.speaker_id, "raw_label": t.raw_label} for t in turns],
        "provenance": {
            "audio": {"availability": audio_availability},
            "asr": asr,
            "alignment": {**alignment, "status": gate, "unaligned_word_count": unaligned},
            "diarization": {
                "attempted": diarization["attempted"], "status": diarization["status"],
                "missing_reason": diarization["missing_reason"], "provider": diarization["provider"],
                "model_id": diarization["model_id"], "error_category": diarization["error_category"],
                "speaker_count": len({t.speaker_id for t in turns}),
            },
            "sentence_seg": {
                "version": "sentence_seg_v1", "sentence_gap_ms": cfg["SENTENCE_GAP_MS"],
                "sentence_max_s": cfg["SENTENCE_MAX_S"], "hard_split_min_gap_ms": cfg["HARD_SPLIT_MIN_GAP_MS"],
            },
            "speaker_assignment": {"version": ASSIGNMENT_VERSION},
            "model_manifest": model_manifest,
        },
    }
    return doc
