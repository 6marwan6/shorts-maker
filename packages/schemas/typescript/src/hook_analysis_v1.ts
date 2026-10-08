// AUTO-GENERATED from packages/schemas/json/hook_analysis_v1.schema.json by packages/schemas/typescript/scripts/gen-types.mjs
// Do not hand-edit -- edit the JSON Schema and regenerate (impl plan 0.4 / 4.3).

/**
 * v5.0 2.37.8. 'Each {v, m} pair follows 2.37.3; the schema is abbreviated to values for readability' -- every bracketed {} in the literal example is a {v,m} feature pair per 2.37.3's missingness contract. m is left as an open string (not closed to 2.37.3's 6-value table) to match this repo's existing {v,m} precedent (tier1_score_v1.schema.json's local $defs/vm), so a feature's missing_reason vocabulary is not duplicated/drifted across schema files. promise_sentence_index and promise_sentence_index_valid are NOT {v,m} pairs (the literal example shows raw null/boolean), matching 2.37.3's hook_llm_output@1 schema and the promise_established_ms conversion-contract table.
 */
export interface HookAnalysisV1 {
  hook_analysis_id: string;
  edit_plan_id: string;
  schema_version: 1;
  stage_version: "hook_analysis@1";
  config_version: string;
  config_sha256: string;
  language_code: string;
  region_kind: "speech_led" | "event_led";
  verified_edit_plan_id: string;
  llm_cache_key: string;
  signal_cache_key: string;
  timeline_ref: string;
  text_window: {
    sentence_ids: string[];
    word_count: number;
    over_max_words: boolean;
    under_min_words: boolean;
    window_truncated_by_plan_end: boolean;
    text_sha256: string;
  };
  signal_window_ms: number;
  deterministic: {
    extractor_version: "hook_signals@1";
    first_content_ms: {
      v: unknown;
      m: string | null;
    };
    immediate_content_ratio: {
      v: unknown;
      m: string | null;
    };
    info_density: {
      v: unknown;
      m: string | null;
    };
    first_question_ms: {
      v: unknown;
      m: string | null;
    };
    first_number_ms: {
      v: unknown;
      m: string | null;
    };
    first_claim_ms: {
      v: unknown;
      m: string | null;
    };
    cue_question: {
      v: unknown;
      m: string | null;
    };
    cue_number: {
      v: unknown;
      m: string | null;
    };
    cue_claim_word: {
      v: unknown;
      m: string | null;
    };
    first_audio_event_ms: {
      v: unknown;
      m: string | null;
    };
    first_motion_ms: {
      v: unknown;
      m: string | null;
    };
    audio_onset_in_window: {
      v: unknown;
      m: string | null;
    };
    motion_in_window: {
      v: unknown;
      m: string | null;
    };
    cuts_in_window: {
      v: unknown;
      m: string | null;
    };
    face_ratio_in_window: {
      v: unknown;
      m: string | null;
    };
    first_signal_ms: {
      v: unknown;
      m: string | null;
    };
  };
  from_verifier: {
    verification_id: string;
    verifier_stage_version: "verifier@2";
    prompt_version: "verifier_prompt@2";
    judge_call_index: number;
    opening_standalone_raw: number | null;
    context_independence: {
      v: unknown;
      m: string | null;
    };
    requires_prior_context: {
      v: unknown;
      m: string | null;
    };
  };
  llm: {
    prompt_version: "hook_prompt@1";
    model_id: string;
    temperature: 0;
    /**
     * v may be an array (hook_types is a list of up to HOOK_MAX_TYPES tags, 2.37.3/2.37.4).
     */
    hook_types: {
      v: unknown;
      m: string | null;
    };
    primary_hook_type: {
      v: unknown;
      m: string | null;
    };
    type_confidence: {
      v: unknown;
      m: string | null;
    };
    curiosity_gap: {
      v: unknown;
      m: string | null;
    };
    promise_clarity: {
      v: unknown;
      m: string | null;
    };
    emotional_intensity: {
      v: unknown;
      m: string | null;
    };
    promise_sentence_index: number | null;
    promise_sentence_index_valid: boolean | null;
    promise_established_ms: {
      v: unknown;
      m: string | null;
    };
    raw_output: {};
    valid: boolean;
  };
  analysis_status: "complete" | "partial" | "failed" | "retryable_transport_error" | "not_applicable";
}
