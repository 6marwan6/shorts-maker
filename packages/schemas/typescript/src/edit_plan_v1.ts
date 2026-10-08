// AUTO-GENERATED from packages/schemas/json/edit_plan_v1.schema.json by packages/schemas/typescript/scripts/gen-types.mjs
// Do not hand-edit -- edit the JSON Schema and regenerate (impl plan 0.4 / 4.3).

/**
 * v5.0 2.36.8.9, literal JSON example plus surrounding prose. Provisional/raw plan artifact produced by edit-plan generation, BEFORE verification. After verification the authoritative artifact is verified_edit_plan_v1 (2.36.9.8a) -- nothing downstream of verification reads this raw form for content/timing (impl plan 3.6). opening_unit_id/completion_unit_id allow null: the literal 2.36.8.9 example shows only "U3"/"U27" with no null variant, but the parallel verified_edit_plan_v1 example (2.36.9.8a) explicitly types these "U3 | null"/"U27 | null", and 2.36.8.5 scopes forced-opening/completion selection to speech-led balanced/aggressive plans only -- event-led (single-interval, trim-only, 2.36.8.3) plans have no super-unit opening selection. null is therefore allowed here too, inferred from that parallel rather than stated literally for this exact artifact -- flagged per this repo convention (see super_unit.schema.json).
 */
export interface EditPlanV1 {
  edit_plan_id: string;
  source_region_id: string;
  lineage_id: string;
  plan_origin: "model" | "user_edit";
  parent_edit_plan_id: string | null;
  replaces_short_candidate_id: string | null;
  schema_version: 1;
  stage_version: "edit_plan_gen@1";
  config_version: string;
  config_sha256: string;
  study_mode: boolean;
  evaluation_mode: boolean;
  effective_max_compression_ratio: number;
  export_profile_id: string;
  export_profile_sha256: string;
  content_style_id: string;
  intensity: "minimal" | "balanced" | "aggressive" | "study_ratio" | "user_edit";
  study_target_ratio: number | null;
  duration_profile: "primary" | "extended";
  opening_unit_id: string | null;
  completion_unit_id: string | null;
  retained_intervals: IntervalWithUnits[];
  deleted_spans: IntervalWithUnits[];
  cuts: {
    cut_id: string;
    cut_index: number;
    before_unit_id: string;
    after_unit_id: string;
    removed_unit_ids: string[];
  }[];
  /**
   * Items: type is const pause_shorten: 2.36.8.8 scopes MVP micro-edits to pause shortening only.
   */
  micro_edits: {
    type: "pause_shorten";
    start_ms: number;
    end_ms: number;
  }[];
  /**
   * 2.36.8.8 prose: "recorded in skipped_micro_edits with its reason" -- no literal item shape given anywhere in v5.0. Left open (not closed) rather than inventing a field list, matching this repo convention for underspecified shapes (see boundary_event.schema.json).
   */
  skipped_micro_edits: {}[];
  cleanup: {
    mode: "pause_shortening_only" | "none";
    d_clean_ms: number;
    minimal_cleanup_ratio_cap: number;
    savings_ms: number;
    applied_micro_edit_count: number;
  };
  dp_duration_ms: number;
  final_duration_ms: number;
  source_region_duration_ms: number;
  compression_ratio: number;
  compression_band: "standard" | "strict";
  interval_count: number;
  objective_value: number;
  short_hook: {
    score: number;
    type: "question" | "number" | "claim" | "none";
    text: string;
  };
  crossfades: {
    at_ms: number;
    type: "audio";
    duration_ms: number;
    provisional: boolean;
  }[];
  region_kind: "speech_led" | "event_led";
  timeline: {
    output_segment_id: string;
    source_start_ms: number;
    source_end_ms: number;
    output_start_ms: number;
    output_end_ms: number;
    speed_factor: 1;
  }[];
  /**
   * 2.36.8.9: null for speech-led plans; for event-led plans one of two literal shapes (settle_source=detected with settle_ms set and capped_end_ms null, or settle_source=capped with settle_ms null and capped_end_ms set).
   */
  event: {
    onset_ms: number;
    settle_ms: number | null;
    settle_source: "detected" | "capped";
    capped_end_ms: number | null;
    start_is_nearest_safe_before_onset: boolean;
  } | null;
  /**
   * 2.24/2.36.8.9: the raw Edit Plan reframe field always stays null; the reframer writes its own separate reframe_plan_v1 artifact after verification.
   */
  reframe: null;
  reject_reason: string | null;
}
export interface IntervalWithUnits {
  start_ms: number;
  end_ms: number;
  unit_ids: string[];
}
