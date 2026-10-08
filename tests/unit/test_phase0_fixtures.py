"""Phase 0.9 fixture tests: every committed media fixture matches its ground-truth manifest,
and every scenario fixture is valid JSON referencing a real media file where applicable."""
import itertools
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MEDIA_DIR = ROOT / "packages/fixtures/media"
SCENARIO_DIR = ROOT / "packages/fixtures/scenarios"

_FFPROBE = shutil.which("ffprobe")
pytestmark = pytest.mark.skipif(_FFPROBE is None, reason="ffprobe not installed")

REQUIRED_MEDIA_FIXTURES = [
    "fixture_speech_45s.mp4",
    "fixture_speech_lt25words.mp4",
    "fixture_event_6_8s.mp4",
    "fixture_multi_speaker.mp4",
    "fixture_screen_content.mp4",
]

REQUIRED_SCENARIO_FIXTURES = [
    "no_diarization_path.json",
    "llm_transport_error_path.json",
    "llm_invalid_output_path.json",
    "study_ratio_generation.json",
    "user_edit_rejection.json",
]


def _probe_duration_s(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


@pytest.mark.parametrize("name", REQUIRED_MEDIA_FIXTURES)
def test_media_fixture_exists(name):
    assert (MEDIA_DIR / name).is_file()


@pytest.mark.parametrize("name", REQUIRED_MEDIA_FIXTURES)
def test_media_fixture_has_ground_truth(name):
    gt_path = MEDIA_DIR / (name.replace(".mp4", ".ground_truth.json"))
    assert gt_path.is_file(), f"missing {gt_path.name}"
    gt = json.loads(gt_path.read_bytes())
    assert gt["media_fixture"] == name


@pytest.mark.parametrize("name", REQUIRED_MEDIA_FIXTURES)
def test_media_fixture_duration_matches_ground_truth(name):
    gt = json.loads((MEDIA_DIR / name.replace(".mp4", ".ground_truth.json")).read_bytes())
    actual = _probe_duration_s(MEDIA_DIR / name)
    assert actual == pytest.approx(gt["duration_s"], abs=0.05)


@pytest.mark.parametrize("name", REQUIRED_MEDIA_FIXTURES)
def test_media_fixture_has_video_and_audio_streams(name):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(MEDIA_DIR / name)],
        capture_output=True, text=True, check=True,
    )
    stream_types = set(out.stdout.split())
    assert stream_types == {"video", "audio"}


def test_speech_fixture_word_count_matches_transcript():
    gt = json.loads((MEDIA_DIR / "fixture_speech_45s.ground_truth.json").read_bytes())
    assert len(gt["exact_transcript"].split()) == gt["word_count"] == 144


def test_short_speech_fixture_is_below_judge_min_words():
    gt = json.loads((MEDIA_DIR / "fixture_speech_lt25words.ground_truth.json").read_bytes())
    assert gt["word_count"] < 25


def test_event_fixture_segments_sum_to_duration():
    gt = json.loads((MEDIA_DIR / "fixture_event_6_8s.ground_truth.json").read_bytes())
    segs = gt["segments"]
    assert segs[0]["start_s"] == 0.0
    assert segs[-1]["end_s"] == pytest.approx(gt["duration_s"])
    for a, b in itertools.pairwise(segs):
        assert a["end_s"] == b["start_s"]


def test_multi_speaker_fixture_has_two_speakers_and_turns_are_contiguous_with_gaps():
    gt = json.loads((MEDIA_DIR / "fixture_multi_speaker.ground_truth.json").read_bytes())
    assert gt["speaker_count"] == 2
    turns = gt["turns"]
    speakers = {t["speaker"] for t in turns}
    assert speakers == {"A", "B"}
    for a, b in itertools.pairwise(turns):
        assert b["start_s"] > a["end_s"]  # a real gap between every turn


def test_screen_content_fixture_rectangle_within_detector_acceptance_bounds():
    gt = json.loads((MEDIA_DIR / "fixture_screen_content.ground_truth.json").read_bytes())
    rect = gt["screen_rectangle"]
    assert 0.10 <= rect["area_fraction_of_frame"] <= 0.95
    assert 0.60 <= rect["aspect_ratio"] <= 2.50


@pytest.mark.parametrize("name", REQUIRED_SCENARIO_FIXTURES)
def test_scenario_fixture_is_valid_json(name):
    data = json.loads((SCENARIO_DIR / name).read_bytes())
    assert "scenario_id" in data
    assert "description" in data


def test_no_diarization_scenario_references_a_real_media_fixture():
    data = json.loads((SCENARIO_DIR / "no_diarization_path.json").read_bytes())
    media_rel = data["media_fixture"]
    assert (ROOT / "packages/fixtures" / media_rel).is_file()


def test_all_ten_task_0_9_items_are_covered():
    covered = set()
    for name in REQUIRED_MEDIA_FIXTURES:
        gt = json.loads((MEDIA_DIR / name.replace(".mp4", ".ground_truth.json")).read_bytes())
        covered.add(gt["satisfies_task_0_9_item"])
    scenario_items = {
        "no_diarization_path.json": "no-diarization path",
        "llm_transport_error_path.json": "transport-error LLM path",
        "llm_invalid_output_path.json": "invalid-output LLM path",
        "study_ratio_generation.json": "study-ratio generation",
        "user_edit_rejection.json": "user-edit rejection",
    }
    covered.update(scenario_items.values())
    expected = {
        "speech-led >= 25 words", "speech-led < 25 words", "6-8s event-led candidate",
        "multi-speaker reframe", "screen-content reframe", "no-diarization path",
        "transport-error LLM path", "invalid-output LLM path", "study-ratio generation",
        "user-edit rejection",
    }
    assert covered == expected
