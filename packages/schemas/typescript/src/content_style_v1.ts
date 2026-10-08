// AUTO-GENERATED from packages/schemas/json/content_style_v1.schema.json by packages/schemas/typescript/scripts/gen-types.mjs
// Do not hand-edit -- edit the JSON Schema and regenerate (impl plan 0.4 / 4.3).

/**
 * v5.0 2.37.5.1.
 */
export interface ContentStyleV1 {
  content_style_id: string;
  source_region_id: string;
  schema_version: 1;
  stage_version: "content_style@1";
  config_version: string;
  config_sha256: string;
  language_code: string;
  prompt_version: "style_prompt@1";
  model_id: string;
  temperature: 0;
  tokenizer_version: "style_tokenizer@1";
  canonical_passage_sha256: string;
  input_tokens: number;
  truncated: boolean;
  raw_output: {};
  valid: boolean;
  style_status: "ok" | "low_confidence" | "invalid_output" | "rule_event";
  content_style: "story" | "tutorial" | "explanation" | "conversation_qa" | "commentary" | "event" | "other";
  confidence: number;
  visual_format: "talking_head" | "screen_capture" | "mixed" | "other_visual";
  extended_range_allowed: boolean;
}
