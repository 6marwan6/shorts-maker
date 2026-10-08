"""Phase 0 unit tests: the 4 schemas added after Phase 0 sign-off (edit_plan_v1, verified_edit_plan_v1,
hook_analysis_v1, verification_result_v1) each validate a concrete instance transcribed from v5.0's
literal JSON examples (2.36.8.9, 2.36.9.8a, 2.37.8, 2.36.9.8). This is a stronger check than
test_phase0_schemas.py's generic meta-checks: it proves the schema actually accepts a realistic,
spec-shaped payload, not just that it is well-formed draft 2020-12 with the right identity fields.

Placeholder substitution rule applied uniformly: v5.0's "uuid" -> a real UUID4 string, "…" -> a
representative non-empty string, bare 0/0.0 -> a representative non-zero value where a more concrete
value is implied elsewhere in the spec (e.g. crossfade/join constants from 2.36.9.10), else left 0.
"""
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

REPO = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO / "packages/schemas/json"

UUID_A = "11111111-1111-4111-8111-111111111111"
UUID_B = "22222222-2222-4222-8222-222222222222"
UUID_C = "33333333-3333-4333-8333-333333333333"
UUID_D = "44444444-4444-4444-8444-444444444444"
UUID_E = "55555555-5555-4555-8555-555555555555"

CONFIG_SHA = "a" * 64


def _load(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_bytes())


EDIT_PLAN_EXAMPLE = {
    "edit_plan_id": UUID_A,
    "source_region_id": UUID_B,
    "lineage_id": UUID_C,
    "plan_origin": "model",
    "parent_edit_plan_id": None,
    "replaces_short_candidate_id": None,
    "schema_version": 1,
    "stage_version": "edit_plan_gen@1",
    "config_version": "config@1",
    "config_sha256": CONFIG_SHA,
    "study_mode": False,
    "evaluation_mode": False,
    "effective_max_compression_ratio": 4.0,
    "export_profile_id": "youtube_shorts",
    "export_profile_sha256": CONFIG_SHA,
    "content_style_id": UUID_D,
    "intensity": "balanced",
    "study_target_ratio": None,
    "duration_profile": "primary",
    "opening_unit_id": "U3",
    "completion_unit_id": "U27",
    "retained_intervals": [{"start_ms": 0, "end_ms": 5000, "unit_ids": ["U3", "U4"]}],
    "deleted_spans": [{"start_ms": 5000, "end_ms": 9000, "unit_ids": ["U5"]}],
    "cuts": [{"cut_id": "cut:U4>U9", "cut_index": 0, "before_unit_id": "U4", "after_unit_id": "U9",
              "removed_unit_ids": ["U5", "U6", "U7", "U8"]}],
    "micro_edits": [{"type": "pause_shorten", "start_ms": 1200, "end_ms": 1550}],
    "skipped_micro_edits": [],
    "cleanup": {"mode": "pause_shortening_only", "d_clean_ms": 42000,
                "minimal_cleanup_ratio_cap": 1.10, "savings_ms": 800, "applied_micro_edit_count": 2},
    "dp_duration_ms": 45000,
    "final_duration_ms": 45000,
    "source_region_duration_ms": 180000,
    "compression_ratio": 4.0,
    "compression_band": "standard",
    "interval_count": 2,
    "objective_value": 12.5,
    "short_hook": {"score": 0.8, "type": "question", "text": "Why does this always happen?"},
    "crossfades": [{"at_ms": 5000, "type": "audio", "duration_ms": 30, "provisional": True}],
    "region_kind": "speech_led",
    "timeline": [{"output_segment_id": UUID_E, "source_start_ms": 0, "source_end_ms": 5000,
                  "output_start_ms": 0, "output_end_ms": 5000, "speed_factor": 1.0}],
    "event": None,
    "reframe": None,
    "reject_reason": None,
}

EDIT_PLAN_EVENT_EXAMPLE = dict(EDIT_PLAN_EXAMPLE)
EDIT_PLAN_EVENT_EXAMPLE.update({
    "region_kind": "event_led",
    "intensity": "minimal",
    "opening_unit_id": None,
    "completion_unit_id": None,
    "event": {"onset_ms": 12000, "settle_ms": 15500, "settle_source": "detected",
              "capped_end_ms": None, "start_is_nearest_safe_before_onset": False},
})

VERIFIED_EDIT_PLAN_EXAMPLE = {
    "verified_edit_plan_id": UUID_A,
    "schema_version": 1,
    "stage_version": "verified_plan@1",
    "config_version": "config@1",
    "config_sha256": CONFIG_SHA,
    "study_mode": False,
    "evaluation_mode": False,
    "effective_max_compression_ratio": 4.0,
    "verification_id": UUID_B,
    "edit_plan_id": UUID_C,
    "source_region_id": UUID_D,
    "lineage_id": UUID_E,
    "plan_origin": "model",
    "parent_edit_plan_id": None,
    "replaces_short_candidate_id": None,
    "export_profile_id": "youtube_shorts",
    "export_profile_sha256": CONFIG_SHA,
    "final_status": "TRANSCRIPT_VERIFIED_PASS",
    "human_validation_required": False,
    "region_kind": "speech_led",
    "intensity": "balanced",
    "study_target_ratio": None,
    "retained_intervals": [{"start_ms": 0, "end_ms": 45000, "unit_ids": ["U3", "U4"]}],
    "cuts": [{"cut_id": "cut:U4>U9", "cut_index": 0, "before_unit_id": "U4", "after_unit_id": "U9",
              "removed_unit_ids": ["U5"]}],
    "micro_edits": [{"type": "pause_shorten", "start_ms": 1200, "end_ms": 1550}],
    "audio_joins": [{"cut_id": "cut:U4>U9", "tail_gap_ms": 40, "head_gap_ms": 40,
                      "nonspeech_tail_ms": 100, "nonspeech_head_ms": 100,
                      "normal_crossfade_available": True, "extended_crossfade_available": True,
                      "speech_overlap_allowed": False, "loudness_step_db": 1.2,
                      "crossfade_ms": 30, "applied_crossfade_ms": 30}],
    "crossfades": [{"at_ms": 5000, "type": "audio", "duration_ms": 30, "provisional": False}],
    "timeline": [{"output_segment_id": UUID_E, "source_start_ms": 0, "source_end_ms": 45000,
                  "output_start_ms": 0, "output_end_ms": 45000, "speed_factor": 1.0}],
    "final_duration_ms": 45000,
    "compression_ratio": 4.0,
    "compression_band": "standard",
    "duration_profile": "primary",
    "opening_unit_id": "U3",
    "completion_unit_id": "U27",
    "short_hook": {"score": 0.8, "type": "question", "text": "Why does this always happen?"},
    "content_style_id": UUID_D,
    "final_face_ratio": 0.6,
    "final_screen_ratio": 0.0,
    "final_visual_format": "talking_head",
    "event": None,
    "reframe": None,
}

HOOK_FEATURE = {"v": 900, "m": None}
HOOK_FEATURE_NULL = {"v": None, "m": "no_detection"}

HOOK_ANALYSIS_EXAMPLE = {
    "hook_analysis_id": UUID_A,
    "edit_plan_id": UUID_B,
    "schema_version": 1,
    "stage_version": "hook_analysis@1",
    "config_version": "config@1",
    "config_sha256": CONFIG_SHA,
    "language_code": "en",
    "region_kind": "speech_led",
    "verified_edit_plan_id": UUID_C,
    "llm_cache_key": "sha256:" + "b" * 64,
    "signal_cache_key": "sha256:" + "c" * 64,
    "timeline_ref": "verified_edit_plan_id#timeline",
    "text_window": {"sentence_ids": ["s1", "s2"], "word_count": 18, "over_max_words": False,
                     "under_min_words": False, "window_truncated_by_plan_end": False,
                     "text_sha256": "d" * 64},
    "signal_window_ms": 3000,
    "deterministic": {
        "extractor_version": "hook_signals@1",
        "first_content_ms": HOOK_FEATURE, "immediate_content_ratio": {"v": 0.7, "m": None},
        "info_density": {"v": 0.5, "m": None}, "first_question_ms": HOOK_FEATURE_NULL,
        "first_number_ms": HOOK_FEATURE_NULL, "first_claim_ms": HOOK_FEATURE_NULL,
        "cue_question": {"v": False, "m": "no_detection"}, "cue_number": {"v": False, "m": "no_detection"},
        "cue_claim_word": {"v": False, "m": "no_detection"}, "first_audio_event_ms": HOOK_FEATURE,
        "first_motion_ms": HOOK_FEATURE, "audio_onset_in_window": {"v": True, "m": None},
        "motion_in_window": {"v": 1.2, "m": None}, "cuts_in_window": {"v": 0, "m": None},
        "face_ratio_in_window": {"v": 0.9, "m": None}, "first_signal_ms": HOOK_FEATURE,
    },
    "from_verifier": {
        "verification_id": UUID_D, "verifier_stage_version": "verifier@2",
        "prompt_version": "verifier_prompt@2", "judge_call_index": 1,
        "opening_standalone_raw": 5, "context_independence": {"v": 1.0, "m": None},
        "requires_prior_context": {"v": False, "m": None},
    },
    "llm": {
        "prompt_version": "hook_prompt@1", "model_id": "kimi-k3", "temperature": 0,
        "hook_types": {"v": ["question"], "m": None}, "primary_hook_type": {"v": "question", "m": None},
        "type_confidence": {"v": 0.9, "m": None}, "curiosity_gap": {"v": 4, "m": None},
        "promise_clarity": {"v": 4, "m": None}, "emotional_intensity": {"v": 3, "m": None},
        "promise_sentence_index": 0, "promise_sentence_index_valid": True,
        "promise_established_ms": HOOK_FEATURE, "raw_output": {}, "valid": True,
    },
    "analysis_status": "complete",
}

VERIFICATION_RESULT_EXAMPLE = {
    "verification_id": UUID_A,
    "edit_plan_id": UUID_B,
    "lineage_id": UUID_C,
    "schema_version": 1,
    "stage_version": "verifier@2",
    "verdict_code_version": "verdict@1",
    "config_version": "config@1",
    "config_sha256": CONFIG_SHA,
    "study_mode": False,
    "evaluation_mode": False,
    "effective_max_compression_ratio": 4.0,
    "layer1": {"passed": True, "failures": [], "warnings": [], "audio_joins": [
        {"cut_id": "cut:U4>U9", "tail_gap_ms": 40, "head_gap_ms": 40, "nonspeech_tail_ms": 100,
         "nonspeech_head_ms": 100, "normal_crossfade_available": True,
         "extended_crossfade_available": True, "speech_overlap_allowed": False,
         "loudness_step_db": 1.2, "crossfade_ms": 30, "applied_crossfade_ms": 30}]},
    "judge_calls": [{
        "call_index": 1, "plan_id_judged": UUID_D, "prompt_version": "verifier_prompt@2",
        "model_id": "deepseek-v4-pro", "temperature": 0,
        "judge_validation_version": "validate_judge_semantics@1",
        "normalized_input_sha256": "e" * 64, "transcript_sha256": "f" * 64,
        "normalized_input_ref": "storage://artifacts/verifier_input.json",
        "cut_map": [{"cut_index": 0, "cut_id": "cut:U4>U9"}],
        "raw_output": {}, "valid": True, "normalized_issues": [],
        "judged_band": "standard", "verdict": "PASS",
    }],
    "repair": {"applied_ops": [], "stale_targets": [], "repair_insufficient": False,
               "repaired_plan_id": None, "result": None},
    "origin_intensity": "balanced",
    "origin_band": "standard",
    "judged_band": "standard",
    "final_status": "TRANSCRIPT_VERIFIED_PASS",
    "verification_scope": "speech_judged",
    "semantic_validation": "passed",
    "semantic_judge_status": "JUDGED",
    "human_validation_required": False,
    "selection_policy": "verify_all",
    "verify_order": ["minimal", "balanced", "aggressive"],
    "verified_edit_plan_id": UUID_E,
    "fail_reason": None,
    "tier2_features": {"coherence_min": 0.9, "coherence_mean": 0.94, "issue_count_minor": 0,
                        "repair_applied": False, "judged_band": "standard", "unjudged": False},
}


@pytest.mark.parametrize(
    "schema_file, instance",
    [
        ("edit_plan_v1.schema.json", EDIT_PLAN_EXAMPLE),
        ("edit_plan_v1.schema.json", EDIT_PLAN_EVENT_EXAMPLE),
        ("verified_edit_plan_v1.schema.json", VERIFIED_EDIT_PLAN_EXAMPLE),
        ("hook_analysis_v1.schema.json", HOOK_ANALYSIS_EXAMPLE),
        ("verification_result_v1.schema.json", VERIFICATION_RESULT_EXAMPLE),
    ],
    ids=["edit_plan_speech_led", "edit_plan_event_led", "verified_edit_plan",
         "hook_analysis", "verification_result"],
)
def test_literal_spec_shaped_instance_validates(schema_file, instance):
    schema = _load(schema_file)
    Draft202012Validator(schema).validate(instance)


def test_edit_plan_rejects_unknown_field():
    schema = _load("edit_plan_v1.schema.json")
    bad = dict(EDIT_PLAN_EXAMPLE)
    bad["not_a_real_field"] = True
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(bad)


def test_hook_analysis_llm_temperature_must_be_zero():
    # v5.0 2.37.3: hook LLM calls always run at temperature 0.
    schema = _load("hook_analysis_v1.schema.json")
    bad = json.loads(json.dumps(HOOK_ANALYSIS_EXAMPLE))
    bad["llm"]["temperature"] = 0.7
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(bad)
