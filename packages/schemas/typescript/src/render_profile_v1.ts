// AUTO-GENERATED from packages/schemas/json/render_profile_v1.schema.json by packages/schemas/typescript/scripts/gen-types.mjs
// Do not hand-edit -- edit the JSON Schema and regenerate (impl plan 0.4 / 4.3).

/**
 * v5.0 2.24. Sole authority for export-format settings. Field-level decision (owner, 2026-09-23): render_profile_v1 keeps profile_version, NOT stage_version -- these are distinct concepts (stage_version = pipeline-stage/producer implementation-contract version; profile_version = export-profile identity/content version), and this artifact is the one exception to the impl-plan-0 blanket stage_version rule because it is not itself a pipeline-stage output in the same sense as the other artifacts -- it is a configuration object the render stage consumes. Faithful to v5.0's literal JSON example, which has no stage_version field.
 */
export interface RenderProfileV1 {
  render_profile_id: string;
  schema_version: 1;
  profile_version: string;
  config_version: string;
  config_sha256: string;
  platform: string;
  aspect_ratio: string;
  target_resolution: {
    width: number;
    height: number;
  };
  frame_rate: number;
  video_codec: string;
  audio_codec: string;
  pixel_format: string;
  container: string;
  caption_mode: "burned_in" | "sidecar" | "none";
  caption_style: {};
  loudness_policy: "source_normalized";
}
