"""Shared deterministic primitives (implementation plan 2.3 / v5.0 2.36.0).

`robust_z_v1` (Phase 0) and `local_nonspeech_rms_v1` (Phase 4, owner decision 2026-10-07 s7)
are implemented here. The remaining Phase-5+-dependent helpers (event_safe_cut_v1,
latest_safe_before, earliest_safe_after, d_clean_v1, super_unit_embedding_v1) stay deferred
until their artifact I/O shapes exist (owner decision, 2026-09-24). The five Phase-0.7 deterministic analysis primitives (sentence_seg_v1,
TextTiling_depth_v1, embedding-provenance validation, no-diarization fallback, the forced-
alignment gate) are pure functions operating on already-produced inputs, so they are
implemented now in analysis_primitives.py instead.
"""
from __future__ import annotations

import math

ROBUST_Z_ZERO_MAD = 6.0  # mirrors config@1 constant; verified equal by tests


def robust_z_v1(x, center, mad, floor, zero_mad: float = ROBUST_Z_ZERO_MAD):
    """v5.0 2.36.0. Single permitted implementation of a robust z-score."""
    if x is None or center is None or mad is None:
        return None
    den = max(1.4826 * max(mad, 0), max(floor, 0))
    if den > 0:
        return (x - center) / den
    if x == center:
        return 0
    return math.copysign(zero_mad, x - center)


def local_nonspeech_rms_v1(t_s: float, rms_1s, *, window_s: float = 60.0, percentile: float = 20.0):
    """v5.0 2.36.0 / owner decision 2026-10-07 s7. The 20th percentile of the 1 s linear-RMS frames
    in the CENTERED 60 s window around t (edge-truncated, never trailing). `rms_1s[j]` is the RMS
    of second [j, j+1). Returns None when no frame falls inside the window.

    Implementer's readings (flagged, neither document states them): a 1 s frame belongs to the
    window iff its CENTER (j + 0.5) lies in [t - window_s/2, t + window_s/2]; the percentile uses
    numpy's default 'linear' interpolation. Both are recorded in audio_features_v1's
    nonspeech_threshold_definition."""
    import numpy as np

    n = len(rms_1s)
    if n == 0:
        return None
    half = window_s / 2.0
    lo = max(0, int(np.ceil(t_s - half - 0.5)))
    hi = min(n - 1, int(np.floor(t_s + half - 0.5)))
    if hi < lo:
        return None
    return float(np.percentile(np.asarray(rms_1s[lo:hi + 1], dtype=np.float64), percentile))
