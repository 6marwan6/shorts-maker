"""diarization_v1 word->speaker assignment (owner decision G5, 2026-09-30).

* Raw diarization turns are preserved exactly (boundaries as returned; no minimum turn length, no
  merge gap, overlapping turns kept).
* speaker(word) = the turn with maximum temporal overlap with the word; ties -> earliest turn
  start, then first-appearance speaker order. No overlapping turn -> None. Unaligned words
  (null timing) have no overlap by definition -> None.
* Speaker ids are SPK_<n>, numbered by first appearance over turns sorted by
  (start_ms, end_ms, raw_label). Sorting only fixes a deterministic order; it does not alter
  any turn's content.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

ASSIGNMENT_VERSION = "diarization_v1"


@dataclass(frozen=True)
class Turn:
    turn_id: str
    start_ms: int
    end_ms: int
    speaker_id: str
    raw_label: str


def build_turns(raw_turns: Sequence[dict]) -> list[Turn]:
    ordered = sorted(raw_turns, key=lambda t: (t["start_ms"], t["end_ms"], t["raw_label"]))
    order: dict[str, str] = {}
    turns: list[Turn] = []
    for i, t in enumerate(ordered, start=1):
        spk = order.setdefault(t["raw_label"], f"SPK_{len(order)}")
        turns.append(Turn(f"T{i:06d}", t["start_ms"], t["end_ms"], spk, t["raw_label"]))
    return turns


def _overlap(a0: int, a1: int, b0: int, b1: int) -> int:
    return max(0, min(a1, b1) - max(a0, b0))


def assign_word_speaker(start_ms: int | None, end_ms: int | None, turns: Sequence[Turn]) -> str | None:
    if start_ms is None or end_ms is None or not turns:
        return None
    first_seen = {}
    for t in turns:
        first_seen.setdefault(t.speaker_id, len(first_seen))
    best: tuple[int, int, int, str] | None = None  # (-overlap, turn_start, first_appearance, speaker)
    for t in turns:
        ov = _overlap(start_ms, end_ms, t.start_ms, t.end_ms)
        if ov <= 0:
            continue
        key = (-ov, t.start_ms, first_seen[t.speaker_id], t.speaker_id)
        if best is None or key < best:
            best = key
    return None if best is None else best[3]
