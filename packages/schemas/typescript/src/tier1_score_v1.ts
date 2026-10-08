// AUTO-GENERATED from packages/schemas/json/tier1_score_v1.schema.json by packages/schemas/typescript/scripts/gen-types.mjs
// Do not hand-edit -- edit the JSON Schema and regenerate (impl plan 0.4 / 4.3).

/**
 * v5.0 2.38.8.
 */
export interface Tier1ScoreV1 {
  tier1_id: string;
  source_region_id: string;
  schema_version: 1;
  stage_version: "tier1@1";
  config_version: string;
  config_sha256: string;
  study_mode: boolean;
  evaluation_mode: boolean;
  effective_max_compression_ratio: number;
  weights_version: "t1_weights@1";
  features: {
    "t1.hook": Vm;
    "t1.boundary": Vm;
    "t1.completeness": Vm;
    "t1.standalone": Vm;
    "t1.density": Vm;
    "t1.energy": Vm;
    "t1.duration_fit": Vm;
    "t1.live_air": Vm;
  };
  region_priority_score: number;
  coverage: number;
  low_evidence: boolean;
  rank: number;
  in_keep_T1: boolean;
  queue: "send_to_edit" | "backfill" | "dropped";
  drop_reason: string | null;
}
export interface Vm {
  v: number | boolean | string | null;
  m: string | null;
}
