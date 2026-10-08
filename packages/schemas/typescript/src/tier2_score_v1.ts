// AUTO-GENERATED from packages/schemas/json/tier2_score_v1.schema.json by packages/schemas/typescript/scripts/gen-types.mjs
// Do not hand-edit -- edit the JSON Schema and regenerate (impl plan 0.4 / 4.3).

/**
 * v5.0 2.39.11.
 */
export interface Tier2ScoreV1 {
  tier2_id: string;
  short_candidate_id: string;
  schema_version: 1;
  stage_version: "tier2_heuristic@1";
  config_version: string;
  config_sha256: string;
  export_profile_id: string;
  export_profile_sha256: string;
  weights_version: "t2_weights@1";
  hook_groups_enabled: string[];
  terms: {
    coherence: number | null;
    hook: number | null;
    completeness: number | null;
    density: number | null;
    pacing: number | null;
    energy: number | null;
    visual: number | null;
    edit: number | null;
    reframe: number | null;
  };
  applicable_weight: number;
  present_weight: number;
  failed_weight: number;
  coverage: number;
  degraded_features: boolean;
  final_rank_score: number;
  comparability_class: "A" | "B";
  score_rank: number;
  display_rank: number | null;
  shown: boolean;
  alternate_of: string | null;
  exclusion_reason: string | null;
}
