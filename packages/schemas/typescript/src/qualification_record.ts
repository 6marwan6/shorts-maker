// AUTO-GENERATED from packages/schemas/json/qualification_record.schema.json by packages/schemas/typescript/scripts/gen-types.mjs
// Do not hand-edit -- edit the JSON Schema and regenerate (impl plan 0.4 / 4.3).

/**
 * v5.0 2.9.4.
 */
export interface QualificationRecord {
  region_id: string;
  schema_version: 1;
  stage_version: "qualify@1";
  config_version: string;
  config_sha256: string;
  passed: boolean;
  checks: {
    id: "QC-1" | "QC-2" | "QC-3" | "QC-4" | "QC-5" | "QC-6";
    applicable: boolean;
    passed: boolean;
    value: number | null;
    threshold: number | null;
  }[];
  reject_reasons: string[];
  context_dependency: number;
  single_idea: boolean;
}
