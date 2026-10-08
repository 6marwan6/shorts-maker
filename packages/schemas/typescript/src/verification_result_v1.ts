// AUTO-GENERATED from packages/schemas/json/verification_result_v1.schema.json by packages/schemas/typescript/scripts/gen-types.mjs
// Do not hand-edit -- edit the JSON Schema and regenerate (impl plan 0.4 / 4.3).

/**
 * v5.0 2.36.9.8. Named 'Verification artifact (schema v1)' in prose with no artifact-type name given; filename/title verification_result_v1 chosen consistent with impl plan's own phrase 'the verification-result artifact (2.36.9.8)' and this file's own id field (verification_id) and stage_version (verifier@2). normalized_issues items are an INFERENCE: the literal top-level example only shows an empty array, but 2.36.9.3's normalization procedure explicitly states 'cut_index values are first resolved to cut_id' and issues are 'deduplicated by (location, cut_id, type)', so the post-normalization item shape is the raw verifier_output@1 issue shape (2.36.9.3) with cut_index replaced by cut_id -- well-grounded but flagged per this repo convention.
 */
export interface VerificationResultV1 {
  verification_id: string;
  edit_plan_id: string;
  lineage_id: string;
  schema_version: 1;
  stage_version: "verifier@2";
  verdict_code_version: "verdict@1";
  config_version: string;
  config_sha256: string;
  study_mode: boolean;
  evaluation_mode: boolean;
  effective_max_compression_ratio: number;
  layer1: {
    passed: boolean;
    /**
     * L1_* codes from 2.36.9.2, e.g. L1_SCHEMA, L1_ORDER, L1_CUT_IN_SPEECH, L1_AUDIO_JOIN, L1_EVENT_BOUNDARY_UNSAFE.
     */
    failures: string[];
    /**
     * e.g. loudness_step_xfade (2.36.9.2), settle_capped (2.36.9.2 L1_EVENT_SETTLE_MISSING check).
     */
    warnings: string[];
    audio_joins: {
      cut_id: string;
      tail_gap_ms: number;
      head_gap_ms: number;
      nonspeech_tail_ms: number;
      nonspeech_head_ms: number;
      normal_crossfade_available: boolean;
      extended_crossfade_available: boolean;
      speech_overlap_allowed: false;
      loudness_step_db: number;
      crossfade_ms: number;
      applied_crossfade_ms: number;
    }[];
  };
  judge_calls: {
    call_index: number;
    plan_id_judged: string;
    prompt_version: "verifier_prompt@2";
    model_id: string;
    temperature: 0;
    judge_validation_version: "validate_judge_semantics@1";
    normalized_input_sha256: string;
    transcript_sha256: string;
    normalized_input_ref: string;
    cut_map: {
      cut_index: number;
      cut_id: string;
    }[];
    raw_output: {};
    valid: boolean;
    normalized_issues: {
      location: "cut" | "opening" | "ending";
      cut_id: string | null;
      type:
        | "dangling_reference"
        | "missing_setup"
        | "non_sequitur"
        | "abrupt_end"
        | "topic_jump"
        | "opening_dependent"
        | "other";
      severity: "minor" | "major";
      evidence: string;
    }[];
    judged_band: "standard" | "strict";
    verdict: "PASS" | "REPAIRABLE" | "HARD_FAIL";
  }[];
  repair: {
    applied_ops: {
      op: "R1" | "R2";
      cut_id: string;
      restored_unit_ids: string[];
      /**
       * 2.36.9.6: when restoring r closes the cut completely the bridge test 'passes automatically' without computing the cosine-similarity formulas, so the numeric fields are nullable (not shown nullable in the literal top-level example, but implied by that prose).
       */
      bridge: {
        S_cur: number | null;
        S_in: number | null;
        S_out: number | null;
        S_new: number | null;
        T_r: number | null;
        closed_cut: boolean;
        passed: boolean;
      };
    }[];
    /**
     * 2.36.9.6: an operation whose cut_id no longer exists is 'skipped and recorded as stale_target'; no literal item shape given.
     */
    stale_targets: {}[];
    repair_insufficient: boolean;
    repaired_plan_id: string | null;
    result: "judged" | "repair_infeasible" | "repair_duplicate" | "repair_unfunded" | null;
  };
  origin_intensity: "minimal" | "balanced" | "aggressive" | "study_ratio" | "user_edit";
  origin_band: "standard" | "strict";
  judged_band: "standard" | "strict";
  final_status: "TRANSCRIPT_VERIFIED_PASS" | "LAYER1_ONLY_PASS" | "FAIL";
  verification_scope: "speech_judged" | "event_layer1_only";
  semantic_validation: "passed" | "failed" | "skipped";
  semantic_judge_status: "JUDGED" | "SKIPPED_LOW_TRANSCRIPT";
  human_validation_required: boolean;
  selection_policy: "verify_all";
  /**
   * e.g. minimal, balanced, aggressive, study_ratio:4.5 ... study_ratio:8.0 (2.36.9.5 PLAN_VERIFY_ORDER).
   */
  verify_order: string[];
  verified_edit_plan_id: string | null;
  /**
   * L1_* prefix codes (2.36.9.2) plus fixed literal values from 2.36.9.8.
   */
  fail_reason: string | null;
  tier2_features: {
    coherence_min: number;
    coherence_mean: number;
    issue_count_minor: number;
    repair_applied: boolean;
    judged_band: "standard" | "strict";
    unjudged: boolean;
  };
}
