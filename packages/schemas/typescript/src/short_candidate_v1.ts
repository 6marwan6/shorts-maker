// AUTO-GENERATED from packages/schemas/json/short_candidate_v1.schema.json by packages/schemas/typescript/scripts/gen-types.mjs
// Do not hand-edit -- edit the JSON Schema and regenerate (impl plan 0.4 / 4.3).

/**
 * v5.0 2.39.2.
 */
export interface ShortCandidateV1 {
  short_candidate_id: string;
  verified_edit_plan_id: string;
  source_region_id: string;
  source_video_id: string;
  schema_version: 1;
  stage_version: "short_candidate@1";
  config_version: string;
  config_sha256: string;
  plan_origin: "model" | "user_edit";
  parent_short_candidate_id: string | null;
  replaces_short_candidate_id: string | null;
  export_profile_id: string;
  export_profile_sha256: string;
  comparability_class: "A" | "B";
  hook_analysis_id: string;
  content_style_id: string;
  reframe_plan_id: string;
  caption_plan_id: string | null;
  features: {
    [k: string]: {
      v: unknown;
      m: string | null;
    };
  };
  eligible: boolean;
  exclusion_reason: string | null;
}
