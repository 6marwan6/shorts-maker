"""Phase 0 unit tests: config@1 canonicalization/hashing (impl plan 0.5, 0.9)."""
import json
from pathlib import Path

import pytest
from shorts_config import canonical_json, load_config
from shorts_config.registry import ConfigSpecGap

REPO = Path(__file__).resolve().parents[2]


def test_config_canonicalization_is_stable():
    obj = {"b": 1, "a": [3, 2, 1], "c": {"z": 1, "y": 2}}
    obj_reordered = {"c": {"y": 2, "z": 1}, "a": [3, 2, 1], "b": 1}
    assert canonical_json(obj) == canonical_json(obj_reordered)


def test_config_sha256_is_stable():
    cfg1 = load_config()
    cfg2 = load_config()
    assert cfg1.config_sha256 == cfg2.config_sha256
    assert len(cfg1.config_sha256) == 64


def test_config_sha256_changes_on_content_change():
    raw = json.loads((REPO / "packages/config/config@1.json").read_text())
    from shorts_config.registry import Config
    base = Config(raw)
    mutated = json.loads(json.dumps(raw))
    mutated["constants"]["JUDGE_MIN_WORDS"] = 26
    changed = Config(mutated)
    assert base.config_sha256 != changed.config_sha256


def test_config_version_is_config_at_1():
    cfg = load_config()
    assert cfg.config_version == "config@1"


def test_unknown_constant_raises_spec_gap_not_silent_default():
    cfg = load_config()
    with pytest.raises(ConfigSpecGap):
        cfg["DOES_NOT_EXIST_CONSTANT"]


def test_known_constants_match_implementation_plan_2_1():
    cfg = load_config()
    assert cfg["MAX_COMPRESSION_RATIO"] == 4.0
    assert cfg["STUDY_MAX_RATIO"] == 8.0
    assert cfg["MAX_REGION_S"] == 240
    assert cfg["JUDGE_MIN_WORDS"] == 25
    assert cfg["T4_BASE_PAIRS"] == 400
    assert cfg["T4_SEALED_PAIRS"] == 160
    assert cfg["CAPTION_MAX_CHARS_PER_LINE"] == 32
    assert cfg["MMR_LAMBDA"] == 0.7


def test_max_single_idea_region_s_derivation():
    # v5.0 2.36.3: MAX_SINGLE_IDEA_REGION_S = min(1.25 * 240, 360) = 300
    cfg = load_config()
    assert cfg["MAX_SINGLE_IDEA_REGION_S"] == 300


def test_effective_max_compression_ratio_toggles_with_study_mode():
    cfg = load_config()
    assert cfg["STUDY_MODE"] is False
    assert cfg.effective_max_compression_ratio == cfg["MAX_COMPRESSION_RATIO"]


def test_t1_and_t2_weights_sum_to_one():
    cfg = load_config()
    assert abs(sum(cfg["T1_WEIGHTS"].values()) - 1.0) < 1e-9
    assert abs(sum(cfg["T2_WEIGHTS"].values()) - 1.0) < 1e-9


def test_judge_call_budget_consistent():
    cfg = load_config()
    assert cfg["MAX_JUDGE_CALLS_PER_REGION"] >= cfg["MAX_PLANS_PER_REGION"] * cfg["MAX_JUDGE_CALLS_PER_PLAN"]


def test_youtube_shorts_profile_matches_2_2():
    cfg = load_config()
    p = cfg.profile("youtube_shorts")
    assert p["min_s"] == 8
    assert tuple(p["primary_range_s"]) == (20, 60)
    assert tuple(p["extended_range_s"]) == (60, 120)
    assert p["max_s"] == 180


def test_non_youtube_profiles_disabled_pending_verification():
    # impl plan 2.2: "do not use non-YouTube profiles in production until max_s is verified"
    cfg = load_config()
    with pytest.raises(ValueError):
        cfg.profile("tiktok_default")
    with pytest.raises(ValueError):
        cfg.profile("instagram_reels_default")
