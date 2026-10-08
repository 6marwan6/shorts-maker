// AUTO-GENERATED from packages/schemas/json/transcript_v1.schema.json by packages/schemas/typescript/scripts/gen-types.mjs
// Do not hand-edit -- edit the JSON Schema and regenerate (impl plan 0.4 / 4.3).

/**
 * Phase 3 output (impl plan Phase 3 3.7; owner decision 2026-09-30 G1). Canonical identity + timing authority for words, sentences, speaker turns. Word/sentence/turn IDs are immutable for the artifact's lifetime (owner G2): W/S/T + six-digit 1-based ordinal, never derived from timestamps or text. Timing is forced-aligned only (v5.0 2.14.1); a word with no reliable alignment keeps its text and has null start/end (owner G4) and is never a cut-safety anchor. Speaker fields are null when diarization was unavailable or failed (owner C1/C4); no zero is substituted. Sentence edges whose boundary word is unaligned are kept but marked timing-unusable (null timing, never synthesized; owner 2026-10-02 #1).
 */
export interface TranscriptV1 {
  schema_version: 1;
  stage_version: "transcript@1";
  config_version: string;
  config_sha256: string;
  source_video_id: string;
  /**
   * compute_stage_input_sha256 of the Phase-3 input artifact IDs (stage idempotency identity).
   */
  input_sha256: string;
  /**
   * language_gate_v1 result (v5.0 2.14). A failed gate never produces a transcript (job FAILED), so gate_status is only passed | not_applicable.
   */
  language: {
    gate_status: "passed" | "not_applicable";
    code: string | null;
    confidence: number | null;
    model_id: string;
    model_sha256: string | null;
    sample_word_count: number;
  };
  words: {
    word_id: string;
    text: string;
    start_ms: number | null;
    end_ms: number | null;
    /**
     * unaligned <=> start_ms and end_ms are both null.
     */
    timing_status: "aligned" | "unaligned";
    confidence: number | null;
    speaker_id: string | null;
  }[];
  sentences: {
    sentence_id: string;
    start_ms: number | null;
    end_ms: number | null;
    text: string;
    /**
     * @minItems 1
     */
    word_ids: [string, ...string[]];
    speaker_id: string | null;
    end_reason:
      | "terminal_punctuation"
      | "gap_speaker_change"
      | "gap_uppercase"
      | "end_of_input"
      | "hard_split_gap"
      | "synthetic_split";
    synthetic_boundary: boolean;
    /**
     * true iff the sentence's FIRST word has a real forced-aligned start AND end. false => start_ms is null and this sentence start is NOT a cut-safety anchor (owner 2026-10-02 #1).
     */
    start_timing_usable: boolean;
    /**
     * true iff the sentence's LAST word has a real forced-aligned start AND end. false => end_ms is null and this sentence end is NOT a cut-safety anchor.
     */
    end_timing_usable: boolean;
  }[];
  /**
   * Raw diarization turns, boundaries exactly as returned (owner G5): no minimum duration, no merging; overlapping turns preserved. Sorted by (start_ms, end_ms, raw_label); speaker_id is assigned by first appearance in that order.
   */
  speaker_turns: {
    turn_id: string;
    start_ms: number;
    end_ms: number;
    speaker_id: string;
    raw_label: string;
  }[];
  provenance: {
    audio: {
      availability: "present" | "not_applicable";
    };
    asr: {
      status: "completed" | "not_applicable_no_audio";
      runtime_id: string | null;
      runtime_sha256: string | null;
      segment_count: number;
      word_count: number;
    };
    alignment: {
      status: "aligned" | "not_applicable";
      runtime_id: string | null;
      runtime_sha256: string | null;
      unaligned_word_count: number;
    };
    diarization: {
      attempted: boolean;
      status: "succeeded" | "unavailable" | "failed" | "not_applicable_no_speech";
      missing_reason: null | "not_available_in_stage" | "extraction_failed";
      provider: string | null;
      model_id: string | null;
      error_category: string | null;
      speaker_count: number;
    };
    sentence_seg: {
      version: "sentence_seg_v1";
      sentence_gap_ms: number;
      sentence_max_s: number;
      hard_split_min_gap_ms: number;
    };
    speaker_assignment: {
      version: "diarization_v1";
    };
    /**
     * component -> pinned model identity. Component keys: asr, alignment, vad, language_id, diarization.
     */
    model_manifest: {
      [k: string]: {
        model_id: string;
        revision: string | null;
        sha256: string | null;
      };
    };
  };
}
