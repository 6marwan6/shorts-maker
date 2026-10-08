// AUTO-GENERATED from packages/schemas/json/edit_unit.schema.json by packages/schemas/typescript/scripts/gen-types.mjs
// Do not hand-edit -- edit the JSON Schema and regenerate (impl plan 0.4 / 4.3).

/**
 * v5.0 2.36.8.2 Step 1: 'Fields: unit_id, start_ms, end_ms, text, speaker_id, word_count, filler_share.' split_from_run_on is from Step 2 ('flagged split_from_run_on = true'). This is a sub-object embedded in an EditPlan/region working set, not a standalone top-level artifact, so it carries no independent config/schema identity.
 */
export interface EditUnit {
  unit_id: string;
  start_ms: number;
  end_ms: number;
  text: string;
  speaker_id: string | null;
  word_count: number;
  filler_share: number;
  split_from_run_on: boolean;
}
