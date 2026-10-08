"""Regression tests from the 2026-09-23 constant-reconciliation audit (decisions 1, 6, 7)."""
import pytest
from shorts_config import ConfigNotYetCalibrated, load_config


def test_region_budget_floor_cap_values_from_table_2_36_7():
    cfg = load_config()
    assert (cfg["R_DISC_FLOOR"], cfg["R_DISC_CAP"]) == (6, 90)
    assert (cfg["R_T1_FLOOR"], cfg["R_T1_CAP"]) == (4, 40)
    assert (cfg["R_EDIT_FLOOR"], cfg["R_EDIT_CAP"]) == (3, 25)


def test_min_final_duration_s_default_from_2_36_10():
    cfg = load_config()
    assert cfg["MIN_FINAL_DURATION_S_DEFAULT"] == 8
    # distinct from source-region discovery/qualification minimums (2.36.10 explicitly
    # keeps these three separate even though the default final duration equals youtube_shorts min_s)
    assert cfg["MIN_REGION_SPEECH"] == 10
    assert cfg["MIN_REGION_EVENT"] == 6


def test_evaluation_mode_default_false():
    cfg = load_config()
    assert cfg["EVALUATION_MODE"] is False


def test_cont_min_has_no_initial_value_and_cannot_be_silently_defaulted():
    # v5.0 2.36.6: "CONT_MIN is set from data instead of a guess" -- no initial number exists.
    cfg = load_config()
    with pytest.raises(ConfigNotYetCalibrated):
        cfg["CONT_MIN"]


def test_runtime_model_slots_resolve_to_fixed_impl_plan_models():
    cfg = load_config()
    assert cfg.runtime_model("JUDGE_MODEL") == "deepseek-v4-pro"
    assert cfg.runtime_model("STYLE_MODEL") == "kimi-k3"
    assert cfg.runtime_model("HOOK_MODEL") == "kimi-k3"


def test_no_automatic_model_fallback_exists_in_registry():
    # impl plan 1.11: "Do not automatically switch providers after an error."
    # Enforced by having exactly one fixed value per slot with no alternate/fallback key.
    cfg = load_config()
    raw = cfg._raw["runtime_model_slots"]
    for slot in ("JUDGE_MODEL", "STYLE_MODEL", "HOOK_MODEL"):
        assert set(raw[slot].keys()) == {"value", "source"}
