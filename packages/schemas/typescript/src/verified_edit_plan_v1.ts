// AUTO-GENERATED from packages/schemas/json/verified_edit_plan_v1.schema.json by packages/schemas/typescript/scripts/gen-types.mjs
// Do not hand-edit -- edit the JSON Schema and regenerate (impl plan 0.4 / 4.3).

/**
 * v5.0 2.36.9.8a. The single content/timeline/audio-join authority after verification (impl plan 3.6): every stage downstream of verification (hook analysis, reframe planning, Tier 2, review UI, captions, renderer) reads only this artifact, never the raw edit_plan_v1. Per 3.6 this artifact must NOT store downstream hook_analysis_id/reframe_plan_id/caption_plan_id -- those are Short Candidate/render dependencies recorded elsewhere (short_candidate_v1). reframe is always null here too (2.36.9.8a rule 2: 'a later reframe result is stored in its own artifact that references verified_edit_plan_id').
 */
export interface VerifiedEditPlanV1 {
  verified_edit_plan_id: string;
  schema_version: 1;
  stage_version: "verified_plan@1";
  config_version: string;
  config_sha256: string;
  study_mode: boolean;
  evaluation_mode: boolean;
  effective_max_compression_ratio: number;
  verification_id: string;
  edit_plan_id: string;
  source_region_id: string;
  lineage_id: string;
  plan_origin: "model" | "user_edit";
  parent_edit_plan_id: string | null;
  replaces_short_candidate_id: string | null;
  export_profile_id: string;
  export_profile_sha256: string;
  final_status: "TRANSCRIPT_VERIFIED_PASS" | "LAYER1_ONLY_PASS";
  human_validation_required: boolean;
  region_kind: "speech_led" | "event_led";
  intensity: "minimal" | "balanced" | "aggressive" | "study_ratio" | "user_edit";
  study_target_ratio: number | null;
  retained_intervals: IntervalWithUnits[];
  cuts: {
    cut_id: string;
    cut_index: number;
    before_unit_id: string;
    after_unit_id: string;
    removed_unit_ids: string[];
  }[];
  micro_edits: {
    type: "pause_shorten";
    start_ms: number;
    end_ms: number;
  }[];
  /**
   * v5.0 2.36.9.2, exact audio_join record shape ('Recorded per cut as audio_join').
   */
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
  crossfades: {
    at_ms: number;
    type: "audio";
    duration_ms: number;
    provisional: false;
  }[];
  timeline: {
    output_segment_id: string;
    source_start_ms: number;
    source_end_ms: number;
    output_start_ms: number;
    output_end_ms: number;
    speed_factor: 1;
  }[];
  final_duration_ms: number;
  compression_ratio: number;
  compression_band: "standard" | "strict";
  duration_profile: "primary" | "extended";
  opening_unit_id: string | null;
  completion_unit_id: string | null;
  short_hook: {
    score: number;
    type: "question" | "number" | "claim" | "none";
    text: string;
  };
  content_style_id: string | null;
  final_face_ratio: number;
  final_screen_ratio: number;
  final_visual_format: "talking_head" | "screen_capture" | "mixed" | "other_visual";
  event: {
    onset_ms: number;
    settle_ms: number | null;
    settle_source: "detected" | "capped";
    capped_end_ms: number | null;
    start_is_nearest_safe_before_onset: boolean;
  } | null;
  /**
   * 2.36.9.8a rule 2: always null; the reframe result lives in its own reframe_plan_v1 artifact referencing verified_edit_plan_id.
   */
  reframe: null;
}
export interface IntervalWithUnits {
  start_ms: number;
  end_ms: number;
  unit_ids: string[];
}
