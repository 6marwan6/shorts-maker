// AUTO-GENERATED from packages/schemas/json/display_selection_v1.schema.json by packages/schemas/typescript/scripts/gen-types.mjs
// Do not hand-edit -- edit the JSON Schema and regenerate (impl plan 0.4 / 4.3).

/**
 * v5.0 2.39.8. Immutable, reproducible display-order decision, separate from score order.
 */
export interface DisplaySelectionV1 {
  display_selection_id: string;
  schema_version: 1;
  stage_version: "display_selection@1";
  config_version: string;
  config_sha256: string;
  study_mode: boolean;
  evaluation_mode: boolean;
  job_id: string;
  revision: number;
  mmr_lambda: number;
  display_max_overlap: number;
  selected: {
    short_candidate_id: string;
    comparability_class: "A" | "B";
    score_rank: number;
    display_rank: number;
  }[];
  slot_allocation: {
    n_A: number;
    n_B: number;
    slots_A: number;
    slots_B: number;
  };
  exclusions: {
    short_candidate_id: string;
    reason: string;
    overlap_with: string | null;
    overlap_value: number | null;
  }[];
}
