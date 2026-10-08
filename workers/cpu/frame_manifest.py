"""Phase 4 frame_manifest_v1 content (owner decision 2026-10-07 s8). Describes sampled-frame STREAMS
(no pixels). Sampling is exact-rational:

    t_k = k / sampling_fps ;  source_frame_index = floor(k * source_fps / sampling_fps)
    pts_ms = round-half-up(source_frame_index * 1000 / source_fps)

and a sample exists iff source_frame_index < source_frame_count (flagged readings: the owner
decision fixes the stream list and fields but not the index rule).

The width/height of motion/motion_probe/screen frames depend on frame_resize_runtime@1
(interpolation / upscale policy), which is BLOCKED_BY_SPEC -- `resolve_size` must be supplied by a
caller that obtained it from that contract; this module never guesses a resize."""
from __future__ import annotations

from collections.abc import Callable
from fractions import Fraction
from typing import Any

from shorts_config import Config

from .shot_map import frame_to_ms

# stream_id -> (purpose, config name of sampling fps or None for native, max-dimension config name or None)
STREAMS = (
    ("face", "face detection", "FACE_SAMPLE_FPS", None),
    ("motion", "canonical motion features", "MOTION_SAMPLE_FPS", "MOTION_MAX_DIM_PX"),
    ("motion_probe", "internal 0.3 s sustained-motion probe", "MOTION_EVENT_PROBE_FPS", "MOTION_MAX_DIM_PX"),
    ("screen", "screen-content detection", "SCREEN_ANALYSIS_FPS", "SCREEN_MAX_DIM_PX"),
    ("scene_context", "general 2 fps visual-analysis stream", "SCENE_ANALYSIS_FPS", None),
    ("shot_detection", "ContentDetector over every normalized frame (metadata only)", None, None),
)


def sample_frames(duration_frames: int, source_fps: Fraction, sampling_fps: Fraction) -> list[tuple[int, int]]:
    """[(source_frame_index, pts_ms)] for every sample k with source_frame_index < duration_frames."""
    out, k = [], 0
    while True:
        idx = (Fraction(k) * source_fps / sampling_fps) // 1
        if idx >= duration_frames:
            return out
        out.append((int(idx), frame_to_ms(int(idx), source_fps)))
        k += 1


def build_frame_manifest(*, source_fps: Fraction, source_frame_count: int, width: int, height: int,
                         cfg: Config, resolve_size: Callable[[str, int, int, int | None], tuple[int, int, dict]]) -> dict[str, Any]:
    """resolve_size(stream_id, width, height, max_dim) -> (w, h, resize_policy). For streams whose
    max_dim is None it is called with None and must return the native size."""
    streams = []
    for sid, purpose, fps_name, dim_name in STREAMS:
        if fps_name is None:
            streams.append({"stream_id": sid, "purpose": purpose, "sampling_fps": None,
                            "source_fps": float(source_fps), "width": width, "height": height,
                            "resize_policy": {"kind": "native"}, "frame_count": source_frame_count, "frames": None})
            continue
        fps = Fraction(cfg[fps_name]).limit_denominator(1000)
        w, h, policy = resolve_size(sid, width, height, cfg[dim_name] if dim_name else None)
        frames = [{"sample_index": k, "source_frame_index": i, "pts_ms": p, "width": w, "height": h}
                  for k, (i, p) in enumerate(sample_frames(source_frame_count, source_fps, fps))]
        streams.append({"stream_id": sid, "purpose": purpose, "sampling_fps": float(fps),
                        "source_fps": float(source_fps), "width": w, "height": h,
                        "resize_policy": policy, "frame_count": len(frames), "frames": frames})
    return {"source_fps": float(source_fps), "source_frame_count": source_frame_count,
            "duration_ms": frame_to_ms(source_frame_count, source_fps), "streams": streams, "missing_reason": None}
