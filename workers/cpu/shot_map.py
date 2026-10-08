"""Phase 4 shot map (owner decision 2026-10-07 s3): frame-accurate PySceneDetect ContentDetector
over EVERY decoded normalized frame. Never derived from the 2 fps analysis grid."""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from shorts_config import Config


def frame_to_ms(frame: int, fps: Fraction | int | float) -> int:
    """pts_ms = round-half-up(frame * 1000 / fps), exact rational arithmetic (flagged reading:
    schema ms are integers; frame identity stays exact in start_frame/end_frame)."""
    f = Fraction(fps).limit_denominator(1_000_000) if not isinstance(fps, Fraction) else fps
    v = Fraction(frame) * 1000 / f
    return int((v + Fraction(1, 2)) // 1)


def shots_from_scene_list(scenes: list[tuple[int, int]], frame_count: int, fps: float) -> list[dict[str, int]]:
    """scenes = [(start_frame, end_frame_exclusive), ...] as reported by the detector. A video
    with no detected cut is one shot covering all frames. Validates monotonic, gap-free,
    non-overlapping coverage of [0, frame_count) -- anything else is an error, never repaired."""
    if frame_count < 1:
        raise ValueError("frame_count must be >= 1")
    if not scenes:
        scenes = [(0, frame_count)]
    out = []
    expect = 0
    for i, (s, e) in enumerate(scenes):
        if s != expect or e <= s or e > frame_count:
            raise ValueError(f"shot {i} ({s},{e}) is not contiguous/monotonic (expected start {expect}, frame_count {frame_count})")
        out.append({"shot_index": i, "start_ms": frame_to_ms(s, fps), "end_ms": frame_to_ms(e, fps),
                    "start_frame": s, "end_frame": e})
        expect = e
    if expect != frame_count:
        raise ValueError(f"shots cover {expect} frames, video has {frame_count}")
    return out


def detect_scene_list(video_path: str, cfg: Config) -> tuple[list[tuple[int, int]], int, str]:
    """Runs ContentDetector with exactly the frozen parameters. frame_skip=0: every frame."""
    import scenedetect
    from scenedetect import ContentDetector, SceneManager, open_video

    video = open_video(video_path)
    sm = SceneManager()
    sm.add_detector(ContentDetector(threshold=cfg["SHOT_CONTENT_THRESHOLD"],
                                    min_scene_len=cfg["SHOT_MIN_SCENE_FRAMES"], luma_only=False))
    processed = sm.detect_scenes(video, frame_skip=0, show_progress=False)
    scenes = [(a.frame_num, b.frame_num) for a, b in sm.get_scene_list(start_in_scene=True)]
    return scenes, int(processed), scenedetect.__version__


def compute_shot_map(video_path: str, *, fps: float, expected_frame_count: int, cfg: Config) -> dict[str, Any]:
    scenes, processed, version = detect_scene_list(video_path, cfg)
    if processed != expected_frame_count:
        raise ValueError(f"decoded {processed} frames but media_manifest says {expected_frame_count}; refusing to continue")
    return {
        "detector_id": "scenedetect.ContentDetector", "detector_version": version,
        "threshold": cfg["SHOT_CONTENT_THRESHOLD"], "min_scene_len_frames": cfg["SHOT_MIN_SCENE_FRAMES"],
        "luma_only": False, "normalized_source_fps": fps, "frame_count": processed,
        "duration_ms": frame_to_ms(processed, fps),
        "shots": shots_from_scene_list(scenes, processed, fps), "missing_reason": None,
    }
