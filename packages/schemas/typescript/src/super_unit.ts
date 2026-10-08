// AUTO-GENERATED from packages/schemas/json/super_unit.schema.json by packages/schemas/typescript/scripts/gen-types.mjs
// Do not hand-edit -- edit the JSON Schema and regenerate (impl plan 0.4 / 4.3).

/**
 * v5.0 2.36.8.2 Step 4: 'Each glue group collapses into one super-unit U_i with duration d_i, value v_i = sum v(u) over its members, and a forced flag.' member_unit_ids and the U<n> id scheme are an INFERENCE (not literal spec text) from the edit_plan_v1 example's opening_unit_id: 'U3' / completion_unit_id: 'U27' alongside Step 4's 'n is typically 20-120' -- reasonably well-grounded, but flagged rather than presented as literal. See README Q-07.
 */
export interface SuperUnit {
  super_unit_id: string;
  /**
   * @minItems 1
   */
  member_unit_ids: [string, ...string[]];
  duration_ms: number;
  value: number;
  forced: boolean;
}
