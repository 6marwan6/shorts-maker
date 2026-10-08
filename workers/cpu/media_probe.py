"""ffprobe wrapper + source validation (impl plan Phase 2 §2.1, §2.4).

`ProbeResult` is an INTERNAL value object. It is NOT the media_manifest schema: that schema is
BLOCKED_BY_SPEC pending an owner field-level contract (2026-09-28). Frame rates are kept as the
raw ffprobe rational strings on purpose; the manifest's fps representation is an owner decision."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from workers.shared.failures import FailureKind, StageFailure


@dataclass(frozen=True)
class VideoStreamInfo:
    codec: str
    width: int            # as stored (coded) -- before applying rotation
    height: int
    pix_fmt: str | None
    r_frame_rate: str     # raw ffprobe rational, e.g. "24/1"
    avg_frame_rate: str
    rotation_deg: int     # clockwise degrees needed to display upright, in {0, 90, 180, 270}

    @property
    def display_width(self) -> int:
        return self.height if self.rotation_deg in (90, 270) else self.width

    @property
    def display_height(self) -> int:
        return self.width if self.rotation_deg in (90, 270) else self.height


@dataclass(frozen=True)
class AudioStreamInfo:
    codec: str
    sample_rate: int
    channels: int


@dataclass(frozen=True)
class ProbeResult:
    duration_s: float
    size_bytes: int | None
    video: VideoStreamInfo | None
    audio: AudioStreamInfo | None

    @property
    def has_audio(self) -> bool:
        return self.audio is not None


def _rotation(stream: dict) -> int:
    tag = (stream.get("tags") or {}).get("rotate")
    if tag is not None:
        return int(float(tag)) % 360
    for sd in stream.get("side_data_list") or []:
        if "rotation" in sd:
            # displaymatrix rotation is counter-clockwise degrees -> clockwise = negate.
            return round(-float(sd["rotation"])) % 360
    return 0


def parse_ffprobe_json(doc: dict) -> ProbeResult:
    streams = doc.get("streams") or []
    v = next((s for s in streams if s.get("codec_type") == "video"
              and not (s.get("disposition") or {}).get("attached_pic")), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    fmt = doc.get("format") or {}
    dur = fmt.get("duration") or (v or {}).get("duration") or 0
    size = fmt.get("size")
    return ProbeResult(
        duration_s=float(dur),
        size_bytes=int(size) if size is not None else None,
        video=None if v is None else VideoStreamInfo(
            codec=v.get("codec_name", ""), width=int(v["width"]), height=int(v["height"]),
            pix_fmt=v.get("pix_fmt"), r_frame_rate=v.get("r_frame_rate", "0/0"),
            avg_frame_rate=v.get("avg_frame_rate", "0/0"), rotation_deg=_rotation(v)),
        audio=None if a is None else AudioStreamInfo(
            codec=a.get("codec_name", ""), sample_rate=int(a.get("sample_rate") or 0),
            channels=int(a.get("channels") or 0)),
    )


def probe_media(path: str | Path) -> ProbeResult:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-of", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        raise StageFailure(FailureKind.PERMANENT_INPUT, "unreadable_media", proc.stderr.strip()[:500])
    return parse_ffprobe_json(json.loads(proc.stdout))


def validate_source(probe: ProbeResult, *, max_duration_s: float) -> None:
    """§2.4: reject duration <= 0 or > MAX_SOURCE_DURATION_S. A missing video stream cannot be
    normalized to H.264 at all, so it is also PERMANENT_INPUT. A missing AUDIO stream is NOT a
    rejection (owner decision 2026-09-28: the zero-speech/event-led path must stay reachable)."""
    if probe.video is None:
        raise StageFailure(FailureKind.PERMANENT_INPUT, "no_video_stream")
    if probe.duration_s <= 0:
        raise StageFailure(FailureKind.PERMANENT_INPUT, "duration_not_positive")
    if probe.duration_s > max_duration_s:
        raise StageFailure(FailureKind.PERMANENT_INPUT, "duration_exceeded",
                           f"{probe.duration_s:.1f}s > {max_duration_s}s")
