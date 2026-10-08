// AUTO-GENERATED from packages/schemas/json/caption_plan_v1.schema.json by packages/schemas/typescript/scripts/gen-types.mjs
// Do not hand-edit -- edit the JSON Schema and regenerate (impl plan 0.4 / 4.3).

/**
 * v5.0 2.24. Sole caption timing/text-segmentation authority.
 */
export interface CaptionPlanV1 {
  caption_plan_id: string;
  verified_edit_plan_id: string;
  schema_version: 1;
  stage_version: "caption_plan@1";
  config_version: string;
  config_sha256: string;
  caption_mode: "burned_in" | "sidecar" | "none";
  safe_zone: {
    x_min: number;
    x_max: number;
    y_min: number;
    y_max: number;
  };
  cues: {
    output_start_ms: number;
    output_end_ms: number;
    text: string;
    line_count: number;
    safe_zone: string;
  }[];
}
