// AUTO-GENERATED from packages/schemas/json/reframe_plan_v1.schema.json by packages/schemas/typescript/scripts/gen-types.mjs
// Do not hand-edit -- edit the JSON Schema and regenerate (impl plan 0.4 / 4.3).

/**
 * v5.0 2.39.3. Sole vertical-composition authority.
 */
export interface ReframePlanV1 {
  reframe_plan_id: string;
  reframe_lineage_id: string;
  parent_reframe_plan_id: string | null;
  verified_edit_plan_id: string;
  content_unchanged: boolean;
  schema_version: 1;
  stage_version: "reframe_plan@1";
  config_version: string;
  config_sha256: string;
  final_visual_format: "talking_head" | "screen_capture" | "mixed" | "other_visual";
  strategy: "fixed_center" | "face_aware" | "multi_speaker" | "blurred_background";
  status: "ok" | "degraded" | "infeasible";
  crop_confidence: number;
  reasons: string[];
}
