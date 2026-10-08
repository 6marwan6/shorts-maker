// AUTO-GENERATED from packages/schemas/json/boundary_event.schema.json by packages/schemas/typescript/scripts/gen-types.mjs
// Do not hand-edit -- edit the JSON Schema and regenerate (impl plan 0.4 / 4.3).

/**
 * v5.0 2.7, literal per-event JSON shape. `type` is deliberately an open string, not a closed enum: 2.7's prose lists 11 event-type bullets (some packing two concepts, e.g. 'question start/end'), and 2.36.5's family-score table gives 12 exact identifiers (sentence_start, sentence_end, speaker_change, shot_cut, pause, audio_event, activity_change, semantic, topic, qa_start, qa_end, hook_potential) that plausibly ARE these types -- but 2.7's 'face/reaction change' and 'story/payoff signal' have no matching identifier anywhere in 2.36.5's table. Closing the enum would mean inventing 2 of 12 canonical strings; left open with `examples` instead. See README Q-07.
 */
export interface BoundaryEvent {
  time_ms: number;
  type: string;
  confidence: number;
  source: "deterministic" | "ml" | "llm";
  version: string;
}
