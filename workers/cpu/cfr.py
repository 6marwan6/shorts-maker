"""CFR determination from frame presentation timestamps (owner decision 2026-10-02 #13).

Not inferred from r_frame_rate. A source is CFR (eligible for FPS preservation) only when
  1. consecutive frame PTS deltas, in presentation order, are all identical AND > 0, and
  2. the exact rational FPS derived from that delta and the stream time_base is one of
     {24, 25, 30, 50, 60}.
Anything else is non-eligible and is normalized to constant 30 FPS. The decision and its
reason are persisted in media_manifest_v1. Integer PTS ticks are compared exactly (no float
tolerance); a container whose ticks are rounded (e.g. ms time_base at 30 fps -> 33/34 tick
deltas) is therefore classified variable_deltas, per the owner's strict wording.
"""
from __future__ import annotations

import itertools
import json
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

from workers.shared.failures import FailureKind, StageFailure

ELIGIBLE_FPS = (24, 25, 30, 50, 60)
FALLBACK_FPS = 30


@dataclass(frozen=True)
class CFRDecision:
    is_cfr: bool                 # both owner conditions hold
    reason: str                  # cfr_eligible | insufficient_frames | missing_pts | non_positive_delta
    #                              | variable_deltas | fps_not_eligible | no_video_stream
    frame_count: int
    time_base: str | None        # "n/d"
    constant_delta_ticks: int | None
    derived_fps: str | None      # exact rational "n/d" when deltas are constant

    @property
    def selected_fps(self) -> int:
        if self.is_cfr:
            return int(Fraction(self.derived_fps))  # type: ignore[arg-type]
        return FALLBACK_FPS


def classify_cfr_v1(pts_ticks: list[int | None], time_base: Fraction | None) -> CFRDecision:
    n = len(pts_ticks)
    tb = None if time_base is None else f"{time_base.numerator}/{time_base.denominator}"
    if time_base is None or n < 2:
        return CFRDecision(False, "insufficient_frames", n, tb, None, None)
    if any(p is None for p in pts_ticks):
        return CFRDecision(False, "missing_pts", n, tb, None, None)
    ordered = sorted(p for p in pts_ticks if p is not None)  # presentation order (B-frames)
    deltas = {b - a for a, b in itertools.pairwise(ordered)}
    if min(deltas) <= 0:
        return CFRDecision(False, "non_positive_delta", n, tb, None, None)
    if len(deltas) != 1:
        return CFRDecision(False, "variable_deltas", n, tb, None, None)
    delta = next(iter(deltas))
    fps = 1 / (Fraction(delta) * time_base)
    fps_s = f"{fps.numerator}/{fps.denominator}"
    if fps not in ELIGIBLE_FPS:
        return CFRDecision(False, "fps_not_eligible", n, tb, delta, fps_s)
    return CFRDecision(True, "cfr_eligible", n, tb, delta, fps_s)


def probe_frame_pts(path: str | Path) -> tuple[list[int | None], Fraction | None]:
    """All video-frame PTS (ticks) of the first video stream + its time_base."""
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "frame=pts,pkt_pts,best_effort_timestamp:stream=time_base",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise StageFailure(FailureKind.PERMANENT_INPUT, "unreadable_media", proc.stderr.strip()[:500])
    doc = json.loads(proc.stdout)
    streams = doc.get("streams") or []
    tb_s = streams[0].get("time_base") if streams else None
    tb = Fraction(tb_s) if tb_s and "/" in tb_s and not tb_s.startswith("0/") else None
    pts: list[int | None] = []
    for fr in doc.get("frames") or []:
        v = fr.get("pts", fr.get("pkt_pts", fr.get("best_effort_timestamp")))
        pts.append(None if v in (None, "N/A") else int(v))
    return pts, tb


def determine_cfr(path: str | Path) -> CFRDecision:
    pts, tb = probe_frame_pts(path)
    return classify_cfr_v1(pts, tb)
