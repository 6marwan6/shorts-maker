"""Deterministic FFmpeg normalization command construction + execution (impl plan Phase 2).

Fixed semantics (§2.2): libx264 CRF 18 preset medium, -threads 1, yuv420p, CFR, AAC 192k 48 kHz
(2 ch if source has >= 2 ch else 1), MP4, make_zero timestamps, metadata + chapters stripped.
NOT added (owner decision 2026-09-28): -fflags +bitexact.

Owner decisions 2026-09-30 / 2026-10-02: (G6) a source with no audio stream gets no synthesized
WAV; (#13) the normalized FPS comes from the PTS-based CFR predicate in workers.cpu.cfr
(24/25/30/50/60 preserved only for a strictly constant-delta source, else CFR 30); (#12)
media_manifest_v1 is written by stage_normalize.
Pinned FFmpeg 9.x is not available in the dev sandbox (BLOCKED_BY_DEPENDENCY for verification)."""
from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path

from workers.cpu.cfr import FALLBACK_FPS, CFRDecision, determine_cfr
from workers.cpu.media_probe import ProbeResult, probe_media
from workers.shared.failures import FailureKind, StageFailure


def select_normalized_fps(cfr: CFRDecision) -> tuple[int, str]:
    """(fps, reason) from the PTS-based CFR decision (owner decision #13)."""
    return cfr.selected_fps, cfr.reason


def normalized_audio_channels(probe: ProbeResult) -> int | None:
    if probe.audio is None:
        return None
    return 2 if probe.audio.channels >= 2 else 1


def build_normalize_command(
    src: str | Path, dst: str | Path, probe: ProbeResult, fps: int = FALLBACK_FPS,
) -> list[str]:
    cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-y", "-i", str(src), "-map", "0:v:0"]
    if probe.has_audio:
        cmd += ["-map", "0:a:0"]
    cmd += ["-map_metadata", "-1", "-map_chapters", "-1",
            "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-threads", "1",
            "-pix_fmt", "yuv420p", "-fps_mode", "cfr", "-r", str(fps)]
    if probe.has_audio:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-ac", str(normalized_audio_channels(probe))]
    cmd += ["-avoid_negative_ts", "make_zero", "-f", "mp4", str(dst)]
    return cmd


def build_analysis_audio_command(src: str | Path, dst: str | Path, probe: ProbeResult) -> list[str]:
    if not probe.has_audio:
        # Owner decision G6 (2026-09-30): a source with NO audio stream never gets a synthesized
        # silent WAV. Callers must branch on probe.has_audio; reaching here is a caller bug.
        raise ValueError("build_analysis_audio_command called for a source with no audio stream (G6)")
    return ["ffmpeg", "-nostdin", "-hide_banner", "-y", "-i", str(src), "-map", "0:a:0", "-vn",
            "-map_metadata", "-1", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", "-f", "wav",
            str(dst)]


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise StageFailure(FailureKind.PERMANENT_INPUT, "ffmpeg_failed", proc.stderr.strip()[-500:])


@dataclass(frozen=True)
class NormalizedMedia:
    video_path: Path
    video_sha256: str
    analysis_audio_path: Path | None
    analysis_audio_sha256: str | None
    analysis_audio_status: str  # "created" | "not_applicable" (owner decision G6: no audio stream)
    source_probe: ProbeResult
    normalized_probe: ProbeResult
    analysis_audio_probe: ProbeResult | None
    cfr: CFRDecision
    selected_fps: int
    fps_reason: str
    ffmpeg_argv: dict  # placeholders {src}/{dst}; recorded in media_manifest_v1 provenance


def _templated(cmd: list[str], src, dst) -> list[str]:
    return ["{src}" if c == str(src) else "{dst}" if c == str(dst) else c for c in cmd]


def normalize_media(src: str | Path, out_dir: str | Path, probe: ProbeResult | None = None) -> NormalizedMedia:
    probe = probe or probe_media(src)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cfr = determine_cfr(src)
    fps, fps_reason = select_normalized_fps(cfr)
    video = out / "normalized.mp4"
    vcmd = build_normalize_command(src, video, probe, fps)
    _run(vcmd)
    argv = {"normalize": _templated(vcmd, src, video)}
    audio: Path | None = None
    if probe.has_audio:
        audio = out / "analysis_audio.wav"
        acmd = build_analysis_audio_command(src, audio, probe)
        _run(acmd)
        argv["analysis_audio"] = _templated(acmd, src, audio)
    return NormalizedMedia(
        video_path=video, video_sha256=sha256_file(video),
        analysis_audio_path=audio, analysis_audio_sha256=sha256_file(audio) if audio else None,
        analysis_audio_status="created" if probe.has_audio else "not_applicable",
        source_probe=probe, normalized_probe=probe_media(video),
        analysis_audio_probe=probe_media(audio) if audio else None,
        cfr=cfr, selected_fps=fps, fps_reason=fps_reason, ffmpeg_argv=argv,
    )
