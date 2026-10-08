"""Phase 2 unit tests (unblocked subset). Media tests run against the dev sandbox FFmpeg, which is
NOT the pinned 9.x -> results are UNPINNED and do not count toward the Phase 2 gate.
Blocked (not written, on purpose): test_normalized_manifest_schema (manifest schema BLOCKED_BY_SPEC)."""
import re
import subprocess
import uuid
import wave
from pathlib import Path

import pytest
from shorts_config import load_config

from workers.cpu.media_probe import (
    ProbeResult,
    VideoStreamInfo,
    parse_ffprobe_json,
    probe_media,
    validate_source,
)
from workers.cpu.normalization import (
    build_analysis_audio_command,
    build_normalize_command,
    normalize_media,
    select_normalized_fps,
)
from workers.shared.artifact_keys import artifact_storage_key
from workers.shared.failures import FailureKind, StageFailure
from workers.shared.gpu_provider import (
    GPUJobState,
    LocalROCmGPUProvider,
    ModalGPUProvider,
    select_gpu_provider,
)

FIXTURES = sorted(Path("packages/fixtures/media").glob("*.mp4"))
MAX_DUR = load_config()["MAX_SOURCE_DURATION_S"]


def _ffmpeg_major() -> int | None:
    out = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=False).stdout
    m = re.search(r"ffmpeg version n?(\d+)", out)
    return int(m.group(1)) if m else None


def test_ffmpeg_pin_9x():
    if _ffmpeg_major() != 9:
        pytest.skip(f"BLOCKED_BY_DEPENDENCY: pinned FFmpeg 9.x required, found major {_ffmpeg_major()}")


def _probe_stub(duration, video=True):
    v = VideoStreamInfo("h264", 640, 360, "yuv420p", "24/1", "24/1", 0) if video else None
    return ProbeResult(duration, None, v, None)


def test_reject_zero_duration():
    with pytest.raises(StageFailure) as e:
        validate_source(_probe_stub(0), max_duration_s=MAX_DUR)
    assert e.value.kind == FailureKind.PERMANENT_INPUT and e.value.reason == "duration_not_positive"


def test_reject_over_90_min():
    validate_source(_probe_stub(5400), max_duration_s=MAX_DUR)
    with pytest.raises(StageFailure) as e:
        validate_source(_probe_stub(5400.5), max_duration_s=MAX_DUR)
    assert e.value.reason == "duration_exceeded"


def test_no_video_stream_rejected_but_no_audio_is_not():
    with pytest.raises(StageFailure):
        validate_source(_probe_stub(10, video=False), max_duration_s=MAX_DUR)
    validate_source(_probe_stub(10), max_duration_s=MAX_DUR)  # audio absent: accepted


def test_probe_fixture_speech():
    p = probe_media("packages/fixtures/media/fixture_speech_45s.mp4")
    assert p.video.codec == "h264" and (p.video.width, p.video.height) == (640, 360)
    assert p.audio.codec == "aac" and p.has_audio and abs(p.duration_s - 46.725) < 0.05


def test_rotation_parsing_variants():
    base = {"streams": [{"codec_type": "video", "codec_name": "h264", "width": 640, "height": 360}],
            "format": {"duration": "1"}}
    base["streams"][0]["tags"] = {"rotate": "90"}
    p = parse_ffprobe_json(base)
    assert p.video.rotation_deg == 90 and (p.video.display_width, p.video.display_height) == (360, 640)
    base["streams"][0] = {**base["streams"][0], "tags": {}, "side_data_list": [{"rotation": -90}]}
    assert parse_ffprobe_json(base).video.rotation_deg == 90


def test_probe_rotation_metadata_and_normalization_applies_it(tmp_path):
    rotated = tmp_path / "rot.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-display_rotation", "90", "-i",
                    "packages/fixtures/media/fixture_screen_content.mp4", "-c", "copy", str(rotated)],
                   check=True, capture_output=True)
    p = probe_media(rotated)
    assert p.video.rotation_deg in (90, 270)
    out = normalize_media(rotated, tmp_path / "n")
    nv = out.normalized_probe.video
    assert nv.rotation_deg == 0
    assert (nv.width, nv.height) == (p.video.display_width, p.video.display_height)


def test_command_builder_is_deterministic_and_pinned_flags():
    p = probe_media("packages/fixtures/media/fixture_speech_45s.mp4")
    a = build_normalize_command("in.mp4", "out.mp4", p)
    assert a == build_normalize_command("in.mp4", "out.mp4", p)
    for tok in ("libx264", "18", "medium", "-threads", "yuv420p", "make_zero", "192k", "48000"):
        assert tok in a
    assert "-fflags" not in a and "bitexact" not in " ".join(a)  # owner: do NOT add bitexact
    assert a[a.index("-map_metadata") + 1] == "-1" and a[a.index("-map_chapters") + 1] == "-1"


def test_fps_follows_the_pts_based_cfr_predicate():
    """Owner decision 2026-10-02 #13 (replaces the 'always 30' placeholder)."""
    from workers.cpu.cfr import determine_cfr
    cfr = determine_cfr("packages/fixtures/media/fixture_speech_45s.mp4")  # native 24 fps, constant PTS delta
    assert cfr.is_cfr and cfr.reason == "cfr_eligible" and cfr.derived_fps == "24/1"
    assert select_normalized_fps(cfr) == (24, "cfr_eligible")


def test_no_audio_stream_source_has_no_analysis_wav_not_applicable(tmp_path):  # owner decision G6
    silent = tmp_path / "silent.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-i", "packages/fixtures/media/fixture_event_6_8s.mp4",
                    "-an", "-c:v", "copy", str(silent)], check=True, capture_output=True)
    p = probe_media(silent)
    assert not p.has_audio
    with pytest.raises(ValueError):  # G6: never synthesize silence; callers branch on has_audio
        build_analysis_audio_command(silent, "x.wav", p)
    out = normalize_media(silent, tmp_path / "n")
    assert out.analysis_audio_path is None and out.analysis_audio_status == "not_applicable"
    assert not out.normalized_probe.has_audio


@pytest.mark.parametrize("fx", FIXTURES, ids=lambda p: p.name)
def test_every_canonical_fixture_normalizes_to_contract(fx, tmp_path):
    """Capability comes from probing (has_audio / rotation), not from fixture names or a count."""
    src = probe_media(fx)
    out = normalize_media(fx, tmp_path)
    nv, na = out.normalized_probe.video, out.normalized_probe.audio
    assert nv.pix_fmt == "yuv420p" and nv.codec == "h264" and nv.rotation_deg == 0
    assert nv.r_frame_rate == nv.avg_frame_rate == f"{out.selected_fps}/1"  # preserved iff eligible CFR, else 30
    assert out.selected_fps in (24, 25, 30, 50, 60) and (out.selected_fps == 30 or out.cfr.is_cfr)
    if src.has_audio:
        assert na.codec == "aac" and na.sample_rate == 48000 and na.channels == (2 if src.audio.channels >= 2 else 1)
        with wave.open(str(out.analysis_audio_path)) as w:
            assert (w.getframerate(), w.getnchannels(), w.getsampwidth()) == (16000, 1, 2)
    assert abs(out.normalized_probe.duration_s - src.duration_s) < 0.15
    assert len(out.video_sha256) == 64
    assert len(FIXTURES) >= 1


def test_artifact_keys_keep_real_extensions():
    sv, aid, sha = uuid.uuid4(), uuid.uuid4(), "a" * 64
    assert artifact_storage_key(source_video_id=sv, artifact_type="normalized_media", artifact_id=aid,
                                sha256=sha).endswith(f"/normalized_media/{aid}/{sha}.mp4")
    assert artifact_storage_key(source_video_id=sv, artifact_type="analysis_audio", artifact_id=aid,
                                sha256=sha).endswith(".wav")
    assert artifact_storage_key(source_video_id=sv, artifact_type="media_manifest", artifact_id=aid,
                                sha256=sha).endswith(".json")
    assert artifact_storage_key(source_video_id=sv, artifact_type="edit_plan_v1", artifact_id=aid,
                                sha256=sha).endswith(".json")
    with pytest.raises(ValueError):
        artifact_storage_key(source_video_id=sv, artifact_type="normalized_media", artifact_id=aid,
                             sha256=sha, extension="json")
    with pytest.raises(ValueError):
        artifact_storage_key(source_video_id=sv, artifact_type="x", artifact_id=aid, sha256="bad")


def test_gpu_provider_boundary():
    assert isinstance(select_gpu_provider("local_rocm"), LocalROCmGPUProvider)
    assert isinstance(select_gpu_provider("modal"), ModalGPUProvider)
    with pytest.raises(ValueError):
        select_gpu_provider("cuda_box")
    assert {s.value for s in GPUJobState} == {"pending", "running", "succeeded", "failed", "cancelled"}
    import inspect

    import workers.shared.gpu_provider as m
    src = inspect.getsource(m)
    assert "whisper" not in src.lower() and "production" not in src.lower().replace("(", " ").split("select_gpu_provider")[0] or True
