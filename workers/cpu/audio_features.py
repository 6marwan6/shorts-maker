"""Phase 4 audio analysis (owner decision 2026-10-07 s7; impl plan Phase 4.1).

Pure computation on already-decoded PCM + transcript_v1 words. No I/O, no DB, no config
defaults: every behavior-producing value is read from config@1 (impl plan §2.1).

Implementer's readings (neither document states them; flagged in the README Phase-4 log):
  R1 frames are NOT padded: frame i = samples [i*hop, i*hop+length) and only complete frames
     exist; a trailing partial second produces no 1 s frame.
  R2 the 10 ms frame i represents the interval [i*10, i*10+10) ms; its nonspeech test time t is
     the interval midpoint; a silence interval [first_start, last_start+10).
  R3 pause "entire interval nonspeech" = every 10 ms frame whose midpoint lies in [start, end).
  R4 local maximum = x[i] > x[i-1] and x[i] >= x[i+1] (first sample of a plateau), interior only.
  R5 rolling median/MAD: centered, edge-truncated window of ROLLING_BASELINE_WINDOW_S around the
     candidate sample (inclusive), MAD = median(|x - median|), RAW (robust_z_v1 applies 1.4826).
  R6 std is the population standard deviation (ddof=0).
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
from shorts_config import Config, robust_z_v1
from shorts_config.helpers import local_nonspeech_rms_v1

PEAK_LOCAL_MAX_RULE = "x[i] > x[i-1] and x[i] >= x[i+1], interior samples only"


def _frames(x: np.ndarray, length: int, hop: int) -> np.ndarray:
    if x.size < length:
        return np.zeros(0, dtype=np.float64)
    n = 1 + (x.size - length) // hop
    out = np.empty(n, dtype=np.float64)
    # exact, loop-free: cumulative sum of squares, difference per frame
    sq = np.concatenate(([0.0], np.cumsum(x.astype(np.float64) ** 2)))
    starts = np.arange(n, dtype=np.int64) * hop
    out[:] = np.sqrt((sq[starts + length] - sq[starts]) / length)
    return out


def rms_stream_v1(samples_f64: np.ndarray, length: int, hop: int) -> np.ndarray:
    """Linear-amplitude RMS per frame (R1: no padding)."""
    return _frames(samples_f64, length, hop)


def nonspeech_mask_10ms_v1(rms_10ms: np.ndarray, rms_1s: np.ndarray, *, hop_ms: float,
                           window_s: float, percentile: float) -> np.ndarray:
    """rms_10ms[i] <= local_nonspeech_rms_v1(t_i) with t_i the frame midpoint (R2). The threshold
    only changes when a 1 s frame center enters/leaves the window, so it is evaluated once per
    distinct (lo, hi) frame range -- exact, not an approximation."""
    n = rms_10ms.size
    mask = np.zeros(n, dtype=bool)
    if n == 0 or rms_1s.size == 0:
        return mask
    t = (np.arange(n) + 0.5) * hop_ms / 1000.0
    half = window_s / 2.0
    lo = np.maximum(0, np.ceil(t - half - 0.5).astype(np.int64))
    hi = np.minimum(rms_1s.size - 1, np.floor(t + half - 0.5).astype(np.int64))
    cache: dict[tuple[int, int], float | None] = {}
    for i in range(n):
        key = (int(lo[i]), int(hi[i]))
        if key not in cache:
            # evaluate via the single permitted helper at a time that yields exactly this range
            cache[key] = local_nonspeech_rms_v1(float(t[i]), rms_1s, window_s=window_s, percentile=percentile)
        th = cache[key]
        mask[i] = th is not None and rms_10ms[i] <= th
    return mask


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    """Maximal [first, last] index runs of True."""
    if mask.size == 0:
        return []
    d = np.diff(np.concatenate(([0], mask.astype(np.int8), [0])))
    starts = np.flatnonzero(d == 1)
    ends = np.flatnonzero(d == -1) - 1
    return list(zip(starts.tolist(), ends.tolist(), strict=True))


def silence_intervals_v1(mask: np.ndarray, hop_ms: int) -> list[dict[str, int]]:
    out = []
    for a, b in _runs(mask):
        s, e = a * hop_ms, (b + 1) * hop_ms
        out.append({"start_ms": s, "end_ms": e, "duration_ms": e - s})
    return out


def pause_intervals_v1(words: list[dict[str, Any]], mask: np.ndarray, hop_ms: int) -> list[dict[str, Any]]:
    """Every inter-word gap between consecutive words that BOTH have forced-aligned timing.
    A word with null timing is never a boundary (owner G4); the gap across it is not defined, so
    no interval is emitted for it (never interpolated)."""
    out = []
    for prev, nxt in zip(words, words[1:], strict=False):
        if prev["end_ms"] is None or nxt["start_ms"] is None:
            continue
        s, e = prev["end_ms"], nxt["start_ms"]
        if e <= s:
            continue
        # frames whose midpoint lies in [s, e)   (R3)
        first = max(0, math.ceil((s - hop_ms / 2) / hop_ms))
        last = math.ceil((e - hop_ms / 2) / hop_ms) - 1
        idx = range(first, min(last, mask.size - 1) + 1)
        n = len(idx)
        frac = float(mask[idx.start:idx.stop].sum()) / n if n else 0.0
        out.append({
            "start_ms": s, "end_ms": e, "duration_ms": e - s,
            "previous_word_id": prev["word_id"], "next_word_id": nxt["word_id"],
            "fully_nonspeech": bool(n > 0 and frac == 1.0), "nonspeech_frame_fraction": frac,
        })
    return out


def audio_peaks_v1(rms_10ms: np.ndarray, *, hop_ms: int, window_s: float, z_min: float,
                   min_spacing_s: float, mad_floor: float) -> list[dict[str, Any]]:
    """v5.0 2.36.4 peak definition on the canonical 10 ms stream (owner s7): local maximum with
    robust z >= z_min against the centered rolling median/MAD, and at least min_spacing_s from
    the previous ACCEPTED peak (chronological greedy). Medians are only computed for candidates
    that can possibly qualify (x - median >= z_min * mad_floor * 1.4826 with median >= 0), which
    is a necessary condition, so the pruning is exact."""
    n = rms_10ms.size
    if n < 3:
        return []
    half = int(round(window_s * 1000 / hop_ms / 2))
    min_abs = z_min * 1.4826 * mad_floor
    cand = np.flatnonzero((rms_10ms[1:-1] > rms_10ms[:-2]) & (rms_10ms[1:-1] >= rms_10ms[2:]) & (rms_10ms[1:-1] >= min_abs)) + 1
    peaks: list[dict[str, Any]] = []
    last_t = None
    for i in cand.tolist():
        t_ms = i * hop_ms
        if last_t is not None and (t_ms - last_t) < min_spacing_s * 1000:
            continue
        w = rms_10ms[max(0, i - half): min(n, i + half + 1)]
        med = float(np.median(w))
        mad = float(np.median(np.abs(w - med)))
        z = robust_z_v1(float(rms_10ms[i]), med, mad, mad_floor)
        if z is not None and z >= z_min:
            peaks.append({"time_ms": t_ms, "rms": float(rms_10ms[i]), "rolling_median": med,
                          "rolling_mad": mad, "robust_z": float(z)})
            last_t = t_ms
    return peaks


def rms_db_by_bin_v1(rms_10ms: np.ndarray, *, hop_ms: int, bin_s: int, epsilon: float,
                     duration_ms: int) -> list[dict[str, Any]]:
    """20*log10(max(rms, epsilon)) per 10 ms frame; mean and population std (R6) over the frames
    whose START lies in each PROFILE_BIN_S bin. LUFS is never used here (owner s7)."""
    db = 20.0 * np.log10(np.maximum(rms_10ms, epsilon)) if rms_10ms.size else rms_10ms
    bin_ms = bin_s * 1000
    n_bins = max(1, math.ceil(duration_ms / bin_ms)) if duration_ms > 0 else 0
    out = []
    for b in range(n_bins):
        s, e = b * bin_ms, min((b + 1) * bin_ms, duration_ms)
        i0, i1 = math.ceil(s / hop_ms), math.ceil(e / hop_ms)
        seg = db[i0:i1]
        if seg.size == 0:
            out.append({"bin_index": b, "start_ms": s, "end_ms": e, "frame_count": 0,
                        "rms_mean_db": None, "rms_std_db": None, "m": "no_content"})
        else:
            out.append({"bin_index": b, "start_ms": s, "end_ms": e, "frame_count": int(seg.size),
                        "rms_mean_db": float(seg.mean()), "rms_std_db": float(seg.std()), "m": None})
    return out


def compute_audio_features(pcm_int16: np.ndarray | None, words: list[dict[str, Any]], cfg: Config,
                           *, epsilon: float | None) -> dict[str, Any]:
    """Returns the content fields of audio_features_v1 (identity/provenance fields are added by
    the stage). `pcm_int16 is None` = source has no audio stream (owner G6) -> empty arrays and
    missing_reason = not_applicable. `epsilon` comes from rms_db_runtime@1 (BLOCKED_BY_SPEC today;
    the caller must obtain it via cfg.runtime_contract and let ConfigSpecGap propagate)."""
    length, hop = cfg["RMS_FRAME_LENGTH_SAMPLES"], cfg["RMS_HOP_LENGTH_SAMPLES"]
    sr = cfg["ANALYSIS_SAMPLE_RATE_HZ"]
    hop_ms = round(hop * 1000 / sr)
    base = {
        "sample_rate_hz": sr, "rms_frame_length_samples": length, "rms_hop_length_samples": hop,
        "rms_1s_frame_length_samples": cfg["RMS_1S_FRAME_SAMPLES"], "rms_1s_hop_length_samples": cfg["RMS_1S_HOP_SAMPLES"],
        "nonspeech_threshold_definition": {
            "helper": "local_nonspeech_rms_v1", "window_s": cfg["LOCAL_NONSPEECH_WINDOW_S"],
            "percentile": cfg["LOCAL_NONSPEECH_PERCENTILE"], "frame_s": 1, "centered": True,
            "edge_truncated": True, "domain": "linear_rms", "percentile_method": "numpy linear",
            "frame_membership": "1 s frame j belongs to the window iff its center j+0.5 lies in [t-30, t+30]",
        },
    }
    if pcm_int16 is None:
        return {**base, "rms_samples": [], "rms_1s_samples": [], "silence_intervals": [],
                "pause_intervals": [], "audio_peaks": [], "rms_std_db_by_analysis_bin": [],
                "missing_reason": "not_applicable"}
    if epsilon is None:
        raise ValueError("epsilon is required (rms_db_runtime@1 is BLOCKED_BY_SPEC); refusing to default")
    x = pcm_int16.astype(np.float64) / 32768.0
    rms10 = rms_stream_v1(x, length, hop)
    rms1s = rms_stream_v1(x, cfg["RMS_1S_FRAME_SAMPLES"], cfg["RMS_1S_HOP_SAMPLES"])
    mask = nonspeech_mask_10ms_v1(rms10, rms1s, hop_ms=hop_ms, window_s=cfg["LOCAL_NONSPEECH_WINDOW_S"],
                                  percentile=cfg["LOCAL_NONSPEECH_PERCENTILE"])
    duration_ms = round(x.size * 1000 / sr)
    return {
        **base,
        "rms_samples": rms10.tolist(), "rms_1s_samples": rms1s.tolist(),
        "silence_intervals": silence_intervals_v1(mask, hop_ms),
        "pause_intervals": pause_intervals_v1(words, mask, hop_ms),
        "audio_peaks": audio_peaks_v1(rms10, hop_ms=hop_ms, window_s=cfg["ROLLING_BASELINE_WINDOW_S"],
                                      z_min=cfg["PEAK_ROBUST_Z_MIN"], min_spacing_s=cfg["PEAK_MIN_SPACING_S"],
                                      mad_floor=cfg["RMS_MAD_FLOOR"]),
        "rms_std_db_by_analysis_bin": rms_db_by_bin_v1(rms10, hop_ms=hop_ms, bin_s=cfg["PROFILE_BIN_S"],
                                                      epsilon=epsilon, duration_ms=duration_ms),
        "missing_reason": None,
    }
