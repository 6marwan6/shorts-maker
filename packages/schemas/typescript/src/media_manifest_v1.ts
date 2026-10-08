// AUTO-GENERATED from packages/schemas/json/media_manifest_v1.schema.json by packages/schemas/typescript/scripts/gen-types.mjs
// Do not hand-edit -- edit the JSON Schema and regenerate (impl plan 0.4 / 4.3).

export type VideoStream = {
  codec: string;
  width: number;
  height: number;
  pix_fmt: string | null;
  r_frame_rate: string;
  avg_frame_rate: string;
  rotation_deg: 0 | 90 | 180 | 270;
} | null;
export type AudioStream = {
  codec: string;
  sample_rate: number;
  channels: number;
} | null;

/**
 * Written by the NORMALIZING stage (impl plan 2.2; owner decision 2026-10-02 #12). Records what was probed, what was produced, and how. The original source object is immutable and only referenced here. Artifact ids are deterministic (uuid5 over job, stage input hash and artifact type).
 */
export interface MediaManifestV1 {
  schema_version: 1;
  stage_version: "media_manifest@1";
  config_version: string;
  config_sha256: string;
  source_video_id: string;
  /**
   * The immutable original upload.
   */
  source: {
    artifact_id: string;
    sha256: string;
  };
  probe: Probe;
  audio_presence: "present" | "no_audio_stream";
  orientation: {
    source_rotation_deg: 0 | 90 | 180 | 270;
    rotation_applied_to_pixels: boolean;
    display_width: number;
    display_height: number;
  };
  /**
   * PTS-based decision (owner #13). is_cfr = constant positive PTS delta AND derived fps in {24,25,30,50,60}.
   */
  cfr: {
    is_cfr: boolean;
    reason:
      | "cfr_eligible"
      | "insufficient_frames"
      | "missing_pts"
      | "non_positive_delta"
      | "variable_deltas"
      | "fps_not_eligible";
    frame_count: number;
    time_base: string | null;
    constant_delta_ticks: number | null;
    derived_fps: string | null;
    selected_normalized_fps: 24 | 25 | 30 | 50 | 60;
  };
  normalized_video: {
    object: ObjectRef;
    probe: Probe;
  };
  /**
   * status not_applicable <=> the source has no audio stream (owner G6): no object, no probe.
   */
  analysis_audio: {
    status: "created" | "not_applicable";
    object: ObjectRef | null;
    probe: Probe | null;
  };
  provenance: {
    operation: "ffprobe+ffmpeg_normalize";
    ffmpeg_version: string;
    ffprobe_version: string;
    ffmpeg_argv: {
      [k: string]: string[];
    };
  };
}
export interface Probe {
  duration_s: number;
  size_bytes: number | null;
  video: VideoStream;
  audio: AudioStream;
}
export interface ObjectRef {
  artifact_id: string;
  sha256: string;
  storage_location: string;
}
