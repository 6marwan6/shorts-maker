# Short-Form Virality Shorts Tool — Full Build Plan

A video-in, ranked-shorts-out product: user uploads a video, the system analyzes it, and returns the clips most likely to perform well as short-form content.

## Document control

- **Role:** single source of truth for implementation. If chat history and this file disagree, this file wins.
- **Version:** 5.0 — **Last updated:** 2026-09-21
- **Rule for implementers (human or AI):** implement only items that are normative (not marked OPEN, EXPERIMENTAL, PROPOSED or SUPERSEDED). Never implement OPEN items. PROPOSED items need owner confirmation first. In v5.0, the previously proposed 2.37.5.1, 2.38 and 2.39 decisions T1–T8 are resolved and normative. Every value marked *initial* is a named, configurable constant (2.36.10).

| Tag | Meaning |
|---|---|
| **AGREED / normative** | Decided. Implement as written. |
| **PROPOSED** | Recommended, awaiting owner confirmation. Not yet normative. |
| **OPEN** | Unresolved. Do not implement. |
| **EXPERIMENTAL** | Built behind a flag; must pass an ablation before becoming default. |
| **SUPERSEDED** | Older text kept for history only. |

### Changelog

| Version | Change |
|---|---|
| 5.0 | Post-v4.9 audit patch: closes real blockers and implementation ambiguities in evaluation isolation, foundational deterministic algorithms, event-duration semantics, study-mode reachability, DP feasibility, LLM transport handling, user-edit validation, event-led judging, reframing/captions/loudness, candidate lifecycle, hook adoption, visual-format missingness, artifact lineage, and specification hygiene. Tier 1, Tier 2 and `content_style_v1` remain normative.
| 4.9 | Final patch pass after end-to-end v4.8 consistency audit. **All previously identified second-order gaps are patched:** canonical event-safe cut authority; robust-z zero-MAD handling; minimal cleanup ceiling and shared `D_clean`; super-unit-safe openings; explicit DP pool post-filter scan; independent generation intensity vs final compression band; end-to-end study-mode compression ceiling; speech-only MVP micro-edits; deterministic judge cross-field validation; explicit user-edit REPAIRABLE behavior; separate reframe lineage; final-timeline `final_visual_format`; deterministic style head/tail truncation; Tier 2 applicable-weight coverage; retained-interval MMR; balanced Task 4; config identity on behavior-producing artifacts; explicit `render_profile_v1`; final minimum-duration naming; natural-source-end completion semantics; shared super-unit embeddings; final visual format for reframing; and current-state closure of stale v4.5/v4.7/PROPOSED references in normative/build sections. A second full-document contradiction scan is required and recorded in the v4.9 verification ledger. **Current normative state:** Tier 1, Tier 2 and `content_style_v1` are normative.
| 4.8 | Final implementation-safety closure after the v4.7 second-order audit. **Patched and verified:** canonical event-safe boundaries are the only event-edge authority; robust-z behavior has a shared zero-MAD fallback; minimal cleanup and `D_clean` share one exact ceiling; openings are super-unit-safe; DP answer extraction scans the retained k-best pool for the first hard-feasible result; intensity and final compression band are independent; study mode uses the effective compression ceiling end-to-end; MVP micro-edits are speech-led only; verifier JSON receives deterministic cross-field semantic validation; user edits have explicit terminal behavior and reframe-only edits use a reframe lineage; `final_visual_format` drives reframing; style input uses deterministic head/tail truncation; Tier 2 coverage is normalized over applicable terms; display MMR uses retained source intervals; Task 4 has explicit video/region balance; behavior-producing artifacts carry config identity; rendering uses an explicit `render_profile_v1`. **Tier 1, Tier 2 and `content_style_v1` remain normative.** |
| 4.6 | Second-pass consistency audit of v4.5 applied end-to-end. **Closed remaining cross-stage gaps:** canonical event-safe boundaries; effective study-mode compression cap; minimal-cleanup ratio contract; opening/super-unit compatibility; DP-pool post-filter selection; intensity vs compression-band separation; event-only micro-edit scope; Tier 2 coherence normalization; applicable-weight coverage; final-timeline visual format; Task 4 sampling controls; user-edit REPAIRABLE behavior; reframe-only lineage; deterministic LLM cross-field validation; robust-z zero-MAD handling; style-input truncation; config/version provenance; retained-interval display overlap. **Tier 1, Tier 2 and `content_style_v1` are now normative in v4.6.** |
| 4.5 | Review of v4.4 applied point by point (ledger below, 40 review items). **Contracts closed:** deterministic qualification C-1…C-6 and `context_dependency` (2.9); Tier 1 prioritizer (2.38, PROPOSED); Tier 2 feature vector, heuristic ranker, comparability classes, display selection and H-G5 protocol (2.39, PROPOSED); `content_style_v1` contract (2.37.5.1, PROPOSED). **Bugs fixed:** start-candidate bound, unreachable `SINGLE_IDEA_EXTENSION` (two caps), exact cohesion function, operational `pattern_completeness`, unreachable G0 (retired), filler deletion vs the no-word-deletion contract (filler removal moved to LATER), micro-edits vs compression bands (canonical order, budgeted application), extended-duration priority, DP base state, `context_dependency`, bounded value function, event onset check (start edge only), settle semantics, stable `cut_id`s in repair, `repair_feasible`/`plan_repair`, hook cache key (canonical input), `no_detection` missingness, question anchors, `visual_format` precedence, style classification moved before edit planning. **Authority:** `verified_edit_plan` is the single plan artifact after verification (final crossfades, joins and timeline). **Judge:** viewer-only, no pre-region context (`verifier_prompt@2`, `verifier@2`). **Statistics:** one-to-one region matching, macro recall, video-cluster bootstrap as the decision statistic, stratified dataset split and Task 3 sampling. **Lifecycle:** user edits re-enter verification (2.26.1). Also fixed: 2.11 compression-ratio definition (was the inverse of 2.36.3); Q6 TikTok note re-checked. |
| 4.4 | Hook analysis and style (F-2) resolved as 2.37 (owner decisions H1–H8 with review amendments): two hook computations (`hook_lexical@1` for opening selection, `hook_analysis_v1` for Tier 2), no composite hook score, deterministic signal algorithms, output-timeline mapping in the Edit Plan, text-window precedence rules, sentence-index conversion contract, per-feature missing reasons, verifier-feature provenance, 8-type hook taxonomy with retention rules, three style axes with a conservative `content_style` default, cluster-bootstrap adoption gate H-G4 plus Tier 2 gate H-G5, cost report keyed by cache. |
| 4.3 | Edit Plan verification (OQ-10) resolved and normative as 2.36.9 (owner decisions V1–V10): Layer 1 hard checks with exact cut-timing and audio-join semantics, structured judge with prompt/schema/normalization, deterministic verdict (LLM scores, code decides), Stage R repair with bridge test, exact judge-call budget, verify-all policy (early stopping disabled), `LAYER1_ONLY_PASS` for low-transcript/event-led plans, corrected sample-size-aware gates, study mode, Task 3 = 100 + 15 plans. All open questions are now resolved. |
| 4.2.1 | Owner corrections: (1) judge-call budget defined exactly (per plan, per region, what a call is, what repair may do); (2) minimal plan keeps the whole Source Region and does not optimize the opening; opening selection applies to balanced/aggressive only, with an explicit tie rule (`OPENING_OBJ_TOL`) because the DP objective does not contain the hook score. |
| 4.2 | Edit Plan generation (OQ-9) resolved and normative as 2.36.8 (owner decisions E1–E6): three intensity-based plans per region (minimal / balanced / aggressive), run-on-sentence guard, glue rules G0–G2, forced opening and completion units, deterministic DP with a defined objective, trim-only event-led editing, Edit Plan schema v1, E-gates. Judge budget changed to 2 per plan / 6 per region and all Layer-1-passing plans are verified (2.36.9). 2.36.2 rule 4 reworded. Constants and gates updated. |
| 4.1 | Locked candidate-discovery decisions D1–D4 and OQ-1–OQ-7. Fixed compression-ratio semantics, confirmed per-video display cap, and made the deterministic event→region proposal algorithm normative for MVP with its recall gate. |
| 4.0 | Added 2.36 (proposed resolutions for OQ-1 to OQ-10). Marked the legacy build plan and the trailing Parts 2B/2C/2D as SUPERSEDED. Added notes to Q2, Q3, Q5. Clarified Tier 1 vs qualification. Added missing orchestration states. Made sentence embeddings a required component. Updated 2.35 with pointers to the proposed resolutions. |
| 3.0 | Normative specification (Part 2), two-tier ranking (OQ-8), rendering/orchestration/review UI/legal/cost sections, evaluation baselines, label strategy. |

### Review findings on v3 still needing an owner decision

| # | Finding | Status in v4 |
|---|---|---|
| F-1 | v3 computes the Structural Profile **once per video**. The agreed design was hierarchical (global plus local profiles), because one video can switch mode. | **Resolved in v4.1** (owner decision D4, 2.36.4). |
| F-2 | The style taxonomy (short-form styles) and the hook-analysis schema from the earlier plan (old 2A.2 and 2A.3) are not in v3. Edit style is supposed to be a per-candidate property, and 2.12 relies on hook analysis. | **Resolved in v4.4** (2.37: hook analysis and a consumer-driven style taxonomy). |
| F-3 | Feature taxonomy (Appendix A) still lacks the per-feature contract fields required by 2.16 (stage, extraction method, failure behavior, cost class). | Unresolved; do it per feature as each is built. |
| F-4 | Numbers for costs were removed entirely. That is consistent with 2.28, but there is no rough per-video-hour budget to sanity-check 2.36.7. | Unresolved; measure after the first pipeline run. |
| F-5 | Product decision still open: upload only, or also import by URL (URL import implies downloading platform content). | Unresolved. |
| F-6 | Tier 1 (2.38), Tier 2 (2.39) and the `content_style_v1` contract (2.37.5.1) were drafted in v4.5 in response to the v4.4 review. | **Resolved in v4.9; normative in v5.0** (owner decisions T1–T8 are recorded in 2.39.13). |

### v4.5 review ledger (review of v4.4, points 1–40)

Verdicts: **PATCHED** = applied as recommended; **PATCHED (variant)** = the finding is accepted but the fix differs from the recommendation (reason given); **PATCHED — PROPOSED** = new specification awaiting owner confirmation; **PATCHED (documented, behavior deferred)** = documented and instrumented, default behavior unchanged until data says otherwise; **NOTED** = commentary, nothing to patch. No finding was rejected outright, so nothing is marked "still not patched".

| # | Finding | Verdict | Where |
|---|---|---|---|
| 1 | Overall architecture assessment | NOTED | – |
| 2.1 | Dataset split not stratified by type | PATCHED | 2.36.1 |
| 2.2 | Region matching not one-to-one | PATCHED (also macro recall, agreement uses the same matching) | 2.36.1 |
| 2.3 | Wilson bounds ignore clustering | PATCHED (cluster bootstrap is the decision statistic; Wilson kept as reference) | 2.36.9.9, V-G2, V-G5 |
| 3.1 | Profile "computed once" contradicts global + local | PATCHED | 2.6 |
| 4 | Raw-search bound wrong (3 starts possible) | PATCHED (Option A: seed's own start plus the best other start, so at most 2) | 2.36.6 Step 2, Bound |
| 5 | `SINGLE_IDEA_EXTENSION` unreachable | PATCHED (two caps, explicit single-idea condition; consequence for 240–300 s regions documented) | 2.36.3, 2.36.6 Step 3 (d) |
| 6 | Cohesion function undefined | PATCHED (exact function, evaluability rules, constants) | 2.36.6 |
| 7 | `pattern_completeness` not operational | PATCHED (two detectable events per pattern; "development" removed from P2) | 2.36.6 |
| 8 | Qualification / C-1 missing; LLM contradiction | PATCHED (Option A, deterministic C-1…C-6, Q-G1; component table fixed) | 2.9, Part 4 |
| 9 | Tier 1 unspecified | PATCHED — PROPOSED | 2.38 |
| 10.1 (10) | G0 unreachable | PATCHED (variant: G0 retired instead of a second threshold; reason in 2.36.8.2) | 2.36.8.2 |
| 10.2 (11) | No word deletion vs filler deletion | PATCHED (Option B: filler removal is LATER) | 2.36.8.8 |
| 10.3 (12) | Micro-edits change compression class | PATCHED (canonical order, budgeted application, final band from final timing) | 2.36.8.1, 2.36.8.8, 2.36.9.2 |
| 10.4 (13) | Extended-duration rules conflict | PATCHED (single build order; extended DP only when `D_clean` exceeds the extended maximum) | 2.36.2 rule 3, 2.36.8.7 |
| 10.5 (14) | DP base state missing | PATCHED | 2.36.8.6 |
| 10.6 (15) | `context_dependency` undefined | PATCHED (deterministic function; kept distinct from the verifier's `opening_standalone`) | 2.9.3, 2.36.8.5 |
| 10.7 (16) | `novelty` unclamped; filler vocabulary undefined | PATCHED | 2.36.8.4 |
| 17 | Style classification too late | PATCHED (state `CLASSIFYING_STYLE`, pipeline, build order) | 2.2, 2.25, Part 3 |
| 18 | `L1_EVENT_ONSET_CUT` rejects normal clips | PATCHED (start edge only; nearest-safe-cut exception added so a cut just before the onset cannot make every plan fail) | 2.36.9.2 |
| 19 | Settle semantics double-count | PATCHED (`settle_ms` = start of the stable interval; capped case defined) | 2.36.6 Step 3, 2.36.9.2 |
| 20 | Repair uses unstable `cut_index` | PATCHED (`cut_id`, stale-target rule, cut map in artifacts) | 2.36.8.9, 2.36.9.6, 2.36.9.8 |
| 21 | Stage R "one transformation" wording | PATCHED | 2.36.9.6 |
| 22 | `repair_feasible` undefined | PATCHED (`plan_repair` dry run) | 2.36.9.4, 2.36.9.6 |
| 23 | Restoring one unit may be insufficient | PATCHED (documented, behavior deferred): depth stays 1, `REPAIR_RESTORE_DEPTH` constant, `repair_insufficient` measurement and a 30% trigger for an offline depth-2 experiment | 2.36.9.6 |
| 24 | Context leakage in the judge | PATCHED (variant: pre-region context removed entirely instead of a two-pass judge; same leakage protection, no extra calls; context-aware check kept as an offline experiment) | 2.36.9.3 |
| 25 | Audio-join authority split | PATCHED (`verified_edit_plan` is authoritative; generator crossfades marked provisional; `applied_crossfade_ms`) | 2.36.9.2, 2.36.9.8a |
| 26 | E-G3 tautological | PATCHED (variant: dedup invariants moved to E-G1; E-G3 measures diversity yield and human-judged difference, because the recommended gate would still only re-test the dedup rule) | 2.36.8.11 |
| 27 | Hook cache key unsafe | PATCHED (canonical input; LLM key includes `[CUT]` markers; separate signal key) | 2.37.1, 2.37.8 |
| 28 | Missingness lacks "no detection" | PATCHED (`no_detection`; cue and promise-index rules updated) | 2.37.3 |
| 29 | Question timing anchors inconsistent | PATCHED | 2.37.3 |
| 30 | Style classifier lacks a contract | PATCHED — PROPOSED | 2.37.5.1 |
| 31 | `visual_format` precedence | PATCHED (ordered rules, `mixed` first) | 2.37.5 |
| 32 | No Tier 2 feature vector / ranker | PATCHED — PROPOSED | 2.39 |
| 33 | What Tier 2 must specify (checklist) | PATCHED — PROPOSED (every row of the checklist is answered in 2.39.1–2.39.10) | 2.39 |
| 34 | Unjudged-plan policy missing | PATCHED — PROPOSED (comparability classes, no invented penalty, merge disabled until T2-G3) | 2.39.6 |
| 35 | Candidate-relative reference population | PATCHED — PROPOSED | 2.39.1, 2.39.5 |
| 36 | Score order vs display order conflated | PATCHED — PROPOSED (`score_rank` and `display_rank` logged separately, 2.18) | 2.3, 2.18, 2.39.8 |
| 37 | User-edit lifecycle | PATCHED (new lineage through the full validation pipeline; state `REVERIFYING_EDIT`) | 2.26.1, 2.25 |
| 38 | External fact check | PATCHED (variant: the TikTok Commercial Content API exists but is an ad-library API with EU-only data, not a path to organic trend data; Q6 note added, conclusion unchanged) | Q6 |
| 39 | Priority classification table | NOTED | – |
| 40 | Minimum patch set | PATCHED (all six groups are covered by the rows above) | – |

**Found while patching (not in the review):** (X-1) 2.11 defined `compression_ratio` as final/source, the inverse of 2.36.3: fixed. (X-2) The judge issue de-duplication keyed on ordinal `cut_index`: now `cut_id`. (X-3) The E-gate row of 2.36.11 still listed the retired E-G2: fixed. (X-4) A 240–300 s single-idea region can only yield an `extended` plan under the 4:1 ceiling: documented in 2.36.3.

**Choices made where the review offered options (owner may override):** Option A for start candidates (R4) and for deterministic qualification (R8); Option B for filler deletion (R11); G0 removed rather than two thresholds (R10.1); viewer-only judge without context (R24); depth-1 repair kept (R23); Tier 2 has no `hook_lexical@1` fallback (T5).

### v4.6 second-pass consistency ledger (historical)

| ID | Finding | v4.6 action | Where |
|---|---|---|---|
| C-1 | Event discovery could generate a non-safe start | Patched with canonical `event_safe_cut_v1` and safe-boundary resolver | 2.36.0, 2.36.6, 2.9 |
| C-2 | Event discovery fallback end could be non-safe | Patched; all event ends use the same safe-boundary resolver or are rejected | 2.36.0, 2.36.6, 2.36.8.3, 2.36.9.2 |
| C-3 | Robust-z formulas lacked universal zero-MAD behavior | Patched with shared `robust_z_v1` and explicit zero-MAD rule | 2.36.0, 2.36.4, 2.36.5, 2.37 |
| C-4 | Minimal cleanup had no explicit compression ceiling | Patched with `MINIMAL_CLEANUP_RATIO_CAP = 1.10`; `D_clean` uses the same rule | 2.36.2, 2.36.8.8, 2.36.10 |
| C-5 | Opening candidates could begin inside atomic glue units | Patched; openings are super-unit starts only | 2.36.8.5 |
| C-6 | DP_POOL post-filters did not define recovery | Patched; first valid solution in objective-descending top-20 pool wins | 2.36.8.6 |
| C-7 | Intensity and final compression band were still conflated | Patched; intensity is generation provenance, band is final-timeline-derived | 2.36.8.7, 2.36.9.4 |
| C-8 | Study mode could not actually produce >4:1 plans | Patched with `effective_max_compression_ratio` used end-to-end | 2.36.0, 2.36.3, 2.36.8, 2.36.9 |
| C-9 | Event-led trim-only plans could still get speech pause micro-edits | Patched; MVP pause micro-edits are speech-led only | 2.36.8.3, 2.36.8.8 |
| C-10 | Tier 2 coherence was normalized twice | Patched; verifier coherence features are stored/consumed in [0,1] | 2.39.3–2.39.4 |
| C-11 | Event/class-B candidates could fail Tier 2 coverage by construction | Patched; coverage denominator is total applicable weight | 2.39.4 |
| C-12 | User-edit REPAIRABLE and reframe-only paths were ambiguous | Patched; user edits never auto-repair; reframe-only edits create a reframe lineage | 2.26.1 |
| C-13 | Source visual format could disagree with final edited content | Patched with `final_visual_format` and final-timeline reframing | 2.24, 2.37.5, 2.39.3 |
| C-14 | Task 4 lacked cluster-balance controls | Patched with video-diversity/share limits and deterministic sampling; base size 400 pairs | 2.36.1 |
| C-15 | JSON schema did not enforce LLM cross-field semantics | Patched with deterministic semantic-output validation | 2.36.9.3–2.36.9.5 |
| C-16 | Style classifier lacked long-input truncation semantics | Patched with deterministic head+tail preservation | 2.37.5.1 |
| C-17 | Display MMR used whole source regions rather than retained intervals | Patched; overlap is based on retained source-time unions | 2.39.8 |
| C-18 | Config identity was not consistently persisted | Patched with `config_version` + `config_sha256` | 2.18, 2.36.9.8a, 2.38.8, 2.39.2, 2.39.11 |
| C-19 | The 3-minute→35-second example violated the initial 4:1 ceiling | Patched to 45 seconds | 2.1 |
| C-20 | Natural video-end completion could be under-scored | Patched; C-6-valid video-end completion counts for P2/P3 | 2.36.6 |

### v4.7 implementation-safety ledger

| ID | Finding from second v4.6 audit | Patch | Where |
|---|---|---|---|
| V7-1 | Event starts/ends could still land off the canonical safe boundary set | One `event_safe_cut_v1` predicate plus safe-boundary resolvers reused by discovery, qualification, event editing and Layer 1 | 2.36.0, 2.36.6, 2.9, 2.36.8.3, 2.36.9.2 |
| V7-2 | Robust-z zero-MAD behavior could produce divide-by-zero/infinite values | Shared finite `robust_z_v1` with signal-specific floors | 2.36.0, 2.36.4, 2.36.5, 2.37 |
| V7-3 | Minimal cleanup had no exact ceiling | `MINIMAL_CLEANUP_RATIO_CAP = 1.10`; `D_clean` is produced by that exact procedure | 2.36.2, 2.36.8.8 |
| V7-4 | Opening candidates could conflict with atomic G1/G2 groups | Opening candidates are super-unit starts only | 2.36.8.5 |
| V7-5 | DP post-filters could discard the optimum without finding a feasible alternative | Top `DP_POOL` hypotheses are retained per state; answer extraction scans them in objective order and selects the first post-filter-feasible solution | 2.36.8.6 |
| V7-6 | Generation intensity and final compression band remained semantically coupled | `intensity` is generation provenance only; `compression_band` comes from final verified timing | 2.36.8.7, 2.36.9.4 |
| V7-7 | Study mode >4:1 was not connected to every hard compression check | `effective_max_compression_ratio` is used by generation, post-filtering, Layer 1 and study artifacts | 2.36.0, 2.36.8, 2.36.9 |
| V7-8 | Event-led trim-only plans could receive pause micro-edits | Pause shortening is speech-led-only in MVP | 2.36.8.3, 2.36.8.8 |
| V7-9 | LLM schema validity did not enforce cross-field semantics | Added `validate_judge_semantics@1`; malformed combinations consume the retry | 2.36.9.3–2.36.9.5 |
| V7-10 | User-edit `REPAIRABLE` and reframe-only paths were underspecified | Content edits reject without auto-repair; reframe-only edits create a reframe lineage and skip content verification | 2.26.1 |
| V7-11 | Region visual format could differ from the final edited timeline | Added `final_visual_format` from verified retained intervals and made it authoritative for reframing | 2.24, 2.37.5, 2.39.3 |
| V7-12 | Long style passages lacked deterministic truncation | Versioned head/tail truncation and hashed canonical input | 2.37.5.1 |
| V7-13 | Tier 2 event candidates could be excluded by a fixed 1.0 coverage denominator | Coverage uses applicable feature weight as denominator; N/A features do not reduce evidence | 2.39.4 |
| V7-14 | Task 4 pair sample could be concentrated by video or sibling pairs | Minimum videos/share, cross-region minimum, explicit sibling stratum and deterministic seed | 2.36.1 |
| V7-15 | Config identity was not consistently persisted | `config_version` + `config_sha256` added to downstream decision artifacts | 2.18, 2.36.9.8, 2.36.9.8a, 2.37.8, 2.38.8, 2.39.2, 2.39.11 |
| V7-16 | Display MMR used broad source spans | MMR uses retained source-time unions and retained duration | 2.39.8 |
| V7-17 | Stale 200-pair wording remained | 400 same-class base pairs; separate cross-class set | 2.36.1, 2.37.7, 2.39.9 |

### v4.8 final patch ledger

| ID | Patch completed | Where |
|---|---|---|
| V8-1 | Added a single `is_event_safe_cut_v1` predicate and resolver semantics that every event stage shares; discovery never invents unsafe endpoints. | 2.36.0, 2.36.6, 2.9, 2.36.8.3, 2.36.9.2 |
| V8-2 | Added deterministic zero-MAD behavior to every robust-z family and a shared helper contract. | 2.36.0, 2.36.4, 2.36.5, 2.37 |
| V8-3 | Made `D_clean` a canonical artifact/result of the exact speech cleanup procedure and bounded minimal cleanup at 1.10:1. | 2.36.2, 2.36.8.8 |
| V8-4 | Openings are selected only at super-unit starts after G1/G2 construction. | 2.36.8.5 |
| V8-5 | Defined explicit top-20 DP hypothesis recovery and post-filter scanning. | 2.36.8.6 |
| V8-6 | Separated generation `intensity` from final `compression_band`; verifier uses the latter. | 2.36.8.7, 2.36.9.4 |
| V8-7 | Wired study mode into all compression checks and artifact provenance. | 2.36.0, 2.36.8.7, 2.36.9.2, 2.36.9.8a |
| V8-8 | Restricted MVP pause micro-edits to speech-led plans. | 2.36.8.3, 2.36.8.8 |
| V8-9 | Added deterministic semantic validation after schema validation for judge output. | 2.36.9.3–2.36.9.5 |
| V8-10 | Clarified user-edit `REPAIRABLE` terminal behavior and separated reframe-only edits into their own lineage. | 2.26.1 |
| V8-11 | Added `final_visual_format` as the final-timeline composition input to the reframer. | 2.24, 2.37.5, 2.39.3 |
| V8-12 | Added deterministic style-passage truncation and tokenizer/versioned cache identity. | 2.37.5.1 |
| V8-13 | Tier 2 coverage is calculated over applicable weights; designed N/A features do not lower coverage. | 2.39.4 |
| V8-14 | Added explicit Task 4 video/region balance and same-region reporting. | 2.36.1 |
| V8-15 | Added `config_version` and `config_sha256` to all decision artifacts and stage provenance. | 2.18, 2.36.9.8, 2.36.9.8a, 2.37.8, 2.38.8, 2.39.2, 2.39.11 |
| V8-16 | Display MMR uses retained source-time unions and retained durations. | 2.39.8 |
| V8-17 | Created an explicit `render_profile_v1` authority and user-edit/render lifecycle tie-in. | 2.24, 2.26.1 |
| V8-18 | Closed remaining stale PROPOSED/v4.5/v4.6 references in normative text and build sequence. | 2.36.11, 2.37, 2.38, 2.39, Part 3, Part 4 |
| V8-19 | Defined Task 4 sampling with a fixed seed, minimum video coverage, share cap, cross-region share and tie handling. | 2.36.1, 2.39.9 |
| V8-20 | Added explicit `natural_source_end` completion semantics for end-of-video candidates. | 2.36.6 |

---

### v4.9 verification ledger

This ledger is the final implementation-safety closure for the second-order audit. Every row below was checked against the normative clauses, not only against prior ledgers.

| ID | Final verification / patch | Normative location |
|---|---|---|
| V9-01 | Confirmed dataset split is creator-disjoint, structural-type stratified, deterministic, and fails closed if the 40/16 + per-type minima are infeasible. | 2.36.1 |
| V9-02 | Confirmed Task 4 has 400 same-class base pairs, ≥40 videos, ≤10% pair share per video, ≥50% cross-region share, separate sibling stratum, fixed seed and deterministic ties. | 2.36.1, 2.39.9–2.39.10 |
| V9-03 | Confirmed `robust_z_v1` is the sole zero-MAD implementation, with explicit finite fallback and named positive signal-specific MAD floors. | 2.36.0, 2.36.4–2.36.5, 2.37 |
| V9-04 | Confirmed `event_safe_cut_v1` plus its resolvers are the only authority for event starts/ends across discovery, qualification, editing and Layer 1; natural source end is a valid completion when its completion check passes. | 2.36.0, 2.36.6, 2.9, 2.36.8.3, 2.36.9.2 |
| V9-05 | Confirmed zero-evidence `StartScore` / `EndScore` returns finite `0.0` with `no_evidence`, without treating absence as weak evidence. | 2.36.5 |
| V9-06 | Confirmed single-idea extension has a separate 300 s cap, and the ordinary 240 s discovery cap does not make `SINGLE_IDEA_EXTENSION` unreachable. | 2.36.3, 2.36.6 |
| V9-07 | Confirmed `pattern_completeness`, cohesion and all qualification checks have exact operational definitions; event patterns are not forced through speech-only checks. | 2.9, 2.36.6 |
| V9-08 | Confirmed `D_clean` is a deterministic pre-DP artifact, bounded by `MINIMAL_CLEANUP_RATIO_CAP`, with filler-word deletion deferred beyond MVP. | 2.36.2, 2.36.8.8 |
| V9-09 | Confirmed edit planning uses a fixed DP base state, super-unit-safe openings, retained top-20 hypotheses and objective-descending post-filter scanning; generation intent is independent from final compression band. | 2.36.8.5–2.36.8.7 |
| V9-10 | Confirmed final timeline, duration, compression ratio, band and profile are recomputed after authoritative audio joins before Layer 1 gates. | 2.36.8.1, 2.36.9.2 |
| V9-11 | Confirmed Stage-R repair uses immutable `cut_id`s, bounded restoration depth, a multi-operation single repair pass, explicit `repair_feasible`, bridge testing and no judge leakage of deleted text. | 2.36.9.5–2.36.9.6 |
| V9-12 | Confirmed verifier output gets deterministic cross-field semantic validation after JSON-schema validation and before normalization. | 2.36.9.3 |
| V9-13 | Confirmed viewer-only hook/context scoring is separated from opening-dependency detection, and hook cache keys bind the canonical actual analysis input, model/prompt versions and timeline mapping. | 2.37.1–2.37.3 |
| V9-14 | Confirmed style classification runs before edit planning, has deterministic 2000-head + marker + 1900-tail truncation, explicit tokenizer identity and versioned cache keys. | 2.37.5–2.37.5.1 |
| V9-15 | Confirmed `visual_format` precedence is explicit and `final_visual_format` is recomputed from the verified retained timeline and used by reframing/Tier 2. | 2.37.5, 2.24, 2.39.3 |
| V9-16 | Confirmed Tier 1 is fully specified: feature vector, weights, score/coverage formula, missingness, score floor, deterministic ordering, bounded backfill, baselines, video-cluster bootstrap gates and learned calibration rule. | 2.38 |
| V9-17 | Confirmed Tier 2 distinguishes `not_applicable` from extraction/validation failures, normalizes coverage over applicable weight, keeps candidate-relative reference population source-video-local, and ranks class A/B separately. | 2.39.1–2.39.6 |
| V9-18 | Confirmed Tier 2 coherence is not divided by 5 twice; B2 is reported only on class A where coherence is applicable; event/class-B coverage is not penalized for designed N/A features. | 2.39.4, 2.39.10 |
| V9-19 | Confirmed display score order and MMR display order are separate artifacts; MMR overlap uses retained source intervals; `display_selection_v1` is immutable and reproducible. | 2.39.8 |
| V9-20 | Confirmed user content edits that become `REPAIRABLE`/`HARD_FAIL` end in `BLOCKED_USER_EDIT` with no automatic repair, while reframe-only edits have separate reframe lineage. | 2.26.1 |
| V9-21 | Confirmed behavior-producing artifacts carry config identity; study-mode compression provenance is explicit; rendering has one immutable `render_profile_v1` export-format authority with no outside override. | 2.18, 2.36.9.8–2.36.9.8a, 2.37.8, 2.38.8, 2.39.2, 2.39.11, 2.24 |
| V9-22 | Confirmed source-region minima (10 s speech / 6 s event) are distinct from final export minimum (8 s default), and final-duration rules use the export profile. | 2.36.2–2.36.3 |
| V9-23 | Confirmed event-led MVP editing is trim-only and excluded from pause-shortening micro-edits; event results are reported separately from speech-led semantic evaluation. | 2.36.8.3, 2.36.8.8, 2.36.9.9 |
| V9-24 | Confirmed the final 3-minute example is 45 s (4:1), and no normative clause retains the earlier 35 s / 8:1 example. | 2.1, 2.36.11 |
| V9-25 | Final static validation passes: no stale v4.8 normative status, no old visual thresholds, no old Tier-1 raw compression cap, 104 fenced-code markers are balanced, and all 18 fenced JSON examples parse with duplicate-key detection. | v4.9 validation pass |

**Verification result:** PASS. The document is internally consistent at the stated MVP scope; historical ledgers may retain superseded/proposed wording, but no current normative/build clause depends on those historical states.

### v5.0 audit disposition

The attached audit was reviewed finding-by-finding against the normative plan. The blockers and implementation-affecting MAJOR/MINOR contradictions were patched in the normative text. `IMPROVE` findings that are product-scope or process preferences rather than correctness bugs were not promoted into mandatory behavior (notably a new content-suitability stage, accounts/quotas/billing, and the proposed score-distribution pilot). Data-dependent risks remain subject to the existing calibration/gate framework rather than being asserted as already solved.

### v5.0 verification ledger

This ledger records the post-v4.9 audit fixes applied in the current normative text.

| ID | Patch | Normative location |
|---|---|---|
| V5-01 | Task 4 split into dev and sealed pools; sealed data cannot drive tuning. | 2.36.1, 2.39.9–2.39.10 |
| V5-02 | Phase 0 now owns config snapshots, shared helpers, deterministic analysis primitives and machine-checkable artifact schemas. | 2.14.1, 2.36.0, Part 3 |
| V5-03 | Sentence segmentation, forced alignment, TextTiling depth, embedding identity and no-diarization behavior are explicit. | 2.14.1 |
| V5-04 | Discovery cap is explicitly profile-independent; each job has one immutable export profile. | 2.13, 2.36.2–2.36.3 |
| V5-05 | Event lead-in, settle search, STOP-point candidates and event final minimum are explicit; 6 s events are no longer impossible. | 2.36.2, 2.36.6, 2.36.9.2 |
| V5-06 | Study mode has deterministic target-ratio generation for >4:1 bands. | 2.36.8.7, 2.36.9.9 |
| V5-07 | DP uses 0.1 s buckets, k-best-per-state and an interval-length state; authoritative-join reserve is explicit. | 2.36.8.6 |
| V5-08 | Event-led trim-only plans use a 1.5:1 generation cap, consistent with their allowed trimming. | 2.36.8.3, 2.36.8.7 |
| V5-09 | Verifier, hook and style calls distinguish transport failures from invalid output with separate retry semantics. | 2.36.9.3–2.36.9.5, 2.37.3, 2.37.5.1 |
| V5-10 | User-edit plans have explicit Layer-1 semantics and a candidate-level lifecycle; selection does not silently reshuffle. | 2.26.1, 2.36.9.2 |
| V5-11 | Event-led plans are Layer-1-only/class-B in MVP; hook LLM does not run for them. | 2.36.9.1, 2.37.1, 2.39.1 |
| V5-12 | Reframe, captions and loudness have deterministic MVP contracts and artifacts. | 2.24, 2.39.3 |
| V5-13 | Hook prompt/semantic validation and adoption-unit semantics are explicit; duplicated context-independence is removed from Tier 2. | 2.37.3, 2.37.7, 2.39.3–2.39.4 |
| V5-14 | Tier-2 applicability, visual-format missingness, region-level completeness semantics and T2-A1 ablation are explicit. | 2.37.5, 2.39.4, 2.39.10 |
| V5-15 | Stale current-state wording, duplicate style hash field, artifact-ID gaps and current identifier/missing-reason ambiguity are removed; no citation-placeholder tokens remain in the current text. | Document control, 2.18, 2.16.1, 2.37.5.1, 2.36.11 |
| V5-16 | Closed the remaining post-audit coherence gaps: explicit English language gate, transcript-bearing forced-alignment boundary, monotonic backfill semantics, study-only judge budget/ordering, final DP base-state namespace, downstream artifact-ID placement, and render-time caption-input authority. | 2.14, 2.25, 2.36.9, 2.37.6, 2.38.5, 2.24, 2.39.2 |
| V5-17 | Promoted render/reframe/caption/loudness constants into the consolidated constant registry and removed a redundant minimum-duration constant row, so implementation values are machine-discoverable and versioned in one place. | 2.24, 2.36.10 |

**Verification result:** PATCHED. The revised plan must pass the same static checks used for v4.9 plus conformance tests for the new contracts before implementation sign-off. The post-audit cleanup also resolves the remaining namespace, lifecycle and provenance inconsistencies identified while applying the fixes.

## Part 1 — Q&A

### Q1. What should the video upload step handle?

**Formats to accept:** MP4 (H.264/H.265), MOV, MKV, WebM, AVI — basically whatever comes off a phone, screen recorder, or streaming setup. Don't validate by file extension alone; check the actual file signature (magic bytes), since a mislabeled or spoofed extension is a common source of bugs and security issues.

**Normalization:** Immediately transcode every upload to one standard format (H.264 MP4, fixed frame rate) with ffmpeg, server-side, in a background job. Normalize once, and every downstream stage (transcription, scene detection, clip export) only has to deal with one predictable format instead of dozens of codec/container combinations.

**Length & size limits (for an MVP):**
- Duration cap: start around 60–90 minutes. Beyond that, per-video processing cost (transcription + vision analysis) grows quickly, and most realistic inputs — podcasts, streams, vlogs, interviews — fall under that anyway.
- File size cap: roughly 2–4 GB is reasonable for that duration range.
- Reject uploads that exceed the limit with a clear message, rather than silently truncating — silent truncation just produces confused "why didn't it find my best clip" complaints later.

**Storage:**
- Don't route large video files through your application server. Use presigned upload URLs (both S3 and Cloudflare R2 support this) so the browser uploads directly to object storage.
- Use three logical prefixes: `raw/` (original upload), `processed/` (normalized MP4 + extracted audio track), `clips/` (final generated shorts).
- Set a lifecycle rule to auto-delete `raw/` after 7–14 days once processing is done. Keeping the original multi-GB file around indefinitely is pure cost with no benefit.
- See Part 3 for the storage vendor comparison (R2 vs S3).

**Processing trigger:** upload completes → a queued background job (Redis + Celery, or a managed queue) picks it up → runs ffmpeg normalization and probes duration/resolution/codec → kicks off transcription and segmentation. Never do this synchronously in the request/response cycle — a 90-minute video takes real wall-clock time to process.

---

### Q2. How does the AI decide which snippet will go viral?

> **Note (v4):** "candidate clips" here means Short Candidates (2.1). Topical match to trends is EXPERIMENTAL (2.22–2.23). Ranking is two-tier (2.3).

It doesn't predict "will go viral" as a yes/no — that's not a solvable problem given how much of virality depends on platform algorithm exposure, timing, and luck. Instead, it computes a **relative ranking score** across candidate clips from a fixed set of features:

- Hook strength in the first 2–3 seconds (a question, a visual surprise, a bold claim)
- Topical match to what's currently trending (via the trend database — see Q5)
- Pacing (cuts per minute, words per minute, silence gaps)
- Audio/emotional peaks (loudness spikes, laughter, music drops)
- Visual signals (face presence/expression, on-screen text, motion)
- Standalone comprehensibility (does the clip make sense with zero context from the rest of the video?)
- Loop potential (does the ending flow back into the beginning?)

These become a feature vector per candidate clip, scored by a ranking model, and the top N clips are returned. It's honestly framed as "these are the strongest candidates," not "these will go viral."

---

### Q3. What type of model(s) do we actually need?

> **Note (v4):** shot/scene detection is one boundary signal among several, not the sole source of candidate boundaries (2.7, 2.36.5).

Not one large multimodal model — a pipeline of small, mostly off-the-shelf components, so audio and visual information become explicit features instead of being discarded:

- **Speech-to-text** → transcript
- **Shot/scene detection** → candidate clip boundaries
- **Lightweight computer vision** → face/expression, motion, on-screen text, turned into numeric features
- **Text embeddings** → semantic similarity between the transcript and currently trending topics
- **A small ranking model** (gradient-boosted trees) → combines everything above into a single score

Full options and alternatives for each are in Part 3.

---

### Q4. Fine-tune vs RAG — which do we use?

Neither is the right *core* mechanism — both are usually built for generation, not scoring:

- **Fine-tuning** an LLM is worth considering later if you want to *generate* captions, titles, or hooks in a particular voice. It's the wrong tool for "score this clip" — that's a regression/ranking problem, and fine-tuning is slow and expensive to keep current as trends shift week to week.
- **RAG-style retrieval** fits one specific piece well: embedding a candidate clip's transcript and searching a trend database for similar recent trending content. That similarity score becomes *one input feature* to the ranking model — retrieval is a feature source, not the decision-maker.
- **The core scorer** should be a gradient-boosted tree model (XGBoost or LightGBM) trained on the engineered feature vector. Cheap to train, cheap to retrain daily, interpretable (you can show *why* a clip scored well), and workable with a few thousand labeled examples instead of millions.

---

### Q5. If RAG, how do we feed it data — every time, or once?

> **SUPERSEDED in part (v4):** step 1 below (transcribing trending videos with ASR) is not available through the official API. The trend index is metadata-only and EXPERIMENTAL (2.22).

Continuously, via a scheduled pipeline — never a one-time load, because trend relevance decays within days:

1. A daily (or hourly) job pulls fresh trending video metadata: transcript (via ASR), hashtags/topic, sound ID, engagement counts.
2. Each item gets embedded and upserted into a vector database.
3. Keep a rolling window (7–30 days) and expire old entries.
4. At inference time: embed the candidate clip's transcript, run a nearest-neighbor search against the trend DB, and use the similarity score plus the neighbors' engagement stats as a feature.

You're never re-feeding the whole dataset to a model per request — it's a fast lookup against a continuously refreshed index.

---

### Q6. How do we collect the underlying data?

This is the hardest and most important part of the whole project to get right early:

- **YouTube** — the YouTube Data API v3 is free and legitimate. Every Google Cloud project gets a default 10,000-unit daily quota. Simple reads (video stats, playlist items) cost 1 unit each, but `search` calls cost 100 units — which caps you at roughly 100 searches/day on the free tier. Design your collector around cheap list/read calls (e.g. pulling a channel's uploads playlist) rather than search, wherever possible.
- **TikTok** — as of 2026, TikTok's official Research API explicitly excludes commercial users, creators, and advertisers from eligibility; it's restricted to accredited academic institutions and non-profits studying specific approved topics. There is no meaningful free or standard-commercial path to TikTok's trend data through official channels. Realistic options: (a) skip TikTok for v1 and build entirely on YouTube Shorts data, (b) pay a licensed third-party commercial data provider (several exist, real monthly cost — see Part 3), or (c) scrape, which carries genuine ToS and legal exposure and isn't something to build a commercial product's foundation on.
  - *v4.5 note (checked 2026-09-20 against TikTok's developer page and secondary sources; re-verify before implementation):* TikTok also publishes a **Commercial Content API**, but it serves the ad / commercial-content library (searches by advertiser name or keyword), currently with EU data only and aimed at researchers and the public, not at organic trend data. Secondary sources describe it as unavailable to commercial marketers. The Research API remains closed to commercial users. The conclusion above therefore stands for this product. A "Creator Search Insights" endpoint is mentioned by one secondary source only; it is unverified and not relied on.
- **Your own first-party data** is your best long-term asset. Once real users generate shorts through your tool, their actual performance (with permission) becomes labeled training data specific to your own output distribution — more predictive than any generic external trend feed. Expect a cold-start period where the ranker leans on hand-tuned heuristics before you've accumulated enough first-party outcomes to train on.

---

### Q7. Where do we host everything, and what does it cost?

Full detail in Part 3 (components) and Part 4 (cost tiers). Short version: object storage on Cloudflare R2 or S3; GPU inference (transcription + vision) on a serverless GPU provider like Modal or RunPod so you only pay for compute actually used; vector search starting on pgvector inside your existing Postgres (free) and only moving to a dedicated vector database if you outgrow it; the ranking model itself runs on plain CPU — it's tiny compared to everything else.

---

## Legacy build plan (formerly labeled "Part 2") — SUPERSEDED by Part 3

> **SUPERSEDED (v4):** kept for history only. It contradicts the normative specification (fixed 20–60 s windows aligned to shot cuts; trend layer as an early phase). Use Part 3.

### Phase 0 — Foundations
- [ ] Decide MVP scope: YouTube-only trend data, one language, max video length/size.
- [ ] Set up object storage (R2 or S3) with presigned upload URLs.
- [ ] Set up a background job queue for async processing.
- [ ] Legal check: your TikTok data-source plan, and clear terms of service covering what you store/use from user-uploaded video and for how long.

### Phase 1 — Heuristic-only MVP (no trained model yet)
- [ ] Upload → normalize (ffmpeg) → transcribe (self-hosted Whisper, or a cheap hosted endpoint).
- [ ] Scene/shot detection (PySceneDetect) to generate candidate clip boundaries (e.g. 20–60 second windows aligned to shot cuts).
- [ ] Extract hand-tuned features per candidate: hook keywords in the first 3 seconds, pacing (words/minute), basic face-presence check.
- [ ] Score with a simple weighted formula — no ML training required yet. Hand-tune weights against your own judgment on a handful of test videos.
- [ ] Output top N clips, cut with ffmpeg, return to the user.
- **Goal of this phase:** ship something usable and start generating your own first-party usage data.

### Phase 2 — Add the trend intelligence layer
- [ ] Build the daily YouTube-trend collector, designed around the 10,000-unit/day quota (favor list/read calls over search).
- [ ] Add an embedding step for both trending content and candidate clips (start with a cheap embedding model).
- [ ] Stand up pgvector inside your existing Postgres; store embeddings + engagement metadata with a rolling expiry window.
- [ ] Add a "trend match score" as a new feature in the scoring formula.

### Phase 3 — Replace heuristics with a trained ranking model
- [ ] Once you have enough first-party labeled data (clip → actual engagement outcome — even a few thousand examples is a start), train a gradient-boosted tree model (XGBoost/LightGBM) on the full feature set.
- [ ] Validate against a held-out set; compare against the Phase 1 heuristic baseline before fully replacing it.
- [ ] Retrain on a schedule (weekly is reasonable) as new outcome data accumulates.

### Phase 4 — Scale the infrastructure
- [ ] Move transcription/vision inference to serverless GPU hosting if a fixed self-hosted box becomes a bottleneck.
- [ ] If the trend database grows past what pgvector handles comfortably (roughly 10M vectors), migrate to a dedicated vector database (Qdrant is the cheapest self-hosted/managed option; Pinecone if you want zero ops).
- [ ] Add caching so you never re-embed or re-transcribe content you've already processed.

### Phase 5 — Optional: generation layer
- [ ] Only after the core ranker works well: add an LLM step (via API — no fine-tuning needed to start) to auto-generate titles/captions/hashtags for the top clips, using the trend database as retrieved context. This is genuine RAG usage.
- [ ] Consider fine-tuning only if you need a very specific house style at high volume — evaluate whether prompting a general model gets you there first.

---



## Part 2 — Normative System Specification

**Status:** Current planning specification. Decisions in this section are normative unless explicitly marked `OPEN` or `EXPERIMENTAL`.

The document uses three layers intentionally:

1. **Part 1 — Q&A / rationale:** historical reasoning and product context. It explains why the system exists but is not the authoritative implementation contract.
2. **Part 2 — Normative specification:** authoritative architecture, terminology, interfaces, constraints, evaluation, and decisions.
3. **Part 3 onward — implementation reference:** concrete technology choices, deployment, costs, risks, and phased delivery.

### 2.1 Canonical terminology

The word **candidate** is no longer used interchangeably for different artifacts.

| Term | Definition | Can contain cuts? |
|---|---|---:|
| **Source Region** | A contiguous interval of the original video representing a potentially complete idea, story, answer, explanation, event, or reaction. | No |
| **Edit Plan** | An order-preserving transformation of one Source Region into a proposed short. It describes retained/removed content and rendering decisions. | Yes |
| **Short Candidate** | A Source Region + Edit Plan with all final-short features computed or estimated. This is what the final ranker compares. | Yes |
| **Rendered Short** | The actual exported video artifact produced from a Short Candidate. | Yes |

A Source Region is not required to be short. A 3-minute source region may legitimately produce a 45-second Short Candidate under the initial 4:1 compression ceiling; shorter outputs require a later validated ceiling increase.

The system must **not** discover shorts primarily by generating many tiny clips and later trying to reconstruct an idea from them.

### 2.2 Canonical pipeline

```text
Upload
  ↓
Normalize + media probe
  ↓
Cheap structural analysis
  ↓
Structural Profile (global + local) + Event/Boundary Map
  ↓
Adaptive Source Region Discovery (2.36.6, Steps 1–3)
  ↓
Source Region Qualification (2.9; discovery Steps 4–6)
  ↓
Region-level prioritization — Tier 1 (2.38)
  ↓
Content-style classification (2.37.5)          ← must precede edit planning (extended-duration rule)
  ↓
Edit Plan generation (2.36.8)
  ↓
Edit Plan verification (2.36.9)  →  verified_edit_plan (the single authoritative plan artifact)
  ↓
Hook analysis (2.37)
  ↓
Reframe planning (2.24)
  ↓
Short Candidate feature extraction (2.39.3)
  ↓
Final short-level ranking — Tier 2 (2.39)
  ↓
Display selection (2.39.8)
  ↓
Review UI  (a user edit re-enters at Edit Plan verification, 2.26.1)
  ↓
Render selected shorts (reads verified_edit_plan only)
  ↓
Optional publication / performance collection
```

This resolves the previous ranking/editing ambiguity:

- **Tier 1: Region prioritization** happens before edit planning. Its purpose is to avoid spending expensive edit-analysis work on every discovered region.
- **Tier 2: Short ranking** happens after edit planning and uses features that only exist after editing, including final duration, compression ratio, edit density, final opening/hook, final ending, and rendered/layout properties.
- The system must never call Tier 1 the final "virality score." It is an opportunity/qualification score.

### 2.3 OQ-8 — Two-tier ranking decision

**Decision: use two tiers.**

#### Tier 1 — Source Region Opportunity Score

Input:
- Source Region transcript/context.
- Structural events.
- Hook opportunities.
- Semantic completeness signals.
- Event/payoff signals.
- Cheap audio/visual signals.
- Candidate-relative context.

Output:
- `region_priority_score`
- `region_qualification_flags` (carried through from the 2.9 qualification gate; Tier 1 ranks qualified regions and does not re-decide qualification)

Purpose:
- Select a bounded number of promising Source Regions for deeper analysis.
- Maximize recall rather than produce the final ordering shown to the user.

It may use deterministic scoring, lightweight ML, or structured LLM analysis, but must remain cheap enough to run across a long video.

**v4.9:** the exact Tier 1 feature vector, formula, budget policy and gates are normative in 2.38. In MVP Tier 1 is deterministic and calls no LLM.

#### Tier 2 — Short Candidate Ranker

Input:
- Source Region features.
- Edit Plan features.
- Final opening/hook features.
- Final duration/platform target.
- Compression ratio/edit density.
- Boundary/coherence verification.
- Rendering/reframing feasibility.
- Candidate-relative features.

Output:
- `final_rank_score`
- ranked Short Candidates (the **score-ranked pool**).

**v4.9:** `final_rank_score` orders the score-ranked pool. The list actually shown to the user comes from a separate **display-selection** step (MMR diversification and overlap limits, 2.39.8); that ordering is not "ranking model output". The normative Tier 2 feature vector, heuristic ranker and gates are specified in 2.39.

**Important:** the hook is defined at the level being evaluated. Tier 1 evaluates the potential hook available in the Source Region; Tier 2 recomputes the hook from the actual Edit Plan opening. An edit is not allowed to inherit an old hook score if its opening changed.

### 2.4 Candidate discovery philosophy

The discovery engine is a **high-recall structural search**, not an exhaustive sliding-window search and not an LLM request over every possible interval.

It should first construct a reusable event/boundary map from analysis that is already required for the rest of the pipeline. It then uses the video's Structural Profile to determine which boundary signals should dominate.

Candidate discovery must prefer **complete semantic/event units** over arbitrary fixed-duration windows.

Examples:

- Podcast/interview: question → answer → explanation → conclusion boundaries receive high weight.
- Vlog: semantic transitions plus activity/scene/event changes receive high weight.
- Tutorial: problem → explanation → demonstration → result boundaries receive high weight.
- Reaction/event content: visual/audio event onset → reaction → payoff receives high weight.
- Calm conversational content: sentence/turn/topic completeness can dominate visual activity.

The system does not need to assign a single hard genre label. It should produce a **Structural Profile** that controls which discovery strategies are active and how strongly they contribute.

### 2.5 Structural Profile

The Structural Profile is a compact description of how the video is organized. It is a routing/control artifact, not itself a virality score.

Initial dimensions:

```json
{
  "speech_density": 0.0,
  "speaker_turn_density": 0.0,
  "topic_transition_density": 0.0,
  "visual_change_density": 0.0,
  "activity_density": 0.0,
  "audio_event_density": 0.0,
  "scene_change_density": 0.0,
  "face_presence_rate": 0.0,
  "screen_content_rate": 0.0
}
```

These are measured from observable signals. In particular:

- `speech_density` means how much of the video contains speech.
- `topic_transition_density` measures how often the semantic subject changes.
- It must **not** use speech density as a proxy for topic richness.
- `visual_change_density` and `activity_density` are distinct: a static camera can contain a visually important event, while camera movement can occur without meaningful content change.

The profile initially acts as a **strategy selector**, not as a learned continuous weighting system. For example, it can select among semantic-led, visual-led, audio-event-led, or hybrid discovery strategies.

### 2.6 How the Structural Profile is obtained without exhaustive analysis

The system performs a bounded **characterization pass** using analyses that are already useful downstream:

1. ASR timestamps and speaker/turn information where available.
2. Shot/scene boundaries from sampled or full-resolution structural analysis.
3. Low-cost audio energy and silence/event detection.
4. Low-cost motion/activity measurements on sampled frames.
5. Face/screen presence on sampled frames.
6. Lightweight transcript segmentation and topic-transition analysis.

A **global** profile is computed once per source video. **Local** profiles are computed once per derived structural segment (2.36.4, owner decision D4). Both are computed once and reused by downstream stages.

The system must not run an expensive VLM/LLM over every possible interval merely to determine video type.

### 2.7 Adaptive boundary map

The boundary map stores events that can indicate the beginning or end of a meaningful Source Region.

Initial event types:

- sentence completion
- speaker turn
- question start/end
- topic transition
- semantic completion
- pause/silence
- shot/scene change
- visual activity onset/change
- audio energy/event onset
- face/reaction change
- story/payoff signal
- hook opportunity

Each event has:

```json
{
  "time_ms": 0,
  "type": "topic_transition",
  "confidence": 0.0,
  "source": "deterministic|ml|llm",
  "version": "..."
}
```

A Source Region is proposed by combining compatible events into a **complete unit**, not by enumerating every pair of timestamps.

The discovery engine should look for patterns such as:

```text
hook / setup → development → completion / payoff
question → answer completion
claim → supporting explanation
problem → solution/result
activity onset → event → reaction
```

The exact pattern library is configurable and must be evaluated against human-labeled regions.

### 2.8 Preventing exhaustive search

The discovery engine must use a bounded search strategy:

1. Detect a limited set of high-confidence structural events.
2. Use event neighborhoods to propose starts and ends.
3. Extend a proposed region only while evidence indicates that the same idea/event continues.
4. Stop at semantic completion, payoff, strong topic transition, or maximum source-region duration.
5. Deduplicate heavily overlapping Source Regions.
6. Keep only the top bounded number of Source Regions per source-video time span for Tier 1.

It must **not** generate every possible start/end pair and must not use a dense sliding window as the primary search.

A fixed-window baseline is still required for evaluation, because the adaptive system must prove that its extra complexity improves recall.

### 2.9 Source Region qualification

**Status: AGREED contract (v4.5, review items R8/R15); numeric thresholds are *initial* and calibrated per 2.9.4.**

**MVP decision: qualification is deterministic.** It uses the boundary map, sentence embeddings, transcript features and audio/visual rates. It calls **no LLM**. An LLM-assisted qualifier for ambiguous regions is LATER and needs an ablation against this deterministic version. (The semantic LLM components of the MVP are the verifier 2.36.9, hook analysis 2.37 and style classification 2.37.5; none of them runs during discovery or qualification.)

#### 2.9.1 When it runs

Qualification runs on **every raw region** produced by discovery Steps 1–3 (2.36.6), **before** RS scoring, dedup and the `R_DISC` cap. Therefore every downstream count in 2.36.7 counts qualified regions only. Every check is computed from the region's own sentences and the video signals; it never reads text outside the region.

#### 2.9.2 Checks (IDs are referenced by 2.36.6 Step 4 and by 2.36.8.5)

| ID | Applies to | Check | Initial threshold | Reject reason |
|---|---|---|---|---|
| QC-1 | all | **Edge validity.** Speech-led: the start is a sentence start that is either the seed's own sentence start or has `StartScore ≥ START_MIN`; the end is a sentence end that either has `EndScore ≥ END_MIN`, is the natural STOP point of 2.36.6 Step 3 (a)–(c), **or is the source-video end from STOP (e) when QC-6 accepts the ending**. Event-led: start and end satisfy the canonical `event_safe_cut_v1` predicate (2.36.0). | START_MIN / END_MIN (0.35) | `bad_start_edge`, `bad_end_edge` |
| QC-2 | speech-led | **Opening context dependency:** `context_dependency(first sentence) ≤ CTX_MAX` (function in 2.9.3). | `CTX_MAX` 0.5 | `opening_context_dependent` |
| QC-3 | all | **Enough material:** duration ≥ `MIN_REGION_SPEECH` for speech-led or `MIN_REGION_EVENT` for event-led; speech-led also ≥ `MIN_REGION_WORDS` words. | 10 s / 6 s; 30 words | `too_short`, `too_few_words` |
| QC-4 | speech-led | **Not a speech-free fragment:** share of region time containing speech ≥ `SPEECH_RATIO_MIN`. | 0.4 | `fragment_no_speech` |
| QC-5 | all | **Duration cap:** ≤ `MAX_REGION_S`, or ≤ `MAX_SINGLE_IDEA_REGION_S` when the region carries `single_idea = true` (2.36.6 Step 3 (d)); event-led regions ≤ `MAX_EVENT_S`. | 240 s / 300 s / 45 s | `too_long` |
| QC-6 | speech-led | **Complete ending:** the last sentence is not an unanswered question (a question with no following sentence inside the region) and its last word is not in `END_CONNECTIVES` = {and, but, so, because, or, then, which, that, if, when}. | – | `open_ending` |

**Event-led exception (explicit).** A region whose seed pattern is P4 (2.36.6) is exempt from QC-2, QC-4 and QC-6 (it is not required to have standalone speech meaning). It must satisfy QC-1, QC-3 and QC-5, and later the Layer-1 event checks (2.36.9.2).

#### 2.9.3 `context_dependency` (deterministic, shared function)

One function is used by QC-2 **and** by opening selection (2.36.8.5). It is a cheap prefilter computed from the transcript alone, before any editing.

```text
tokens   = lowercase word tokens of the sentence being tested
if tokens is empty:
    context_dependency = 1.0
    missing_reason = "no_content"
else:
    R = 1 if tokens[0] ∈ G2_REF else 0
    C = 1 if the sentence starts with a G2_CONNECTIVE (single word or bigram, e.g. "and then") else 0
    P = min(1, (number of tokens ∈ G2_REF ∪ {him, her, them} in this sentence and the next one) / 3)
    context_dependency = clip(0.6·R + 0.6·C + 0.4·P, 0, 1)
```

`G2_REF` and `G2_CONNECTIVE` are the exact lists of glue rule G2 (2.36.8.2), stored once as the versioned config `glue_lists@1`.

**Relation to the verifier.** `context_dependency` is a pre-edit transcript heuristic used to reject or choose openings cheaply. The verifier's `opening_standalone` score (2.36.9.3) is a post-edit semantic judgment and is what Tier 2 consumes (2.37.3 group B). They have different purposes and are never mixed into one feature.

#### 2.9.4 Output and calibration

Each raw region gets a `qualification_record`:

```json
{ "region_id": "uuid", "schema_version": 1, "stage_version": "qualify@1",
  "config_version": "config@1", "config_sha256": "…",
  "passed": true,
  "checks": [ { "id": "QC-1", "applicable": true, "passed": true, "value": 0.0, "threshold": 0.35 } ],
  "reject_reasons": [],
  "context_dependency": 0.0,
  "single_idea": false }
```

Rejected regions are **kept in the artifact** (not deleted) so that qualification's effect on recall can be measured.

**Calibration (after labels exist):**
1. `CTX_MAX`: at least 90% of regions labeled `standalone = yes` (Task 2) pass QC-2, and at least 60% of regions labeled `standalone = no` fail it; otherwise adjust the weights in 2.9.3 by owner decision.
2. `SPEECH_RATIO_MIN`, `MIN_REGION_WORDS`: choose the values that keep ≥ 95% of A/B labeled regions.

**Gate Q-G1 (qualification must not destroy recall).** On the dev set, the share of A+B labeled regions that have a loose hit among the raw regions but no loose hit after qualification is ≤ 0.05 (one-to-one matching, 2.36.1). If it is higher, relax the failing check first (thresholds, then rules) before touching discovery.

### 2.10 Edit Plan constraints — no fragment-assembly search

Edit planning is explicitly **not** a second candidate-generation search.

For the MVP:

- Source order is immutable.
- No reordering.
- No synthesis of new spoken content.
- No arbitrary sub-sentence word splicing.
- For speech-led candidates, cuts occur at sentence/phrase-safe boundaries and remove whole low-value spans.
- For event-led non-speech material, cuts may use validated event boundaries.
- The edit planner may delete material; it may not invent a new narrative order.
- The number of retained intervals is bounded.

Conceptually:

```text
Source Region
   ↓
ordered content units
   ↓
keep/remove decisions
   ↓
Edit Plan
```

The verifier must check:

- transcript continuity around cuts;
- sentence/phrase completeness;
- pronoun/reference dependencies;
- topic continuity;
- setup/payoff preservation;
- temporal ordering;
- final duration;
- excessive compression;
- abrupt audio transitions.

If the verifier fails, the Edit Plan is rejected or simplified; the system must not keep searching arbitrary combinations until it finds a high-scoring but incoherent edit.

### 2.11 Compression-ratio constraint and evaluation

`compression_ratio = source_region_duration / final_duration` (v4.5: corrected to match 2.36.3, where 4.0 means a 4:1 source-to-final ceiling; earlier text of this section had the inverse fraction) is a diagnostic feature and a safety constraint for edit planning.

The project will not assume that an arbitrarily high compression ratio is acceptable. The evaluation set must measure coherence and human preference across compression bands.

Initial MVP policy:
- Prefer conservative compression.
- Do not allow extreme compression without explicit evaluation evidence.
- Treat compression ratio as a ranking/editing feature rather than an objective to maximize.

The evaluation must report where coherence or perceived quality begins to degrade as compression increases.

### 2.12 Hook definition across the two tiers

Hook is not one immutable number.

**Region hook:** potential strength of the earliest viable opening of the Source Region.

**Short hook:** strength of the actual first 1–3 seconds after applying the Edit Plan.

The final short score must use the **Short hook**, not the Region hook.

The edit planner may choose a stronger sentence-safe opening within the same Source Region only if doing so preserves standalone comprehension and the source order. It may not arbitrarily move a payoff to the beginning just to manufacture a hook.

### 2.13 Platform duration policy

The system must not hard-code a universal 20–60 second target.

Duration is a per-platform/per-export-profile configuration:

```json
{
  "platform": "youtube_shorts",
  "aspect_ratio": "9:16",
  "max_duration_seconds": 180,
  "preferred_duration_ranges": []
}
```

As of the current plan date, YouTube states that square or vertical videos up to three minutes uploaded after October 15, 2024 are categorized as Shorts for standard channels.

The product should therefore optimize for a configurable duration range rather than assuming that every good short should be under one minute. Other platforms must have independent configuration because platform rules can differ and change.

**Export-profile selection (MVP).** Each job chooses exactly one `export_profile_id` at job creation. All discovery is platform-agnostic and uses the fixed discovery cap of 240 s (2.36.3); the selected export profile affects edit planning, verification duration checks, reframing and rendering. A multi-platform output is implemented as separate jobs, one per export profile. Every plan-level decision artifact records `export_profile_id` and `export_profile_sha256` so the duration/rendering contract is auditable.

### 2.14 Language decision

**MVP language: English.**

This is a product/engineering scope decision, not an assumption that the architecture is English-only.

English-only MVP allows:

- one ASR evaluation target;
- one diarization evaluation target;
- one semantic-analysis prompt/schema;
- English sentence/phrase boundary rules;
- English hook patterns and question/claim detectors;
- simpler benchmark construction.

All language-sensitive components must expose a `language_code` and model/prompt version so additional languages can be added without changing the core artifact schemas.

ASR punctuation must never be the sole source of question or sentence boundaries. Timestamped ASR segments, acoustic pauses, speaker turns, and semantic segmentation must be allowed to override or correct punctuation.

**`language_gate_v1`.** After ASR and before forced alignment, run language identification on up to the first `LANGUAGE_SAMPLE_S = 60 s` of detected speech using the pinned language-ID model in the job config. If at least `LANGUAGE_MIN_WORDS = 20` words are available, the job passes only when `language_code = en` and `confidence ≥ LANGUAGE_CONF_MIN = 0.90`; otherwise it fails closed with `unsupported_language` or `language_uncertain`. If fewer than 20 words are available, return `not_applicable` and allow the no/low-speech event-led path; all speech-dependent extractors must then carry their normal `not_applicable`/`no_evidence` reasons. The gate result, model identity, language code and confidence are persisted in analysis provenance.

#### 2.14.1 Deterministic analysis primitives (v5.0)

The following primitives are implementation-authoritative because later stages depend on their exact outputs.

**`sentence_seg_v1`.** Input is forced-aligned word timing plus optional speaker turns. Start a sentence at the first word of a span. End it at the earliest terminal punctuation boundary that has a usable word timestamp, or at an inter-word gap `>= SENTENCE_GAP_MS` when either the speaker changes at the boundary or the next token begins with an uppercase letter. If a span still exceeds `SENTENCE_MAX_S = 15 s`, split at the largest inter-word gap in the span that is `>= HARD_SPLIT_MIN_GAP_MS = 20 ms`; ties use the earliest gap. If no such gap exists, split at the largest available inter-word gap and mark `synthetic_boundary = true`. The segmentation never splits inside a word.

**Forced alignment is mandatory for transcript-bearing MVP jobs.** When ASR produces at least one word, a job cannot enter `ANALYZING` until `forced_alignment_v1` has produced word-level timestamps. A job with no ASR words may enter `ANALYZING` with alignment status `not_applicable` and is restricted to the event-led/no-text path. If alignment is unavailable after its bounded transport/attempt policy, fail the analysis stage with `alignment_unavailable`; do not silently substitute coarse segment timings for cut-safety decisions.

**`TextTiling_depth_v1`.** For sentence boundary `b` and window `W`, let `L` be the mean embedding of up to `W` sentences ending at `b`, `R` the mean embedding of up to `W` sentences beginning at `b+1`, and `gap(b,W) = 1 - cos(L,R)`. Let `left_peak` be the maximum `gap` over the previous `W-1` boundaries and `right_peak` the maximum over the next `W-1` boundaries, using only complete windows. Then `depth(b,W) = max(0, left_peak - gap(b,W)) + max(0, right_peak - gap(b,W))`. A boundary without a complete pair of windows is `null` and is skipped by downstream change-point logic. `W=5` is used for `semantic`; `W=25` for `topic`.

**Embeddings.** `EMBEDDING_MODEL_ID` is a required immutable config value, not an implicit library default. The model version/checksum and inference backend are stored in the config snapshot; sentence embeddings are persisted as artifacts and reused by cohesion, TextTiling, novelty and repair bridge tests. MVP embedding inference must run deterministically (fixed model, tokenizer, precision and deterministic backend settings) or be treated as a build failure.

**Diarization fallback.** Diarization is optional for single-speaker footage, but when unavailable, `speaker_change`, `qa_start`, `qa_end` and any other speaker-dependent feature are returned as `null` with `m = not_available_in_stage`; no zero is substituted. `speaker_id` is likewise `null`. Features that do not depend on speakers continue normally.

### 2.15 Feature ownership and stage contracts

The taxonomy is reorganized by **when a feature exists**, not only by semantic category.

| Stage | Feature examples |
|---|---|
| Video-level | duration, language, speech density, speaker count, structural profile |
| Event/boundary map | sentence ends, topic transitions, scene changes, audio events, visual activity events |
| Source Region | completeness, region hook opportunity, context dependency, topic/story structure, payoff potential |
| Edit Plan | retained duration, removed spans, compression ratio, interval count, cut density, coherence verification |
| Short Candidate | final hook, final duration, final pacing, final ending, captionability, render/reframe feasibility |
| Candidate-relative | relative hook, emotion, pacing, visual activity, semantic density, local novelty |
| Outcome/label | views, watch time, completion/retention, likes, comments, shares, normalized performance |

No feature should appear in a stage where it cannot yet be computed.

### 2.16 Feature taxonomy and extraction contracts

The original feature taxonomy remains useful, but every feature now requires these fields in implementation:

```text
feature_id
stage
input_artifacts
extraction_method
model_or_library
output_type
version
failure_behavior
cost_class
evaluation_metric
```

The implementation must not create a large undifferentiated list of ~90 features and then attempt to compute all of them for every candidate.

MVP features are selected by stage and validated incrementally.

**Global missing/failure-reason vocabulary.** All feature-like artifacts use one shared enum for `missing_reason` / `m` unless a field explicitly documents a terminal status instead: `no_content`, `no_evidence`, `no_detection`, `no_valid_opening`, `not_run`, `not_applicable`, `not_available_in_stage`, `extraction_failed`, `invalid_output`, `unsupported_language`, `language_uncertain`, `alignment_unavailable`, `lead_in_excessive`, `no_safe_event_end`, `too_short`, `too_long`, `compression_limit`, `fragment_no_speech`, `open_ending`, `bad_start_edge`, `bad_end_edge`, `pipeline_incomplete`, `reframe_signal_missing`. A reason may be extended only by adding it here and versioning the affected artifact schema.

### 2.17 Evaluation before complexity

The adaptive system must prove that it earns its complexity.

Required region-discovery baselines:

1. **Uniform/simple heuristic baseline:** equal or fixed weights over the same boundary signals.
2. **Fixed-duration baseline:** fixed windows snapped to sentence/valid event boundaries.
3. **Adaptive Structural Profile system:** profile-guided discovery.

Primary discovery metrics:

- Region Recall@K: fraction of human-labeled good regions represented by at least one discovered region.
- Boundary error: distance between discovered and human start/end boundaries, with task-appropriate tolerance.
- Redundancy: overlap among discovered regions.
- Search budget: number of Source Regions passed to Tier 1/edit planning.
- Cost per source-video minute.

The adaptive system should only become the default if it improves recall/quality meaningfully at an acceptable search and compute budget. Otherwise, use the simpler baseline.

This rule prevents the Structural Profile machinery from becoming complexity for its own sake.

### 2.18 Outcome/label strategy

Phase 3 must not treat `clip → views` as a clean supervised label.

Performance is affected by:

- creator/channel size;
- platform;
- posting time/date;
- audience;
- title/caption/hashtags;
- thumbnail where relevant;
- distribution/exposure;
- clip age;
- platform algorithm changes;
- whether the user actually chose to publish the candidate.

The system therefore stores **exposure and selection metadata** alongside outcomes.

For each Short Candidate, log at minimum:

```text
source_video_id
source_region_id
edit_plan_id
verified_edit_plan_id
short_candidate_id
tier2_id
display_selection_id
content_style_id
hook_analysis_id
reframe_plan_id
candidate_score_version
score_rank
display_rank
plan_origin (model | user_edit)
parent_edit_plan_id (for user_edit)
whether_shown
whether_selected
whether_published
publication_platform
publication_timestamp
channel/account identifier (privacy-safe internal reference)
performance snapshot timestamps
performance metrics
published_video_id (when published)
published_title
published_description/caption
published_hashtags (when applicable)
account/channel size snapshot at publication
promotion/boosting status (when known)
render_profile_id
```

### 2.19 Selection bias and exploration

The product observes outcomes disproportionately for clips it ranked highly and users selected.

To reduce self-reinforcing training bias:

- retain the full candidate pool and scores, not only the selected clip;
- log user selection separately from model score;
- preserve unselected candidates as preference/exposure data where appropriate;
- introduce controlled exploration later, so some lower-ranked candidates can be evaluated rather than training forever on the current ranker's favorites;
- do not treat an unposted candidate as a negative-performance example.

The first training targets should include both **user preference signals** and **published performance**, rather than relying only on views.

### 2.20 Train/test splitting and leakage prevention

Splits must be grouped by **creator and source video**, never random clip-level splitting.

All clips derived from the same source video belong to the same split. Where creator-level data exists, all source videos from the same creator must stay in one split.

Feature extraction, trend snapshots, and model versions must also respect temporal ordering so future information cannot leak into historical training examples.

### 2.21 YouTube performance data and OAuth

Public Data API statistics can provide basic public metrics such as views, likes, and comments, but creator-specific Analytics data requires authorization. YouTube's Analytics API requires OAuth 2.0 and can provide metrics including average view duration, average view percentage, and audience-retention reports for authorized channel owners.

Therefore:

- **MVP:** performance collection may begin with public video statistics for published outputs where sufficient.
- **Retention-aware training:** requires an explicit YouTube connection/OAuth flow and user consent.
- OAuth tokens must be encrypted, scoped minimally, revocable, and never exposed to the browser beyond the required authorization flow.

The product must not pretend that retention data exists when the user has not authorized access.

### 2.22 Trend pipeline decision

The trend pipeline is downgraded from a core MVP dependency to an **optional feature pending validation**.

The official YouTube captions download API documents 403 errors when the caller lacks sufficient permission to download a caption track.

The trend collector therefore must not assume that it can legally or technically obtain third-party audio/captions for arbitrary trending videos.

Initial trend index inputs should be limited to legally/technically accessible metadata such as:

- title;
- description;
- tags where available;
- category/topic metadata;
- publication time;
- public engagement statistics.

The trend feature remains **experimental** until an ablation demonstrates measurable improvement over the no-trend system.

No scraper or unauthorized third-party audio-download pipeline is a product dependency.

### 2.23 Trend ablation

The evaluation must compare:

```text
Core system without trends
vs.
Core system + trend metadata/retrieval features
```

If trend features do not improve held-out performance or candidate recall/quality consistently, they remain disabled by default.

### 2.24 Rendering specification

Rendering is part of the MVP, not a later polish step.

Every generated short must have a configurable `render_profile_v1`. The default YouTube Shorts profile is:

- vertical 9:16 output;
- target resolution configured by the render profile;
- source audio preserved and normalized;
- captions available as a burned-in or otherwise explicitly configured output;
- cuts use verified audio joins where needed to prevent clicks/pops;
- no invalid aspect-ratio stretching;
- vertical composition is determined by `reframe_plan_v1`.

**Canonical render authorities (v5.0).** `verified_edit_plan` is the sole authority for retained source content, temporal ordering, output timeline and authoritative audio joins. `reframe_plan_v1` is the sole authority for vertical composition. `render_profile_v1` is the sole authority for export-format settings. The renderer consumes all three and never reconstructs timing or composition from an earlier artifact.

`render_profile_v1` contains exactly one value for each export-format field: selected platform, aspect ratio, target resolution, frame rate, video codec, audio codec, pixel format, container, caption mode/style and loudness policy. It records `profile_version`, `config_version` and `config_sha256`. No render job may apply an export-format override outside this immutable profile.

`render_profile_v1` artifact (schema v1):

```json
{
  "render_profile_id": "uuid",
  "schema_version": 1,
  "profile_version": "youtube_shorts@1",
  "config_version": "config@1",
  "config_sha256": "…",
  "platform": "youtube_shorts",
  "aspect_ratio": "9:16",
  "target_resolution": { "width": 1080, "height": 1920 },
  "frame_rate": 30,
  "video_codec": "h264",
  "audio_codec": "aac",
  "pixel_format": "yuv420p",
  "container": "mp4",
  "caption_mode": "burned_in | sidecar | none",
  "caption_style": {},
  "loudness_policy": "source_normalized"
}
```

The renderer receives exactly one immutable `render_profile_v1`, one `verified_edit_plan`, one `reframe_plan_v1`, and one `caption_plan_v1` when `caption_mode != none`. The render request stores the IDs and hashes of the required inputs (caption-plan ID/hash is null when `caption_mode = none`). `render_profile_v1` is export-format authority only; it never contains retained-content or timing decisions.

For landscape talking-head/podcast footage, a usable vertical output requires a reframe strategy. MVP strategies are deterministic: `fixed_center`, `face_aware`, `multi_speaker`, and `blurred_background`.

**Reframe contract.** The reframer consumes only the `verified_edit_plan`, `final_visual_format`, the output-timeline mapping, per-frame face boxes and screen-content boxes/masks. It samples retained output frames at `FACE_SAMPLE_FPS`. For each frame it builds required content points: the centroid of each dominant face (up to two faces) when `final_visual_format` includes faces, and the centroid of the dominant screen-content box when it includes a screen. The candidate 9:16 crop is selected by a deterministic discrete search: evaluate the valid crop centers on a `REFRAME_GRID_PX = 16 px` source-pixel grid plus each clamped required-point centroid, score inclusion of required points/boxes, then break ties by minimum distance to the previous center, then by smallest `(y, x)`. Crop centers are smoothed with a 5-frame median; center jumps greater than `REFRAME_MAX_CENTER_JUMP_PX = 120 px` per frame are limited to the prior center plus the allowed jump. When `multi_speaker` is selected, the renderer uses two vertically stacked portrait panels (one per dominant face), scales each source crop to fit its panel with no stretching, and fills unused panel pixels with the configured blurred background.

**Strategy decision order.** `multi_speaker` is used when two dominant faces are simultaneously required and a single 9:16 crop cannot retain both; otherwise `face_aware` is used when a required face signal exists; otherwise `fixed_center` is used when the required screen/content box fits a fixed center crop; otherwise `blurred_background` is used. If no required content signal exists, `fixed_center` is used and the plan records `reframe_signal_missing`.

**`crop_confidence`.** For each sampled frame, score 1.0 when all required content points/boxes lie inside the safe crop, 0.5 when the primary required point/box is inside but a secondary required item is partially outside, and 0 otherwise. `crop_confidence` is the mean frame score; when no required visual signal exists, set it to `0.0` and reason `reframe_signal_missing`. `status = ok` iff the strategy is `fixed_center | face_aware | multi_speaker` and `crop_confidence >= REFRAME_CONF_MIN`; `status = degraded` when the fallback `blurred_background` is used, no required signal exists, or confidence is below the threshold; `status = infeasible` only when no valid crop/layout exists after evaluating all allowed strategies.

**Captions.** MVP uses `caption_plan_v1`, generated from the verified output-timeline word timings. Captions group consecutive words into 1–2 lines, break at sentence boundaries when possible, otherwise at the nearest word boundary that keeps each line within `CAPTION_MAX_CHARS_PER_LINE = 32`, and never place text outside the configured vertical safe zone. Each caption cue records `output_start_ms`, `output_end_ms`, text, line count and safe-zone placement. The renderer consumes the caption plan without reconstructing timing.

**Loudness.** `loudness_policy = source_normalized` means normalize integrated program loudness toward `LOUDNESS_TARGET_LUFS = -14 LUFS` while keeping true peak `<= TRUE_PEAK_MAX_DBTP = -1.0 dBTP`; values are configurable in `render_profile_v1` and applied after timeline construction.

A Source Region may rank highly but be rejected at final qualification if no usable vertical composition can be produced.

**v5.0:** the reframer reads the `verified_edit_plan` (2.36.9.8a), uses `final_visual_format` from the verified edit timeline (2.37.5) rather than only the coarse Source Region visual format, and writes its own immutable `reframe_plan_v1` artifact. The raw Edit Plan `reframe` field remains null. Tier 2 excludes candidates whose reframe status is `infeasible` (2.39.1 X4).

**Caption artifact `caption_plan_v1` (schema v1):**
```json
{
  "caption_plan_id": "uuid",
  "verified_edit_plan_id": "uuid",
  "schema_version": 1,
  "stage_version": "caption_plan@1",
  "config_version": "config@1",
  "config_sha256": "…",
  "caption_mode": "burned_in | sidecar | none",
  "safe_zone": { "x_min": 0.05, "x_max": 0.95, "y_min": 0.78, "y_max": 0.93 },
  "cues": [ { "output_start_ms": 0, "output_end_ms": 0, "text": "…", "line_count": 1, "safe_zone": "default" } ]
}
```

### 2.25 Pipeline orchestration

Processing is modeled as a resumable state machine, not one long job.

Minimum job states:

```text
CREATED
UPLOADING
UPLOADED
NORMALIZING
NORMALIZED
ANALYZING
DISCOVERING_REGIONS
QUALIFYING_REGIONS
RANKING_REGIONS
CLASSIFYING_STYLE
PLANNING_EDITS
VERIFYING_EDITS
ANALYZING_HOOKS
PLANNING_REFRAME
RANKING_SHORTS
READY_FOR_REVIEW
RENDERING
COMPLETED
FAILED
CANCELLED
```

State mapping (v5.0):

- `DISCOVERING_REGIONS` = discovery Steps 1–3 (raw regions). `QUALIFYING_REGIONS` = qualification (2.9) plus Steps 5–6 (RS, dedup, `R_DISC` cap).
- `RANKING_REGIONS` = Tier 1 (2.38). `CLASSIFYING_STYLE` = `content_style` for every region sent to edit planning (2.37.5); it must finish **before** `PLANNING_EDITS` because the extended-duration rule reads it (2.36.2 rule 2).
- `VERIFYING_EDITS` ends by writing the `verified_edit_plan` artifact (2.36.9.8a); every later stage reads that artifact and never the raw Edit Plan.
- `PLANNING_REFRAME` = reframe planning (2.24) for every plan whose `final_status ≠ FAIL`; it precedes `RANKING_SHORTS` because Tier 2 eligibility needs reframe feasibility.
- `RANKING_SHORTS` may loop back to `PLANNING_EDITS` for **backfill** batches (2.38.6); the loop is bounded by `BACKFILL_MAX_ROUNDS`.
- User-edit reverification is a **candidate-level** lifecycle (below); the job remains in `READY_FOR_REVIEW` while individual candidates move through reverification.

Each stage must:

- have an idempotent input/output contract;
- persist status and heartbeat/progress;
- support retry with bounded attempts;
- record failure reason and stage version;
- write immutable artifacts rather than silently overwriting previous versions;
- allow later stages to reuse completed artifacts.

> **OWNER AMENDMENT 2026-10-04 (to 2.25; version number not bumped -- owner to decide).** For the
> artifact-lifecycle rules above, a **`stage`** means an *orchestrated product-processing stage*
> (e.g. `NORMALIZATION`, `ANALYZING`, `DISCOVERING_REGIONS`, `QUALIFYING_REGIONS`, ...). Internal
> operations inside a stage -- for Phase 3: `ASR`, `language_gate`, `forced_alignment`,
> `sentence_segmentation`, `diarization` -- are **stage sub-steps** and do **not** each require a
> separate canonical artifact. A sub-step must still: have an idempotent input/output contract;
> persist status; record its failure reason; record its stage/sub-step version; record
> provenance; participate in retry/idempotency; and produce data that is incorporated into the
> stage's immutable canonical output artifact (Phase 3: `transcript_v1`). The sub-step records
> reference that canonical artifact and retain their individual provenance. Artifact lineage
> (immutability, reuse, ids/hashes, input lineage, configuration identity, model identity)
> is unchanged; only the *granularity of what counts as a canonical artifact-producing stage*
> changes. Internal transport envelopes between sub-steps (e.g. GPU worker output) are not
> canonical artifacts and never appear in user-facing artifact lists, canonical lineage,
> downstream stage contracts or reproducibility references.

Artifacts should carry:

```text
artifact_id
job_id
stage
stage_version
model_versions
config_version
config_sha256
input_artifact_ids
created_at
checksum
storage_location
schema_version
```

### 2.26 Review UI

The first user-facing result is a review workspace, not just a list of downloaded MP4s.

Each Short Candidate should show:

- preview;
- source timestamp range;
- final duration;
- score/explanation summary;
- hook excerpt;
- why the system selected it;
- edit-plan summary;
- crop/reframe preview;
- captions preview;
- ability to trim start/end within safe boundaries;
- ability to accept/reject the candidate;
- ability to request a simpler edit/no-cut version where applicable (this selects the sibling `minimal` plan of the same region, or a user-edit lineage; it never bypasses verification);
- a "not semantically validated" badge for `LAYER1_ONLY_PASS` plans (2.36.9.1);
- candidates shown in **display order** (2.39.8), with the score-ranked position available in the explanation.

User actions are logged as preference data, distinct from platform performance data.

#### 2.26.1 Candidate lifecycle and user-edit lifecycle (v5.0, review item R37)

Job states remain coarse. Candidate states are independent and may progress concurrently inside one job:

```text
DISPLAYED → USER_EDITING → REVERIFYING → DISPLAYED
                              └→ BLOCKED_USER_EDIT
DISPLAYED → ACCEPTED → RENDERING → RENDERED
```

A verified user edit replaces its parent candidate **in place** for the current display slot and records `replaces_short_candidate_id`. Display selection is not re-run automatically, so a user's local edit cannot reshuffle the review list. An explicit user-requested re-rank creates a new revision of `display_selection_v1`; the prior selection artifact remains immutable.


A user content modification (trim or simpler edit) **never mutates an existing plan**. It creates a **new Edit Plan lineage** with `plan_origin = "user_edit"` and `parent_edit_plan_id`, and passes the same validation pipeline as a model-made plan. A reframe-only modification does not change content or time, so it creates a **new reframe lineage** referencing the same `verified_edit_plan_id` instead of a new Edit Plan.

```text
content edit
  → snap to safe boundaries (sentence-safe units for speech-led, canonical `event_safe_cut_v1` for event-led)
  → new Edit Plan (schema v1, plan_origin = user_edit)
  → Layer 1
  → Layer 2 judge if **speech-led** and transcript has ≥ JUDGE_MIN_WORDS words
       PASS → verified_edit_plan
       REPAIRABLE/HARD_FAIL → reject edit, show reason codes, keep previous plan
  → hook analysis
  → reframe planning
  → Tier 2 feature recomputation and score refresh
  → render

reframe-only edit
  → new reframe_plan lineage referencing the same verified_edit_plan
  → Tier 2 refresh
  → render
```

User edits are never automatically Stage-R repaired because the user explicitly selected the content. `REPAIRABLE` is surfaced as a blocked edit and is not silently rewritten. For a user content edit, `REPAIRABLE` and `HARD_FAIL` are terminal validation outcomes: the candidate enters `BLOCKED_USER_EDIT`, no repaired descendant is created, and the last accepted plan remains intact. A subsequent content change starts a new user-edit lineage from an explicitly chosen parent. A user content edit may not exceed the compression cap or interval limit. User-edit plans are logged as preference data with `plan_origin = user_edit`, distinct from model outputs and platform performance data. Reframe-only preference data is logged separately. Candidate state: `DISPLAYED → USER_EDITING → REVERIFYING → DISPLAYED` on PASS; `DISPLAYED → USER_EDITING → REVERIFYING → BLOCKED_USER_EDIT` on REPAIRABLE/HARD_FAIL.

### 2.27 Legal/privacy requirements

The product must define before public launch:

- acceptable-user-upload policy;
- copyright/DMCA process;
- retention/deletion policy for uploaded media;
- user control over deleting source videos and derived artifacts;
- terms describing how uploaded media and derived features may be processed;
- third-party model/vendor data-processing terms;
- security controls for media and credentials.

Speaker embeddings should **not** be stored by default unless there is a demonstrated product need. If identity-linked biometric or biometric-like data is introduced, obtain jurisdiction-specific legal advice before deployment because applicable privacy obligations vary by jurisdiction.

This document is an engineering plan, not legal advice.

### 2.28 Cost model

The cost model must include all material inference components:

- ASR;
- LLM semantic analysis;
- embeddings;
- optional VLM/CV inference;
- GPU/CPU processing;
- object storage;
- egress;
- database/vector storage;
- queue/orchestration;
- rendering;
- trend data providers if used.

Vendor prices and accuracy claims are planning inputs only and must be re-verified against official pricing/documentation immediately before implementation. The plan must not encode stale vendor prices as architectural facts.

Each pipeline stage should expose an estimated cost class (`low`, `medium`, `high`) and actual measured cost per source-video minute once implemented.

### 2.29 Product differentiation

The product's differentiation is not simply "AI finds clips."

The working product thesis is:

> **Find the complete idea/event first, adapt discovery to the video's structure, then construct and rank a coherent short from that idea.**

The system is intended to differentiate on:

1. adaptive source-region discovery rather than fixed windows;
2. explicit hook + payoff + standalone-comprehension analysis;
3. constrained, verifiable editing rather than arbitrary fragment assembly;
4. multimodal CV/audio/semantic features instead of transcript-only extraction;
5. transparent explanations and editable plans in the review UI;
6. learning from first-party user choices and authorized performance data.

These are product hypotheses, not claims that the system already outperforms existing tools. Competitive evaluation is required before making performance claims.

### 2.30 Reproducibility and tolerance

Exact byte-for-byte feature equality is not required across repeated GPU inference runs.

Each evaluation should define tolerances appropriate to the feature:

- timestamp tolerance;
- score tolerance;
- embedding similarity tolerance;
- segmentation overlap tolerance.

Deterministic components should remain deterministic where practical. Stochastic model components must record model/version/configuration and evaluation tolerance.

### 2.31 Soft-score normalization

Per-video percentile ranks must not be the default universal normalization because they can make approximately 10% of candidates appear "strong" even in a uniform video.

For MVP, prefer:

- calibrated absolute thresholds where meaningful;
- robust z-scores against a source-video baseline where distributional assumptions are acceptable;
- raw normalized measurements plus candidate-relative features;
- percentile/rank features only as additional relative signals.

Uniform or low-variance videos must be allowed to produce uniformly weak scores.

### 2.32 Feature extraction policy

The initial high-value feature set is deliberately small:

1. region/short hook strength and hook type;
2. time-to-core-idea;
3. semantic/idea completeness;
4. standalone comprehensibility;
5. payoff presence and timing;
6. speech rate and pause structure;
7. audio energy/events;
8. scene/shot boundaries;
9. face presence;
10. motion/activity;
11. candidate-relative features;
12. edit compression/density after edit planning.

Advanced facial emotion, sophisticated prosody, broad object recognition, large VLM passes, and trend retrieval are later experiments unless evaluation demonstrates clear value. Features 1 and 2 (hook strength and type; time-to-core-idea) are specified in 2.37.3.

### 2.33 Evaluation dataset

Before training a learned ranker, build a human-labeled evaluation set covering multiple structural types:

- podcast/interview;
- vlog;
- tutorial/education;
- reaction/event;
- storytelling/commentary;
- calm/conversational material;
- visually driven/non-speech material.

For each source video, human annotators should mark:

- meaningful Source Region start/end;
- whether the region is complete/standalone;
- hook quality;
- payoff presence;
- preferred editing style;
- acceptable compression level;
- whether a proposed Edit Plan preserves coherence.

The set must be split by source video and, where possible, creator.

### 2.34 Current decisions

1. Rank **Short Candidates**, not guaranteed virality.
2. Use **two-tier ranking**: region prioritization before edit planning, final ranking after edit planning.
3. Do not build the product around tiny-fragment assembly.
4. Edit plans are order-preserving deletions; no reordering or arbitrary word-level splicing in MVP.
5. Use a verifier to reject incoherent edit plans.
6. Treat compression ratio as a constraint/feature, not an optimization target.
7. MVP language is English.
8. Structural Profile is a routing mechanism whose complexity must beat simple baselines before adoption.
9. Trend retrieval is optional/experimental, not an MVP dependency.
10. YouTube performance/retention collection uses public statistics where available and OAuth-authorized Analytics for private creator metrics.
11. Rendering, orchestration, review UI, legal/privacy controls, and cost measurement are first-class subsystems.
12. The plan distinguishes Source Region, Edit Plan, Short Candidate, and Rendered Short everywhere.
13. *(v4.5)* MVP qualification is deterministic and calls no LLM (2.9).
14. *(v4.5)* After verification, the `verified_edit_plan` is the single authoritative plan artifact (2.36.9.8a).
15. *(v5.0)* The Tier 1 (2.38), Tier 2 (2.39) and `content_style_v1` specifications are **NORMATIVE**. Owner decisions T1–T8 are resolved in 2.39.13.

### 2.35 Open Questions — Candidate Discovery Phase

These are the remaining questions to settle before implementation of candidate discovery:

- **OQ-1:** Exact event-to-region proposal algorithm and pattern library. — *RESOLVED → 2.36.6*
- **OQ-2:** Maximum number of Source Regions per minute / per video and overlap policy. — *RESOLVED → 2.36.7*
- **OQ-3:** Exact maximum Source Region duration before Tier 1 rejection. — *RESOLVED → 2.36.3*
- **OQ-4:** Platform-specific preferred duration ranges and how they influence edit planning. — *RESOLVED → 2.36.2*
- **OQ-5:** Exact boundary scoring/calibration method. — *RESOLVED → 2.36.5*
- **OQ-6:** Human annotation protocol for Source Region recall and boundary tolerance. — *RESOLVED → 2.36.1*
- **OQ-7:** Exact Structural Profile strategy-routing rules. — *RESOLVED → 2.36.4*
- **OQ-8:** **RESOLVED — two-tier ranking/editing order.**
- **OQ-9:** Exact edit-plan unit granularity for speech-led vs event-led content. — *RESOLVED → 2.36.8 (v4.2)*
- **OQ-10:** Exact verifier implementation and coherence thresholds. — *RESOLVED → 2.36.9 (v4.3)*

All questions in this section are resolved and normative for the current plan. Historical wording that previously described them as open is superseded by the resolution subsections below.

### 2.36 Resolutions for OQ-1 to OQ-10

**Status:** OQ-1 through OQ-7 are AGREED and normative for candidate discovery. OQ-9 (v4.2) and OQ-10 (v4.3) are AGREED and normative. Every number marked *initial* is a named configurable constant: implement it as a named constant in one config module (2.36.10), never as a literal. Each resolution ends with the calibration procedure that replaces the guess with a measured value.

**Order of dependency:** OQ-6 (labels) → OQ-4 (durations) → OQ-3 (region cap) → OQ-7 (routing) → OQ-5 (scoring) → OQ-1 (algorithm) → OQ-2 (budgets) → OQ-9 (edit units) → OQ-10 (verifier). Nothing later can be tuned before the labels exist.

**Owner decisions — resolved in v4.1:**

| # | Decision | Resolution |
|---|---|---|
| D1 | Compression ceiling | **AGREED:** `MAX_COMPRESSION_RATIO = 4.0` initially. The ratio is defined as `source_region_duration / final_duration`. A 3-minute region → 45-second short is 4:1 and sits exactly at the initial production ceiling. A 3-minute region → 30-second short would be 6:1 and is therefore rejected in production, but can be studied under `STUDY_MODE`. Nested regions still allow a shorter core to be discovered independently. |
| D2 | Annotation workload | **AGREED:** 56 source videos total: 40 dev + 16 sealed test, with a blind second annotator on at least 30% of videos. Pilot on 8 videos first; all split and sampling procedures are deterministic and creator-disjoint. |
| D3 | Region / edit-planning budgets | **AGREED:** 1.0 discovered regions/min, 0.4 Tier-1 keeps/min, 0.25 edit-planned/min, with per-video floors/caps; `N_SHOW = 10` per video. |
| D4 | Structural Profiles | **AGREED:** hierarchical global + local-per-segment profiles. Local routing is adopted only after the existing paired-recall gate against the simpler baseline. |

---

#### 2.36.0 Canonical shared helpers and invariants (v5.0)

These helpers are normative. Stages must reuse them rather than defining local variants.

**`robust_z_v1(x, center, mad, floor)`**:

```text
if x is null or center is null or mad is null: return null
den = max(1.4826 · max(mad, 0), max(floor, 0))
if den > 0:
    return (x − center) / den
# Deterministic finite fallback. This branch is only reachable when floor = 0 and mad = 0.
if x == center: return 0
return sign(x − center) · ROBUST_Z_ZERO_MAD
```

`ROBUST_Z_ZERO_MAD = 6.0` is finite and deliberately outside the ordinary conversion range; downstream bounded features clip or threshold it. A caller may pass `floor = 0` only when its contract explicitly accepts the zero-MAD fallback. All MVP signal callers use a positive, named floor. No direct `z = (x − center)/(1.4826·MAD)` implementation is permitted outside this helper.

**`event_safe_cut_v1(t)`** is true iff `t` is one of the canonical safe-boundary timestamps for that source video: (0) the exact source-video start or end; (1) a source shot cut; (2) a pause edge belonging to a pause ≥ `EVENT_SAFE_PAUSE_MIN_S = 0.5 s`; or (3) the start/end edge of a continuous interval lasting at least `EVENT_SAFE_SILENCE_MIN_S = 1.5 s` during which RMS ≤ `local_nonspeech_rms_v1(t)` and motion ≤ the video's motion 20th percentile. The same timestamp set is used by discovery, qualification, event editing and Layer 1. An event stage may select an edge only by calling the resolver; it may never construct a timestamp by arithmetic from onset/settle/max-duration values.

**Safe-boundary resolvers.** `latest_safe_before(t)` returns the latest `event_safe_cut_v1` point at or before `t`; it also returns `within_preferred_lookback = ((t − point) / 1000) ≤ preferred_lookback`. `earliest_safe_after(t, max_lookahead)` returns the earliest safe point at or after `t` only when it is no later than `t + max_lookahead`; otherwise it returns null. An event start may use the nearest safe point when the preferred lead-in is unavailable, but the actual lead-in and whether the preference was met are recorded. An event end may use only a resolver-produced safe point. No stage may invent an unsafe timestamp.

**`effective_max_compression_ratio`**:

```text
effective_max_compression_ratio = STUDY_MAX_RATIO if STUDY_MODE else MAX_COMPRESSION_RATIO
```

This value is the sole effective compression ceiling used by generation, post-filtering, verification and study-mode artifacts.

**`local_nonspeech_rms_v1(t)`** returns the 20th percentile of 1 s RMS frames in the rolling 60 s window centered at `t`; edge windows are truncated to the available video. It is evaluated in linear RMS amplitude. The value is the sole threshold used by `event_safe_cut_v1`, dead-air features and pause-related speech features.

**`d_clean_v1(region, export_profile_id)`** is the exact speech cleanup walk of 2.36.8.8 applied once to the unedited region. It returns `d_clean_ms`, applied micro-edits, skipped edits and the final timeline, and uses `plan_min_s` defined in 2.36.2. Tier 1 and Edit Plan generation read this artifact/helper rather than recomputing cleanup independently.

**`super_unit_embedding_v1`** = the L2-normalized mean of the constituent sentence embeddings of a super-unit. Repair bridge tests use this representation.

**Configuration provenance invariant.** Every behavior-producing artifact records `config_version` and `config_sha256`; the referenced config snapshot is immutable and content-addressed.

#### 2.36.1 OQ-6 — Human annotation protocol

**Status: AGREED in v4.1; amended in v4.5 (stratified split, one-to-one matching, cluster bootstrap, Task 3 sampling, Task 4 cross-class pairs — review items R2.1, R2.2, R2.3, R40).**

**Dataset.**

- **56 source videos** total, at least 8 for each of the 7 structural types in 2.33. Each is an excerpt of 15–30 minutes (whole video if shorter). Use only videos the owner has the right to use for evaluation (own, licensed or Creative Commons).
- Split by **source video and creator**, with all videos from a creator kept in one split: **40 dev** and **16 sealed test**, stratified by structural type. The deterministic procedure is: (1) group videos by creator; (2) enumerate creator-group assignments to the sealed-test set that keep the test count at 16, include at least 2 videos of every structural type in test and at least 4 videos of every type in dev, and keep the creator groups disjoint; (3) among feasible assignments choose the lexicographically smallest objective `(abs(test_count-16), total_type_test_deficit, creator_id_sequence)`, where the type deficit is zero for any assignment satisfying the minima; (4) verify that every type has the required test/dev counts and that no creator crosses the split. If no feasible assignment exists, fail the dataset-build gate rather than silently relaxing the minima.
- Pilot first on **8 videos** (one per type plus one extra), then scale. The sealed set is opened once per phase, only for the final comparison.

**Annotators.** A1 = the owner. A2 = a second person, blind, on at least 30% of videos. The protocol passes if at least 60% of A1's grade A/B regions are matched by A2, using the **one-to-one maximum matching** defined below with IoU ≥ 0.5 edges. Otherwise rewrite the guidelines and relabel.

**Task 1 — regions.** "Mark every span you would consider a strong short if you were the creator."

- Start at the first unit a viewer needs. End at the completion of the idea or event. No cap on the count. A label longer than `MAX_SINGLE_IDEA_REGION_S` must be split at its strongest internal boundary or marked out-of-scope with reason `annotation_too_long`; out-of-scope labels are reported and excluded from recall denominator.
- Grade **A** (would post), **B** (acceptable with trimming), **C** (interesting but incomplete or needs context). C is used only to study false positives and is excluded from recall.
- Speech-led regions are labeled by sentence IDs (`start_sentence_id`, `end_sentence_id`) and converted to milliseconds. Non-speech regions use timestamps rounded to 0.1 s.

**Task 2 — per region.** Hook quality 1–5 (the opening), payoff yes/partial/no, standalone yes/needs-context/no, `content_style` (7-value enum, 2.37.5), hook-type tags (up to 2, 2.37.4), and the shortest duration at which the region is still acceptable.

**Task 3 — edit plans.** Label **100** machine-made speech-led Edit Plans, at least 20 in each half-open compression band `[1.0, 1.5)`, `[1.5, 2.5)`, `[2.5, 4.0]`, `(4.0, 6.0]`, `(6.0, 8.0]` (bands above 4.0 come from study mode, 2.36.9.9), **plus at least 15** event-led or low-speech plans (used only for Layer-1-only acceptance, reported separately): pass/fail on coherence, plus reason codes (`dangling_reference`, `missing_setup`, `non_sequitur`, `abrupt_end`, `topic_jump`, `opening_dependent`, `audio_glitch`; `audio_glitch` is human-only). Also rate the opening of every plan 1–5 for hook quality (the Short hook after editing, used by the H-gates, 2.37.7). For every region that has two or more sampled plans, also mark whether the sibling plans differ meaningfully in content (yes/no; used by gate E-G3).

**Task 3 sampling (stratified, v4.5).** Compression bands are always computed from the **final** compression ratio of the verified plan (after micro-edits, 2.36.8.8). Within each band, sample stratified by structural type (2.33): at least 2 plans per type per band where available, drawn round-robin across videos, with no video contributing more than `STUDY_MAX_VIDEO_SHARE` (25%) of a band, and with plans from the same region limited to 2 per band.

**Task 4 — pairwise (later; evaluation-isolated in v5.0).**

- **Dev pool:** `T4_BASE_PAIRS = 400` same-class pairs of distinct Short Candidates, same source video and same comparability class. These pairs are used for Tier 2 development, H-G5, and learned-ranker training/validation. Sampling is constrained to at least `T4_DEV_MIN_VIDEOS` distinct dev videos, no video contributes more than `T4_MAX_VIDEO_SHARE = 0.10`, at least `T4_MIN_CROSS_REGION_SHARE = 0.50` are cross-region pairs, and same-region sibling pairs are reported separately.
- **Sealed pool:** `T4_SEALED_PAIRS = 160` same-class pairs drawn only from the 16 sealed-test videos, with at least `T4_SEALED_MIN_VIDEOS = 12` distinct videos and the same per-video/share/region constraints. The sealed pool is opened once for the final T2-G2 and H-G5 confirmation and is never used for weight fitting, threshold tuning or gate-driven revisions.

The same unordered candidate pair may appear at most once within either pool. Pair sampling uses only the eligible candidate pool and deterministic rules, never Tier 2 score. Use fixed `T4_SAMPLING_SEED`; ties are recorded as 0.5. If the required pool minima are not met, the corresponding evaluation is `NOT_EVALUABLE` and more labels are collected.

**Cross-class evaluation set (separate).** If both `TRANSCRIPT_VERIFIED_PASS` / class A and `LAYER1_ONLY_PASS` / class B candidates exist, collect at least `T4_CROSS_CLASS_PAIRS = 40` pairs across at least `T4_CROSS_CLASS_MIN_VIDEOS = 8` videos in each evaluation pool. These pairs are never used to train or tune the ranker. They are used only for T2-G3.

**Matching rules (v4.5: one-to-one).**

| Metric | Definition |
|---|---|
| Loose edge | A discovered region D and a labeled region L are joined by a loose edge if overlap(D, L) / \|L\| ≥ 0.8 **and** \|D\| ≤ 2.0 × \|L\|. |
| Tight edge | Temporal IoU(D, L) ≥ 0.6. |
| One-to-one matching | Hits are computed by a **maximum-cardinality bipartite matching** over the edges: each discovered region and each labeled region is matched **at most once**, so one broad discovered region cannot hit several labeled regions. Deterministic tie-breaking among maximum matchings: highest total IoU, then lowest D `start_ms`. A *loose hit* = L is matched in the matching over loose edges. A *tight hit* = L is matched in a separate matching over tight edges only. |
| Budget ordering | The discovered list is sorted by `RS` descending (tie: `start_ms` ascending). A budget of *b* regions per source minute uses the first `ceil(b × duration_min)` regions. |
| Recall@budget | Fraction of A+B labeled regions with a loose hit, for budgets of 0.25, 0.5, 1.0 and 2.0 regions per source minute. **Primary = macro** (mean of per-video recalls); micro (pooled) is secondary. Also reported for A only. Per-video values are stored (paired comparisons, cluster bootstrap). |
| Boundary error | For each tight hit: \|Δstart\| and \|Δend\| in seconds; report the median and 90th percentile. Tolerance: speech-led ≤ 3 s start and ≤ 5 s end; event-led ≤ 2 s start and ≤ 3 s end. |
| Redundancy | Mean pairwise IoU among the discovered regions. |
| Uncertainty | Every headline metric is reported with a **video-cluster bootstrap** 95% percentile interval (`BOOTSTRAP_B` = 2000 resamples of videos with replacement). Regions and plans from one video are never treated as independent. |

**Deliverable:** `labels/{video_id}.json` (schema versioned), a labeling guideline document, and the agreement report.

#### 2.36.2 OQ-4 — Platform duration ranges and their influence on editing

**Status: AGREED in v4.1; rule 3 rewritten in v4.5 (R10.4).**

**Export profiles** (2.13 schema, with the ranges filled in). All values are *initial*.

| Profile | `min_s` | `primary_range_s` | `extended_range_s` | `max_s` |
|---|---:|---|---|---:|
| `youtube_shorts` | 8 | 20–60 | 60–120 | 180 |
| `tiktok_default` | 8 | 20–60 | 60–120 | configured; verify at implementation |
| `instagram_reels_default` | 8 | 15–60 | 60–90 | configured; verify at implementation |

Platform limits differ across sources and change, so `max_s` for anything except YouTube Shorts must be re-verified against official documentation before implementation.

**Rules.**

1. Discovery is **platform-agnostic**. `MAX_REGION_S` is fixed at 240 s (2.36.3) and does not depend on the export profile. Platform profiles affect edit planning, verification, reframing and rendering only.
2. The `extended_range_s` is allowed only when the region's `content_style` (2.37.5) is `story`, `tutorial` or `explanation` **and** the verifier passes.
3. Target-duration procedure for one Source Region. **The single normative procedure is 2.36.8.7**; this rule states the priorities so the two never disagree:
   1. Compute `D_clean`, the duration after applying only the pause-shortening micro-edits (2.36.8.8; no content deletion; filler-word removal is LATER).
   2. The **duration profile of a plan is decided by its final duration** (after micro-edits): `primary` if `final ≤ primary_range_max`; `extended` if `primary_range_max < final ≤ extended_range_max` **and** rule 2 allows it; otherwise the plan is invalid (`too_long`). `max_s` stays the absolute platform ceiling (`≥ extended_range_max`). Compression feasibility uses `effective_max_compression_ratio`.
   3. Build order (priority): `minimal` → `balanced` at the primary cap → `balanced` at the extended cap (only if `D_clean > extended_range_max` and rule 2 allows) → `aggressive`. Deduplicate, then keep the first `MAX_PLANS_PER_REGION` survivors. Deleting the lowest-value units to fit a cap stops at the intensity's compression ratio cap.
   4. Define `plan_min_s = EVENT_MIN_FINAL_S` (6 s) for event-led plans and `profile.min_s` for speech-led plans. If `D_clean < plan_min_s`, reject with `too_short`. Event-led completeness does not override this minimum. If nothing can be built, reject with the reason codes of 2.36.8.7 rule 5.
4. Up to **3 model plans** per region by edit intensity (2.36.8.7), using at most **2 duration profiles** (`primary`, `extended`). Final speech-led shorts use the export profile's `min_s`; final event-led shorts use `EVENT_MIN_FINAL_S = 6 s`. `MIN_REGION_SPEECH = 10 s` and `MIN_REGION_EVENT = 6 s` remain Source Region discovery/qualification minimums and are not substituted for final-duration rules.
5. Tier 2 uses final duration only as a context feature and as a hard gate (outside `[min_s, max_s]` is excluded). It must not encode a monotone "shorter is better" prior.

**Calibration.** After Task 2 labels exist, compare labeled "shortest acceptable duration" with `D_clean`. Move the primary range if more than 25% of A/B regions fall outside it.

#### 2.36.3 OQ-3 — Maximum Source Region duration and compression ceiling

**Status: AGREED in v4.1; two-cap definition added in v4.5 (R5).**

**Decision.** The region cap follows from the compression ceiling instead of being an arbitrary number.

For clarity, `compression_ratio` is defined as:

```text
compression_ratio = source_region_duration / final_duration
```

Thus 4.0 means a 4:1 source-to-final compression ceiling.

```text
MAX_COMPRESSION_RATIO = 4.0                       (production default)
STUDY_MAX_RATIO        = 8.0                       (study-only; 2.36.9)
effective_max_compression_ratio = STUDY_MAX_RATIO if STUDY_MODE else MAX_COMPRESSION_RATIO
MAX_REGION_S          = 240 s (fixed discovery constant; independent of export profile)
SINGLE_IDEA_EXTENSION = 1.25
ABSOLUTE_REGION_CEILING = 360 s
MAX_SINGLE_IDEA_REGION_S = min( SINGLE_IDEA_EXTENSION × MAX_REGION_S, ABSOLUTE_REGION_CEILING ) = 300 s
MIN_REGION_SPEECH     = 10 s (speech-led)
MIN_REGION_EVENT      = 6 s (event-led)
```

**Two caps, one rule.** The discovery walk (2.36.6 Step 3) stops at `MAX_REGION_S`, **unless** the region is a proven single-idea unit at that moment (defined in 2.36.6 Step 3 (d)); only then may it continue, up to `MAX_SINGLE_IDEA_REGION_S`. A region longer than `MAX_REGION_S` is flagged `single_idea = true`, and qualification QC-5 (2.9) applies the matching cap.

**Consequence to keep in mind.** With `MAX_COMPRESSION_RATIO = 4.0`, a single-idea region of 300 s cannot be edited below 75 s, so it can only yield an `extended`-profile plan (allowed only for `story`, `tutorial`, `explanation`, 2.36.2 rule 2); otherwise it is rejected with `compression_limit`. A shorter nested core (2.36.7) is the way to obtain a primary-range short from such an idea.

- A region longer than `MAX_REGION_S` that is not a single-idea unit is **split at its strongest internal topic or Q→A boundary**, not truncated.
- Compression policy for Edit Plans: ratio ≤ 2.0 uses standard verifier thresholds; 2.0–4.0 requires the strict thresholds in 2.36.9; above 4.0 is rejected until the study says otherwise.
- The 30-second core inside a 4-minute story is still reachable: discovery may return **nested** regions (2.36.7), so the 30-second core is its own region rather than an 8:1 edit of the whole story.

**Calibration.** The compression study in 2.36.9 sets `MAX_COMPRESSION_RATIO`. `MAX_REGION_S` is recomputed from it, with an absolute ceiling of 360 s.

#### 2.36.4 OQ-7 — Structural Profile routing rules

**Status: AGREED in v4.1.**

**Restored requirement (D4): the profile is hierarchical.** Compute one global profile and a **local profile per segment**. The routing below runs per local segment.

**Local segmentation algorithm** (deterministic):

1. Build one feature vector per `PROFILE_BIN_S = 10` second bin: `[speech_ratio, turn_rate, words_per_min, cut_rate, motion_mean, rms_mean_db, rms_std_db, face_ratio]`.
2. Robust-scale each feature over the video with `robust_z_v1(x, median, MAD, floor)`. Floors: speech_ratio 0.05, turn_rate 1, words_per_min 15, cut_rate 1, motion 0.01, rms_mean 2 dB, rms_std 1 dB, face_ratio 0.05.
3. For each bin b with complete left/right windows of `CP_WINDOW_BINS`, `d(b) = ‖ mean(z[b−CP_WINDOW_BINS…b−1]) − mean(z[b…b+CP_WINDOW_BINS−1]) ‖₂`; bins with incomplete windows are skipped.
4. A change point is a local maximum of `d` with `d > max(mean(d) + CP_SIGMA·std(d), CP_MIN_DIST)`, with non-maximum suppression within ±`CP_WINDOW_BINS` bins. Ties use the earliest bin.
5. Segments lie between change points. A segment shorter than 60 s merges into the neighbor across the change point with the smaller `d`. A video shorter than 180 s is a single segment.

**Driver indices** per segment, each in [0, 1] (`norm(x, N) = min(1, x / N)`):

```text
I_sem = speech_density × norm(words_per_min, 140)
I_vis = mean( norm(cut_rate, 12 cuts/min), norm(motion_mean, 0.15) )
I_evt = mean( norm(audio_peak_rate, 3/min), norm(motion_peak_rate, 3/min) )
```

An audio or motion peak is a local maximum with robust z ≥ 2 against a 60 s rolling median/MAD, at least 3 s apart. A `null` input is excluded from its mean; if every input is null the index is 0.5 (neutral).

**Routing (strategy selector, as v3 requires).**

| Strategy | Active when |
|---|---|
| `S_sem` (semantic-led) | `I_sem ≥ 0.30` |
| `S_vis` (visual-led) | `I_vis ≥ 0.35` |
| `S_evt` (audio/event-led) | `I_evt ≥ 0.35` |
| `S_hybrid` | none of the above is active → activates all three |

Strategies are **additive**: proposals from all active strategies are pooled. This means routing changes weights, never eligibility (recall guard). `S_sem` is also always allowed when `speech_density ≥ 0.15`.

**Family weights.** For each boundary family, `w_f = max(over active strategies of the table value)`, floored at `WEIGHT_FLOOR = 0.1`.

| Family | `S_sem` | `S_vis` | `S_evt` |
|---|---:|---:|---:|
| `qa_start`, `qa_end` | 1.0 | 0.1 | 0.1 |
| `topic` | 0.9 | 0.3 | 0.2 |
| `semantic` | 0.8 | 0.3 | 0.2 |
| `hook_potential` | 0.6 | 0.2 | 0.2 |
| `speaker_change` | 0.5 | 0.1 | 0.1 |
| `pause` | 0.4 | 0.2 | 0.2 |
| `activity_change` | 0.1 | 1.0 | 0.6 |
| `shot_cut` | 0.1 | 0.7 | 0.3 |
| `audio_event` | 0.2 | 0.4 | 1.0 |

The uniform baseline (2.17) sets every weight to 0.5.

**Adoption gate.** Profile routing becomes the default only if, on the dev set and then the sealed test set, the **median per-video paired Recall@budget improvement over the uniform baseline is ≥ 5 percentage points** and at least 60% of videos are no worse. Local segmentation must clear the same gate against global-only routing. Otherwise the simpler variant stays the default.

#### 2.36.5 OQ-5 — Boundary scoring and calibration

**Status: AGREED in v4.1.**

**Per-family scores** are in [0, 1] and use absolute scaling (2.31), never percentile rank alone.

| Family | Score |
|---|---|
| `sentence_start` / `sentence_end` | Gate only (not scored): 1 at a sentence edge, else 0. |
| `speaker_change` | 1 at a turn boundary, else 0. |
| `shot_cut` | 1 at a cut, else 0. |
| `pause` | `min(1, pause_ms / 1200)` for pauses ≥ 600 ms. |
| `audio_event` | `clip((z − 1.5) / 2.5, 0, 1)`, z = `robust_z_v1` of the RMS peak against a 60 s rolling baseline with `RMS_MAD_FLOOR`. |
| `activity_change` | `clip((z − 1) / 3, 0, 1)`, z = `robust_z_v1` of \|mean motion 5 s before − mean motion 5 s after\| against the 60 s baseline; zero if the raw difference is below 0.03. |
| `semantic`, `topic` | TextTiling depth `d` on sentence embeddings (window 5 sentences for `semantic`, 25 for `topic`). `z = robust_z_v1(d, median(d), MAD(d), DEPTH_MAD_FLOOR)`. Score `= clip((z − 1) / 3, 0, 1)` **if** `d ≥ DEPTH_ABS_MIN` (initial 0.08 for `semantic`, 0.06 for `topic`), else 0. When `MAD(d)=0` and `d=median(d)`, `z=0`. The absolute floor lets a uniform video have uniformly weak scores. |
| `qa_start` | 1.0 for a question sentence followed by a speaker change; 0.5 for a rhetorical question (same speaker continues); else 0. |
| `qa_end` | 1.0 at the end of the answering turn (speaker changes back or a new question begins), else 0. |
| `hook_potential` | Lexical MVP score (question +0.4; number/currency/percent +0.3; strong-claim word list +0.2; filler or back-reference opener −0.4; clamp to [0, 1]). LLM-based version is LATER. Also named `hook_lexical@1`: used for opening selection (2.36.8.5) and Tier 1 only, not by Tier 2 (2.37.1). |

`is_question` must not rely on ASR punctuation alone (2.14). Use punctuation OR an interrogative-opener rule OR a rising-pitch check; log which fired.

**Start and end scores** combine the families with role weights `r_f` and the local routing weights `w_f` (2.36.4):

```text
StartScore(t) = Σ r_f^start · w_f(seg(t)) · s_f(t)  /  Σ r_f^start · w_f(seg(t))
EndScore(t)   = Σ r_f^end   · w_f(seg(t)) · s_f(t)  /  Σ r_f^end   · w_f(seg(t))
(sums run over the families whose input signal is available at t)
If the denominator is 0, the score is 0.0 and carries `missing_reason = no_evidence`. That state is not treated as evidence of a weak boundary.

A boundary family is **null only when its input signal is unavailable in the stage**. A measured value of zero is a real observed value and remains in the denominator. Examples: without diarization, `speaker_change` and `qa_*` are null; without video analysis, visual families are null; available signals that simply have no event at `t` remain numeric 0. Threshold calibration records the set of available families used on the dev data.
```

| Family | `r^start` | `r^end` |
|---|---:|---:|
| `qa_start` | 1.0 | 0 |
| `qa_end` | 0 | 1.0 |
| `hook_potential` | 0.8 | 0 |
| `topic` | 0.6 (boundary at t) | 0.7 (boundary right after t) |
| `semantic` | 0.6 | 0.5 |
| `pause` | 0.3 (before) | 0.5 (after) |
| `speaker_change` | 0.4 | 0.4 |
| `activity_change` | 0.8 (onset) | 0.6 (settle) |
| `audio_event` | 0.8 (onset) | 0.3 |
| `shot_cut` | 0.3 | 0.3 |

Thresholds `START_MIN` and `END_MIN` start at 0.35.

**Calibration (after labels exist).**

1. Label every candidate boundary as positive if it lies within tolerance (2.36.1) of a human region start (or end).
2. Set `START_MIN` / `END_MIN` to the lowest values that keep ≥ 90% recall of labeled edges on the dev set. Recall comes first because Tier 1 exists to avoid misses.
3. Fit a non-negative, L2-regularized logistic regression on the family scores. Adopt the fitted weights only if held-out average precision beats the hand weights by ≥ 0.03. Version the weights either way.

#### 2.36.6 OQ-1 — Event → region proposal algorithm and pattern library

**Status: AGREED in v4.1; amended in v4.5 (start-candidate bound R4, single-idea rule R5, cohesion function R6, pattern requirements R7, event settle semantics R19, qualification cross-reference R8).**

**Algorithm — AGREED for MVP** (no LLM in MVP; fully deterministic given the boundary map).

```text
INPUT   boundary_map, local_segments (with family weights), sentences, sentence embeddings

STEP 1  Seeds
   speech seeds
     QA     sentence with qa_start ≥ 0.5
     HOOK   sentence start with hook_potential ≥ 0.5
     TOPIC  boundary with topic score ≥ 0.6 (start of a topical unit)
   event seeds
     EVENT  audio_event ≥ 0.6 or activity_change ≥ 0.6, with no speech seed within ±10 s
   seed_strength = family score × w_f(segment)
   keep the top SEEDS_PER_10MIN (10) seeds in every 10-minute window

STEP 2  Start candidates (per seed)
   speech: exactly the seed's own sentence start, plus the single best OTHER sentence start in
           [seed − LOOKBACK_S (20 s), seed] with StartScore ≥ START_MIN (if any) → at most 2 starts per seed.
   event : start = latest `event_safe_cut_v1` point at or before onset.
           Record `actual_lead_in_s = (onset − start) / 1000` and `lead_in_within_target`.
           If `actual_lead_in_s > EVENT_MAX_LEADIN_S`, reject with `lead_in_excessive`; do not invent an arithmetic start timestamp from the preferred lead-in constant.
           If no safe boundary exists before onset, reject with `no_safe_event_start`.

STEP 3  End candidates (per start)
   speech: walk forward over sentence ends until the first STOP:
     (a) qa_end reached
     (b) next boundary has topic score ≥ TOPIC_STOP
     (c) continuity breaks: cohesion(t) < CONT_MIN at 2 consecutive evaluable positions; STOP is the sentence end t of the first position
     (d) length reaches MAX_REGION_S — stop, UNLESS the region is a proven single-idea unit at that moment (P1/P3, no earlier stop,
         every evaluable cohesion ≥ CONT_MIN); then continue to MAX_SINGLE_IDEA_REGION_S and stop unconditionally there
     (e) source video ends (`stop_reason = end_of_video`)
   Keep up to 3 end candidates in this order: earliest complete candidate, the natural completion at the STOP point **always included even if
   `EndScore < END_MIN`**, and the best remaining candidate by `EndScore ≥ END_MIN`. Natural STOP candidates are still subject to qualification.

   event:
     1. Let `settle_window = [onset + LEADOUT_MIN_S, start + MAX_EVENT_S]`. Search only inside this bounded window for the first continuous
        stable interval of at least `EVENT_SAFE_SILENCE_MIN_S` where RMS and motion are both back within 20% of pre-event baseline.
     2. If a settle interval is detected, set `settle_source = detected`, `settle_ms = START of that stable interval`, and choose
        `event_end = earliest_safe_after(settle_ms + SETTLE_TAIL_MIN_S, SETTLE_SNAP_MAX_S)`. If none exists, choose
        `latest_safe_before(start + MAX_EVENT_S)` only when it is after `settle_ms + SETTLE_TAIL_MIN_S`; otherwise reject `no_safe_event_end`.
     3. If no settle interval is detected within the bounded search, set `settle_source = capped`, `settle_ms = null`, and choose
        `event_end = latest_safe_before(start + MAX_EVENT_S)` only when it is after onset; otherwise reject `no_safe_event_end`.
     4. All event starts/ends are resolver-produced safe boundaries. Record onset, settle source/value, capped end (when present), actual lead-in,
        and whether the preferred lead-in was met.


STEP 4  Qualification: run checks QC-1 … QC-6 of 2.9 on every raw region (a failing region is kept in the
        artifact with its reasons, but is removed from steps 5–6); the region must also contain its seed

STEP 5  Region score (used only for dedup and budgeting, never as the final score)
   RS = 0.35·StartScore + 0.35·EndScore + 0.15·seed_strength + 0.15·pattern_completeness
   pattern_completeness = (start_event + end_event) / 2 ∈ {0, 0.5, 1}, with the two booleans defined per pattern
   in the "Pattern required events" table below (only detectable signals are used)

STEP 6  Dedup and budget (2.36.7)
```

**Bound.** At most 2 starts (the seed's own start plus the best other one) × 3 ends = 6 regions per seed, at most 10 seeds per 10 minutes, so at most 60 raw regions per 10 minutes before dedup. Event seeds have exactly 1 start. No start/end pair is enumerated.

**Deterministic ordering rule.** Whenever a stage selects, truncates, deduplicates or enumerates by a score, its total order is `(primary score(s) descending, start_ms ascending, end_ms ascending, stable ID ascending)` unless a more specific normative tie-break below replaces it. Windowing is **tumbling 10-minute source-time windows**: `[0,600), [600,1200), ...`; boundary timestamps exactly at a window end belong to the next window.

**Pattern library (initial).**

| ID | Pattern | Seed | Start rule | End rule |
|---|---|---|---|---|
| P1 | Question → answer | `QA` | question sentence, or one preceding setup sentence | `qa_end` |
| P2 | Hook start → natural completion (what lies between is not a detected event) | `HOOK` | the hook sentence | best `EndScore` before a topic stop or continuity break |
| P3 | Topic unit | `TOPIC` | the topic boundary | the next topic boundary (or the strongest Q→A or pause split if longer than `MAX_REGION_S`) |
| P4 | Event → reaction | `EVENT` | lead-in before onset | settle point |
| P5 | Story (setup → escalation → payoff) | LLM-labeled | — | — (**LATER**, needs `story_payoff`) |

**Pattern required events (v4.5).** Each pattern has exactly two required, detectable events. `pattern_completeness = (start_event + end_event) / 2`.

| ID | `start_event` is true iff | `end_event` is true iff |
|---|---|---|
| P1 | the region's first or second sentence has `qa_start ≥ 0.5` | the region's last sentence has `qa_end = 1.0` |
| P2 | the first sentence has `hook_potential ≥ 0.5` | the end is a natural completion: stop (a), (b) or (c), a local maximum of `EndScore ≥ END_MIN`, **or an end-of-video stop whose last sentence passes QC-6**; false for a length-cap stop (d) or an open/incomplete video-end stop |
| P3 | the topic score at the region start ≥ 0.6 | the topic score at the boundary right after the region end ≥ `TOPIC_STOP`, the end is a `qa_end` / pause split, **or a QC-6-valid end-of-video completion** |
| P4 | an onset (`audio_event ≥ 0.6` or `activity_change ≥ 0.6`) lies inside the region | `event.settle_source = detected` |

**Cohesion function (v4.5, exact).** Sentence embeddings `e_i` are L2-normalized. Positions `t` are sentence indices counted from the region's first sentence (`t = 1 …`).

```text
A(t) = normalize( mean( e_{t-4}, …, e_t ) )        the last min(COH_A_WINDOW = 5, t) sentences, inside the region only
B(t) = normalize( mean( e_{t+1}, …, e_{t+3} ) )    the next min(COH_B_WINDOW = 3, remaining) sentences
cohesion(t) = cos( A(t), B(t) )
evaluable(t) = ( t ≥ COH_A_MIN = 3 ) and ( |B(t)| ≥ COH_B_MIN = 2 )       otherwise cohesion(t) = null
```

A `null` position is skipped: it is neither a break nor a non-break and does not reset or extend the "2 consecutive" streak. If the source video ends before `B` can reach `COH_B_MIN` sentences, the walk ends there (stop (e)).

**Continuity threshold.** `CONT_MIN` is set from data instead of a guess (measured with the exact function above at every evaluable position inside labeled A/B regions): the 25th percentile of the cohesion measured across sentence transitions *inside* labeled A/B regions on the dev set. Cosine scales differ between embedding models, so recalibrate whenever the model changes.

**Optional LLM boundary refinement (EXPERIMENTAL).** After Step 6, an LLM may see a region plus 30 s of context each side (≤ 4000 tokens) and shift the start or end by at most 3 sentences. Adopt it only if the tight-hit rate improves by ≥ 5 points on the dev set.

**Acceptance gate.** Recall@1.0 regions/min ≥ 0.85 (loose hit, grades A+B) and at least 60% of hits are tight hits. If missed, iterate on this algorithm before starting edit planning.

#### 2.36.7 OQ-2 — Region counts and overlap policy

**Status: AGREED in v4.1.**

**Budgets** (per source minute, with floors and caps per video):

| Stage | Rate | Floor | Cap |
|---|---:|---:|---:|
| Discovery output after dedup (`R_DISC`) | 1.0 | 6 | 90 |
| Tier 1 keeps (`R_T1`) | 0.4 | 4 | 40 |
| Sent to edit planning (`R_EDIT`, counts regions; each region yields up to 3 plans, 2.36.8.7) | 0.25 | 3 | 25 |
| Shown to the user (`N_SHOW`) | — | — | 10 |

A 60-minute podcast therefore yields about 60 discovered regions, 24 kept by Tier 1, 15 edit-planned and 10 shown. How Tier 1 splits the 24 kept regions into the 15 sent first and the 9 held as backfill is defined in 2.38.6. All counts here are counts of **qualified** regions (2.9.1).

**Overlap policy** (temporal IoU):

- IoU ≥ 0.7: keep the higher `RS`.
- 0.5 ≤ IoU < 0.7: keep both only if their `pattern_id` differs.
- **Nesting** is allowed: an inner region is kept alongside its outer region if the inner is ≤ 60% of the outer's length and has its own seed.
- The shown list is produced by **display selection** (2.39.8: maximal marginal relevance with λ = 0.7, at most one plan per region, no two shorts overlapping in source time by more than 30% of the shorter one). It is a separate step from the Tier 2 score order.

**Minimum yield rule.** If discovery returns fewer than `max(3, duration_min / 10)` regions, lower `START_MIN`, `END_MIN` and the seed thresholds by 20% and rerun once. If it is still below the floor, return what exists with `status = "low_yield"`. Never fabricate windows.

**Calibration.** Plot Recall@budget on the dev set. Set `R_DISC` at the knee, the smallest budget reaching ≥ 90% of the recall obtained at 2.0 regions/min. Set `R_T1` and `R_EDIT` from the measured Tier 1 precision and from the measured edit-planning cost per region.

#### 2.36.8 OQ-9 — Edit Plan generation

**Status: AGREED in v4.2** (owner decisions E1–E6, table at the end of this section); **amended in v4.5** (R10.1 G0 retired, R10.2/R11 no word deletion, R10.3/R12 final band from final timing, R10.4/R13 extended priority, R10.5/R14 DP base state, R10.6/R15 `context_dependency`, R10.7/R16 value-function bounds, R20 stable cut ids, R25 provisional crossfades, R26 E-G3).

##### 2.36.8.1 Scope and contract

**Input:** one qualified Source Region (2.9), its sentences with word timestamps, sentence embeddings, boundary map, the export profile (2.36.2), and the video's signals (RMS, motion).
**Output:** 0 to `MAX_PLANS_PER_REGION` (3) Edit Plans, each order-preserving and made only of deletions. Or zero plans plus a `reject_reason`.
**Never:** reorder, splice inside a sentence, synthesize speech, delete individual words, or search outside the algorithm below.
**Cost class:** low. Everything in this section is deterministic and CPU-only. No LLM is called here (the LLM judge is 2.36.9).
**Canonical order per plan (v4.5):** DP → micro-edits (2.36.8.8) → final timeline → recompute final duration, compression ratio, compression band and duration profile from that timeline → Layer 1 (2.36.9.2, which also fixes the audio joins and recomputes the timeline once more).

##### 2.36.8.2 Edit units — speech-led regions

**Step 1 — Base units.** One unit = one ASR sentence, as produced by the sentence segmentation of 2.14 (not by ASR punctuation alone). Fields: `unit_id, start_ms, end_ms, text, speaker_id, word_count, filler_share`.

**Step 2 — Run-on guard.** If a sentence is longer than `LONG_UNIT_S` (15 s), split it at the longest inter-word gap of at least `SPLIT_PAUSE_MS` (500 ms). Repeat until every piece is ≤ `LONG_UNIT_S` or no gap qualifies. Every piece boundary created this way is a gap ≥ 500 ms, so the pieces are separately deletable units (flagged `split_from_run_on = true`). Reason: ASR often returns one huge unpunctuated sentence, which would make a region un-editable.

*Retired in v4.5 (R10.1): glue rule G0.* v4.2 glued split pieces whose boundary gap was under 500 ms, but pieces are only created at gaps ≥ 500 ms, so G0 could never fire. A second, weaker split threshold would not help either: pieces split at a weak gap and glued back are indistinguishable, to the DP, from the unsplit sentence. G0 is removed rather than given a second threshold; `SPLIT_PAUSE_MS` may be lowered later only by an experiment that also defines what a weak-gap cut costs.

**Step 3 — Glue groups (atomic).** Units in one group are kept or deleted together. Apply in order:

| Rule | Group |
|---|---|
| G1 | A question sentence and the first sentence of its answer (the first sentence after the speaker change, or after the question if the same speaker continues). |
| G2 | A sentence that starts with an unresolved reference (`it, that, this, they, those, these, he, she`) or a dependent connective (`so, because, but, which, and then, also, however`) is glued to the previous sentence. Chains merge into one group. |
| G3 | Enumerations, quotations, list intros (**LATER**, not in MVP). |

The word lists of G2 are the versioned config `glue_lists@1`: `G2_REF` = {it, that, this, they, those, these, he, she}; `G2_CONNECTIVE` = {so, because, but, which, and then, also, however}. The same lists are used by `context_dependency` (2.9.3).

Not in MVP (**LATER / EXPERIMENTAL**): semantic couplings such as setup→payoff, action→reaction, demonstration→result. These need semantic labeling, so they are not deterministic. If they are added, they come from at most one structured LLM annotation call per region, behind a flag, gated by an ablation on Task 3 labels.

Remaining coherence risks (non-adjacent antecedents, semantic dependencies) are **not** modeled here. The verifier (2.36.9) is the safety net; the `semantic_role` and `reference_dependencies[]` metadata are dropped from MVP because nothing consumes them.

**Step 4 — Super-units.** Each glue group collapses into one super-unit `U_i` with duration `d_i`, value `v_i = Σ v(u)` over its members (function below), and a `forced` flag. The DP works only on super-units. `n` is typically 20–120.

##### 2.36.8.3 Edit units — event-led regions (MVP: trim only)

A complete event is atomic, and event regions are capped at `MAX_EVENT_S` (45 s). MVP event editing is trim-only.

1. An event-led region produces **one** plan with **one** retained interval (no internal deletions and no pause-shortening micro-edits).
2. Start and end may be tightened only at boundaries satisfying `event_safe_cut_v1` (2.36.0), with a minimum retained duration of `EVENT_MIN_FINAL_S = 6 s`. Event-led trim-only plans use `EVENT_EDIT_MAX_RATIO = 1.5` as their generation compression cap; Layer 1 recomputes the final ratio after authoritative audio joins.
3. Tightening keeps the seed onset with at least `EVENT_ONSET_MARGIN_S` (1.0 s) of lead-in unless the chosen edge is the latest safe point at or before onset. When `settle_source = detected`, it keeps the whole main-event span `[onset_ms, settle_ms]` and at least `SETTLE_TAIL_MIN_S` (1.5 s) after `settle_ms`. When `settle_source = capped`, there is no detected settle point (`settle_ms = null`); the resolver-produced `capped_end_ms` is the event end and no settle-tail requirement is applied.
4. Internal event deletions (for example, skipping a failed attempt) are **LATER**. Event sub-structure `peak / reaction` is not modeled in the MVP boundary map.
5. The plan records `event.onset_ms`, `event.settle_ms`, `event.settle_source` and the actual start lead-in; Layer 1 checks them (2.36.9.2).
6. If no boundary satisfying `event_safe_cut_v1` can produce a valid end before `MAX_EVENT_S`, reject the event region with `no_safe_event_end`; never invent an unsafe timestamp.

##### 2.36.8.4 Unit value function (deterministic)

```text
v(u) = 0.4·novelty(u) + 0.3·density(u) + 0.3·payoff_proximity(u) − 0.5·filler(u)
novelty(u)           = clip( 1 − max cosine similarity between u and earlier units in the region, 0, 1 )   (0 for the first unit)
density(u)           = min(1, content_words_per_second(u) / DENSITY_NORM)      DENSITY_NORM initial 2.5
payoff_proximity(u)  = 1 for the completion unit, else max(0, 1 − distance_in_units / PAYOFF_DECAY_UNITS)   initial 8
filler(u)            = filler_and_hedge_tokens / word_count                                   ∈ [0, 1]
```

Every term is bounded to [0, 1]. `filler_and_hedge_tokens` is the number of non-overlapping matches, in the unit, of the versioned vocabulary `filler_hedge_vocab@1` (case-insensitive, whole-token match, multi-word entries matched longest-first). **Initial vocabulary** — fillers: `um, uh, erm, er, ah, you know, i mean`; hedges: `kind of, sort of, basically, actually, literally, i guess, maybe, probably`. Content words (for `density`) are tokens not in the versioned list `stopwords_en@1` and not fillers. Both are configuration artifacts; changing either changes `stage_version`. The filler list here is unrelated to the hook opener filler list of 2.37.3.

`transition_penalty`, `reference_risk` and `coherence_risk` are **not** in the value function. Cuts are penalized in the objective by `LAMBDA_CUT`; reference and coherence problems are hard constraints (glue rules) or the verifier's job. Putting a risk term into the utility would invent an unmeasured number and would mix generation with verification.

##### 2.36.8.5 Opening and completion (forced units)

**Applies to `balanced` and `aggressive` only.** The `minimal` plan retains the complete Source Region after the allowed cleanup, so its opening is the region's first super-unit and its completion is the region's last super-unit. Its Short-hook score is recorded but not optimized.

1. **Completion unit** = the final super-unit of the region. It must be retained. Because the discovery qualification requires a complete ending, the completion is the region's final sentence/super-unit unless a future edit architecture explicitly changes this rule.
2. **Opening candidates** = the first `OPENING_CANDIDATES` (3) **super-unit starts** whose first sentence is sentence-safe, does not begin with a G2 reference or connective, and whose removal of earlier material passes `context_dependency(candidate opening sentence) ≤ CTX_MAX`. A sentence inside a G1/G2 super-unit is never an opening candidate.
3. For each opening candidate compute the Short-hook score (2.12 / 2.36.5 lexical MVP). Each candidate produces its own DP run with that opening forced kept and all earlier super-units deleted. The payoff is never forced to the front.
4. **Opening tie rule.** For each intensity, let `O*` be the best post-filter-feasible DP objective across opening candidates. Keep candidates whose best feasible objective is at least `(1 − OPENING_OBJ_TOL) · O*` (`OPENING_OBJ_TOL` = 0.10). Among them choose the highest Short-hook score; ties go to the earliest opening. If no candidate is feasible, the intensity has `no_valid_opening` and does not produce a plan.

##### 2.36.8.6 Search — dynamic programming

Let super-units be `U_1 … U_n`, `bucket = DP_BUCKET_S` (0.1 s), `MIN_KEEP_BUCKET = ceil(MIN_KEEP_INTERVAL_S / bucket)`, and `B` = the **DP duration cap** in buckets. The DP duration cap is the exact desired final cap plus `join_reserve_ms` from below; the post-filter remains authoritative.

```text
State:   f[i][k][b][s][q]
         i = number of super-units already decided (0 … n)
         k = retained intervals used so far (0 … MAX_INTERVALS)
         b = retained duration so far, in buckets (0 … B)
         s = 1 if the last decided unit was kept, else 0
         q = current retained-interval length bucket, capped at MIN_KEEP_BUCKET
Base:    f[0][0][0][0][0] = 0 ; every other state = −∞ (unreachable)
Transition (deciding U_{i+1}):
   keep U_{i+1}:    k' = k if s = 1 else k + 1; b' = b + ceil(d_{i+1}/bucket); q' = min(MIN_KEEP_BUCKET, q + ceil(d_{i+1}/bucket)) if s = 1 else min(MIN_KEEP_BUCKET, ceil(d_{i+1}/bucket)); s' = 1
   delete U_{i+1}:  allowed only if U_{i+1} is not forced AND (s = 0 OR q = MIN_KEEP_BUCKET); k' = k; b' = b; q' = 0; s' = 0
Forced:  opening unit kept, completion unit kept, all units before the opening deleted
         (their only allowed transition is "delete" except the opening itself).
Answer:  every state stores up to `DP_POOL` (20) distinct partial hypotheses. A hypothesis is distinct if its kept-unit-id sequence differs.
         Rank retained hypotheses by objective rounded to 1e-6, then by kept-unit-id sequence lexicographically. Reconstruct the global
         top-20 hypotheses for each `(opening, intensity)` from these k-best state lists, then scan them in order and select the first
         solution that passes every exact post-filter.
Hard constraints (prune, do not penalize):
   k' ≤ MAX_INTERVALS ; b' ≤ B ; current interval may not be closed below MIN_KEEP_BUCKET; opening/completion forced units are kept; glue groups intact
Post-filter (applied to reconstructed solutions, and re-applied to the final plan after micro-edits):
   final duration within [plan_min_s, max_s] and inside the primary or an allowed extended range
   region_duration / final_duration ≤ the intensity generation cap and ≤ effective_max_compression_ratio
   first kept unit starts at a sentence start, last kept unit ends at a sentence end
```

The exact-millisecond post-filter is authoritative; the 0.1 s DP bucket is only a pruning approximation. `DP_POOL` is a bounded k-best search, not an open-ended enumeration.

**Generation reserve for authoritative joins.** For each DP run use the conservative, hypothesis-independent `join_reserve_ms = (MAX_INTERVALS − 1) × max(0, LOUDNESS_XFADE_MS − CROSSFADE_MS)`. Let `final_min_required_s = max(plan_min_s, source_region_duration_s / generation_ratio_cap)`. The DP is allowed to reach up to `final_max_s + join_reserve_ms/1000`, and its minimum feasible duration is `final_min_required_s + join_reserve_ms/1000`. This prevents pruning a hypothesis that becomes feasible only after authoritative joins shorten the final timeline. The exact-millisecond post-filter then recomputes the final timeline and enforces the real duration and compression constraints. No tolerance is added to the production cap.

`MAX_INTERVALS` counts **retained** intervals (as in v4.1). A plan with 6 retained intervals has at most 5 cuts.

##### 2.36.8.7 Edit intensities (the three plans)

The three intensities describe **generation intent**. The final `compression_band` is a separate derived property of the final verified timeline and is never inferred from intensity.

| Intensity | How it is built | Generation ratio cap | Final compression-band rule |
|---|---|---|---|
| `minimal` | **No content deletion.** Speech-led plans retain the complete Source Region, subject only to bounded pause-shortening cleanup. Event-led plans are trim-only and receive no pause-shortening micro-edits. | `MINIMAL_CLEANUP_RATIO_CAP` (1.10) for speech-led; `EVENT_EDIT_MAX_RATIO` (1.5) for event-led | Final band decides; normally `standard` |
| `balanced` (primary cap) | DP with duration cap = `primary_range_max_s`, ratio cap = 2.0, maximize the objective. Profile `primary`. | 2.0 | Final band decides; normally `standard` |
| `balanced` (extended cap) | Built **only if** `D_clean > extended_range_max_s` and the style allows extended. DP with duration cap = `extended_range_max_s`, ratio cap = 2.0. Profile `extended`. When `D_clean ≤ extended_range_max_s`, the `minimal` plan is already the extended-length no-content-deletion candidate, so no separate DP is run. | 2.0 | Final band decides; normally `standard` |
| `aggressive` | DP with duration cap = `min(primary_range_max_s, AGGR_FACTOR · balanced_duration)` (`AGGR_FACTOR` = 0.7; `balanced_duration` is the first built `balanced` plan, primary or extended; if none exists the factor is not applied and the cap is `primary_range_max_s`), ratio cap = `effective_max_compression_ratio` in production. | `effective_max_compression_ratio` | Final band decides; `standard` or `strict` |
| `user_edit` | **Not model-generated.** A user-selected trim/simplification is validated as a new lineage against the same final-duration and interval constraints. | `effective_max_compression_ratio` | Final band decides from the verified timeline. |

Rules:

1. Build order (priority): `minimal` → `balanced` (primary cap) → `balanced` (extended cap) → `aggressive`. Skip candidates that cannot satisfy hard constraints. `minimal` and `balanced` (extended cap) are mutually exclusive by construction, so at most 3 plans are produced.
2. **Dedup:** drop a plan if retained duration is within `PLAN_DEDUP_DURATION_REL` (10%) of an already kept plan **or** retained-time Jaccard overlap with a kept plan is ≥ 0.9.
3. The primary-cap `balanced` plan is always attempted before the extended-cap `balanced` variant. Example: `D_clean = 75 s`, style `story`, YouTube profile → `minimal` (75 s, extended), `balanced` (about 60 s, primary), `aggressive` (about 42 s, final ratio about 1.8, therefore **standard** band despite `aggressive` generation intent).
4. Per region there are at most `MAX_PLANS_PER_REGION` (3) **production** plans and at most two production duration profiles (`primary`, `extended`). Study-only ratio plans are outside this production cap and are bounded separately by `STUDY_MAX_PLANS_PER_REGION`.
5. Reject with a reason code if no plan exists: `too_short`, `too_long`, `no_valid_opening`, `interval_limit`, `compression_limit`.
6. **Final classification:** `intensity` records generation intent. `compression_band` (`standard` if final ratio ≤ `STANDARD_RATIO_MAX`, else `strict`) and `duration_profile` are computed from the final verified timeline. Intensity never selects verifier thresholds.

**Study-only ratio-target generation.** When `STUDY_MODE = true`, after the normal production model-plan build order, run an additional deterministic **speech-led** study pass for each `r ∈ STUDY_TARGET_RATIOS = {4.5, 5.0, 6.0, 7.0, 8.0}` for which `(1−STUDY_TARGET_TOL)·target_s ≥ plan_min_s` is feasible. Let `target_s = D_clean / r`. The DP target window is `[(max(plan_min_s, (1−STUDY_TARGET_TOL)·target_s) + join_reserve_ms/1000), ((1+STUDY_TARGET_TOL)·target_s + join_reserve_ms/1000)]`, with an additional symmetric widening of `STUDY_TARGET_SLACK_S`; the exact post-filter requires `final_duration ∈ [max(plan_min_s, (1−STUDY_TARGET_TOL)·target_s), (1+STUDY_TARGET_TOL)·target_s]` and final ratio ≤ `STUDY_MAX_RATIO`. These evaluation-only plans carry `intensity = study_ratio` and `study_target_ratio = r`; they are not counted against the three production plans per region, are never emitted to production ranking, and are used only to populate Task 3 compression bands.

##### 2.36.8.8 Micro-edits (cleanup, not content deletion) — pause shortening only

Apply only to **speech-led** plans in MVP, including `minimal`, after the DP. Event-led plans do not receive micro-edits.

**Deterministic cleanup walk.** Build the candidate pause list once from the post-DP timeline, ordered by source start time. For each pause with length > `PAUSE_SHORTEN_THRESHOLD_S` (0.7 s), propose shortening it to `PAUSE_TARGET_S` (0.35 s). Accept the proposal only if, after applying that one change to the current candidate timeline, all of the following remain true: (a) `final_duration ≥ plan_min_s`; (b) the selected duration profile remains valid; (c) `source_region_duration / final_duration` is ≤ the selected generation ratio cap; and (d) the micro-edit density is ≤ one per 2 s of output. Continue in source order until the list is exhausted. A rejected proposal is recorded in `skipped_micro_edits` with its reason; it is not reconsidered in the same pass. This makes cleanup deterministic and avoids choosing a result from hypothetical total savings.

- For `minimal`, the above walk is the **canonical `D_clean` computation** and is implemented by `d_clean_v1`: `D_clean` is the final duration after this exact pass and is stored as an immutable cleanup result/field before any content-deletion DP is selected. The cleanup never deletes content words; filler-word deletion remains **LATER**.
- For `balanced` and `aggressive`, the same walk is applied after the content DP, but the selected intensity's hard final-duration/profile/ratio constraints are authoritative.
- Pause-shortening joins occur entirely inside silence and use the fixed `CROSSFADE_MS`; Layer 1 still owns the final verified timeline. At most one micro-edit per 2 s of output.


##### 2.36.8.9 Edit Plan artifact (schema v1)

```json
{
  "edit_plan_id": "uuid",
  "source_region_id": "uuid",
  "lineage_id": "uuid",
  "plan_origin": "model | user_edit",
  "parent_edit_plan_id": "uuid | null",
  "replaces_short_candidate_id": "uuid | null",
  "schema_version": 1,
  "stage_version": "edit_plan_gen@1",
  "config_version": "config@1",
  "config_sha256": "…",
  "study_mode": false,
  "evaluation_mode": false,
  "effective_max_compression_ratio": 4.0,
  "export_profile_id": "youtube_shorts",
  "export_profile_sha256": "…",
  "content_style_id": "uuid",
  "intensity": "minimal | balanced | aggressive | study_ratio | user_edit",
  "study_target_ratio": null,
  "duration_profile": "primary | extended",
  "opening_unit_id": "U3",
  "completion_unit_id": "U27",
  "retained_intervals": [ { "start_ms": 0, "end_ms": 0, "unit_ids": ["U3","U4"] } ],
  "deleted_spans": [ { "start_ms": 0, "end_ms": 0, "unit_ids": ["U5"] } ],
  "cuts": [ { "cut_id": "cut:U4>U9", "cut_index": 0, "before_unit_id": "U4", "after_unit_id": "U9",
              "removed_unit_ids": ["U5","U6","U7","U8"] } ],
  "micro_edits": [ { "type": "pause_shorten", "start_ms": 0, "end_ms": 0 } ],
  "skipped_micro_edits": [],
  "cleanup": { "mode": "pause_shortening_only | none", "d_clean_ms": 0,
               "minimal_cleanup_ratio_cap": 1.10, "savings_ms": 0, "applied_micro_edit_count": 0 },
  "dp_duration_ms": 0,
  "final_duration_ms": 0,
  "source_region_duration_ms": 0,
  "compression_ratio": 0.0,
  "compression_band": "standard | strict",
  "interval_count": 0,
  "objective_value": 0.0,
  "short_hook": { "score": 0.0, "type": "question|number|claim|none", "text": "..." },
  "crossfades": [ { "at_ms": 0, "type": "audio", "duration_ms": 30, "provisional": true } ],
  "region_kind": "speech_led | event_led",
  "timeline": [ { "output_segment_id": "uuid", "source_start_ms": 0, "source_end_ms": 0,
                  "output_start_ms": 0, "output_end_ms": 0, "speed_factor": 1.0 } ],
  "event": null,
  "reframe": null,
  "reject_reason": null
}
```

`reframe` is filled by the reframer (2.24) later; the edit generator leaves it null. `event` is null for speech-led plans and `{ "onset_ms": 0, "settle_ms": 0, "settle_source": "detected", "capped_end_ms": null, "start_is_nearest_safe_before_onset": false }` or `{ "onset_ms": 0, "settle_ms": null, "settle_source": "capped", "capped_end_ms": 0, "start_is_nearest_safe_before_onset": false }` for event-led plans. All event edges are resolver-produced `event_safe_cut_v1` timestamps. `region_kind` is `event_led` when the region's seed pattern is P4, else `speech_led`.

**Cut identity (v4.5, R20).** `cuts[]` lists the **content cuts** only (joins between retained intervals; pause shortenings are in `micro_edits`, not cuts). `cut_id` = `"cut:" + <last kept base-unit id before the cut> + ">" + <first kept base-unit id after the cut>`; it is stable for as long as those two neighboring units are unchanged, whatever happens to other cuts. `cut_index` is the 0-based position in the output timeline and is **presentation metadata only** (it labels the `[CUT k]` markers the judge sees); every repair, log and artifact reference uses `cut_id`. The plan stores the `cut_index ↔ cut_id` mapping so a judge issue can be resolved to a `cut_id` at judgment time.

**Crossfades are provisional (v4.5, R25).** The `crossfades` written here are the generator's defaults (30 ms). Layer 1 computes the real `audio_join` per cut (2.36.9.2), which can be longer; the authoritative crossfades, joins and timeline live only in the `verified_edit_plan` artifact (2.36.9.8a). Nothing after verification reads the crossfades of this artifact.

**Timeline mapping (canonical).** The edit generator writes `timeline` after micro-edits. One segment per contiguous stretch of retained source audio/video between cuts or micro-edits (a shortened pause splits a stretch in two). The first segment has `output_start_ms = 0`; for each following segment `output_start_ms = previous output_end_ms − crossfade_ms` at that join (0 if none). `speed_factor` is fixed at 1.0 in MVP (validated by `L1_SCHEMA`); no B-roll or overlays exist in MVP, and reframing does not change time. Every consumer (verifier transcript builder, hook analyzer, captions, renderer) reads a timeline and none reconstructs it. Before verification that timeline is this one; **after verification it is the timeline of the `verified_edit_plan`**, which is recomputed with the real crossfade durations. **Invariant:** temporal features derived from a plan are in output milliseconds; source timestamps are provenance only.

##### 2.36.8.10 Constants (all initial, all named in the config module)

| Constant | Value |
|---|---|
| `MAX_INTERVALS` | 6 (retained) |
| `MAX_PLANS_PER_REGION` / `STUDY_MAX_PLANS_PER_REGION` | 3 / 5 |
| `LONG_UNIT_S` / `SPLIT_PAUSE_MS` | 15 / 500 (G0 retired) |
| `LAMBDA_CUT` | 0.15 |
| `DENSITY_NORM` / `PAYOFF_DECAY_UNITS` | 2.5 / 8 |
| `OPENING_CANDIDATES` / `CTX_MAX` | 3 / 0.5 |
| `OPENING_OBJ_TOL` | 0.10 |
| `DP_BUCKET_S` / `DP_POOL` | 0.1 / 20 |
| `AGGR_FACTOR` | 0.7 |
| `PLAN_DEDUP_DURATION_REL` | 0.10 |
| Micro-edit: pause threshold / target / max density | 0.7 s / 0.35 s / 1 per 2 s |
| `PREFERRED_EVENT_LEADIN_S` / `EVENT_MAX_LEADIN_S` | 6 / 15 |
| `PAUSE_SHORTEN_THRESHOLD_S` / `PAUSE_TARGET_S` | 0.7 / 0.35 |
| `STUDY_TARGET_RATIOS` / `STUDY_TARGET_SLACK_S` | 4.5, 5.0, 6.0, 7.0, 8.0 / 0.5 s |
| Filler-word removal confidence (LATER, unused in MVP) | 0.8 |

##### 2.36.8.11 Acceptance gates (E-gates)

| Gate | Condition |
|---|---|
| E-G1 | Unit tests: every plan is order-preserving, cuts only on unit boundaries, no glue group split, interval count ≤ `MAX_INTERVALS`, first/last unit forced; the DP base state and answer extraction (`f[0][0][0][0]`, `k ≥ 1`); micro-edit budget invariants (a micro-edit never crosses a band, profile or `min_s`); `cut_id` uniqueness and stability; **dedup invariants** (no two kept plans of a region within `PLAN_DEDUP_DURATION_REL` in duration or with retained-time Jaccard ≥ 0.9). 100% pass on the dev set. |
| E-G2 | Retired: region yield (at least one plan passes verification, no fallback exists) is gated by V-G3 (2.36.9.9). |
| E-G3 | **Diversity yield** (replaces the v4.2 gate, which only re-tested the dedup rule, R26; dedup correctness is now in E-G1). (a) In at least 60% of dev regions with `D_clean > primary_range_max_s`, at least 2 plans survive dedup. (b) On Task 3 regions with ≥ 2 sampled plans, annotators mark the sibling plans as meaningfully different in at least 70% of regions; the video-cluster bootstrap lower bound is reported. |
| E-G4 | Generation p95 runtime under 2 s per region on CPU. |

##### 2.36.8.12 Owner decisions (resolved in v4.2)

| # | Decision | Resolution |
|---|---|---|
| E1 | Interval bound | **AGREED:** retained intervals, `MAX_INTERVALS = 6` (not deleted intervals). |
| E2 | Plans per region | **AGREED:** up to 3 plans by compression band (minimal / balanced / aggressive), not K-best DP. |
| E3 | MVP couplings | **AGREED:** only G1, G2 (G0 was in v4.2 and is retired in v4.5, see 2.36.8.2). Semantic couplings are LATER. |
| E4 | Event-led editing | **AGREED:** trim-only, one plan per region. Internal event deletions are LATER. |
| E5 | Judge budget | **AGREED:** 2 calls per plan, 6 per region; every plan that passes Layer 1 is verified. |
| E6 | Value function | **AGREED:** as in v4.1. Risk terms stay out of the utility. |


#### 2.36.9 OQ-10 — Edit Plan verification

**Status: AGREED in v4.3** (owner decisions V1–V10, table in 2.36.9.11). All numbers are *initial* and provisional until the gates in 2.36.9.9 are run. **Amended in v4.5:** viewer-only judge without pre-region context (R24, `verifier_prompt@2`, `verifier@2`), stable `cut_id` targets (R20), one repair pass with several operations (R21), explicit `repair_feasible` (R22), documented restoration depth (R23), single authoritative `verified_edit_plan` (R25), event Layer-1 fixes (R18, R19), cluster-bootstrap decision statistic (R2.3).

**Design principle:** the generator proposes coherent shorter versions; the verifier decides whether each one is acceptable. **The LLM scores; code decides.** The LLM never returns a verdict.

**Numbering note:** v4.1's "Layer 3 (audio/visual continuity, LATER)" keeps its number. The repair-and-acceptance procedure is **Stage R**.

##### 2.36.9.1 Contract

**Input:** one Edit Plan (2.36.8.9), its Source Region, sentences with word timestamps, the export profile, the video's RMS/loudness signal.
**Output:** a `verification_result` per plan (2.36.9.8) and, for every plan whose `final_status` is not `FAIL`, a **`verified_edit_plan`** artifact (2.36.9.8a): the single authoritative plan that hook analysis, reframing, Tier 2, the review UI and the renderer read. If no plan of a region passes, the region gets `status = no_valid_plan` plus every plan's diagnostics.
**Cost class:** Layer 1 low (CPU); Layer 2 medium (one LLM call). Worst case 6 judge calls per region lineage, plus transport retries that do not consume the lineage budget; production cost accounting includes both judge calls and all non-budgeted transport attempts separately.

**When Layer 2 runs.** Layer 2 runs **only for speech-led plans** whose retained transcript has at least `JUDGE_MIN_WORDS` (25) words. Event-led plans always skip Layer 2 and are `LAYER1_ONLY_PASS` when Layer 1 passes. For any speech-led plan below the word threshold, Layer 2 is also skipped. In every skipped case `final_status` is decided by Layer 1 alone, with the distinct status `LAYER1_ONLY_PASS` (never `TRANSCRIPT_VERIFIED_PASS`). It means only that structural and media constraints hold; semantic coherence has **not** been validated. The plan carries `coherence_* = null`, `unjudged = true` and `human_validation_required = true`; the review UI shows it as "not semantically validated", and Tier 2 must not treat it as equivalent to a plan that passed both layers (interim rule: an unjudged plan never outranks a `TRANSCRIPT_VERIFIED_PASS` plan of the same source region; the final treatment is defined in 2.39.6: comparability class B). Event-led plans are trim-only (2.36.8.3), so their cuts are only at the two edges and Layer 1 covers their shape. Their quality is measured against human labels (2.36.9.9), and Layer 3 will cover them later.

##### 2.36.9.2 Layer 1 — deterministic hard checks

Any failure gives `final_status = FAIL` with the code, spends **no** LLM call, and is not repairable unless Stage R says so. Layer 1 is re-run after every repair and recomputes **all** constraints from the new plan (nothing is assumed to be preserved).

| Code | Check |
|---|---|
| `L1_SCHEMA` | Plan validates against schema v1. |
| `L1_ORDER` | Retained intervals strictly increasing in source time, non-overlapping. |
| `L1_CUT_IN_SPEECH` | Timing rules below. |
| `L1_GLUE` | No glue group (G1–G2) split. |
| `L1_FORCED` | For model plans, opening and completion units are retained (2.36.8.5). For `plan_origin = user_edit`, the first/last kept units must satisfy the same sentence/event boundary safety and completion rules but there is no opening-candidate requirement. |
| `L1_INTERVALS` | Interval count ≤ `MAX_INTERVALS`; every interval ≥ `MIN_KEEP_INTERVAL_S`. |
| `L1_DURATION` | Final duration (from the timeline recomputed with the applied crossfades) within `[plan_min_s, max_s]`, where `plan_min_s = EVENT_MIN_FINAL_S` for event-led plans and `profile.min_s` otherwise; the duration profile is then decided by final duration (2.36.2 rule 3). |
| `L1_COMPRESSION` | Final ratio (from the recomputed final duration) ≤ the plan's generation cap and ≤ **`effective_max_compression_ratio`**. For `plan_origin = user_edit`, the generation cap is `effective_max_compression_ratio`; the plan has `intensity = user_edit`, no opening-candidate requirement, and the user-selected first/last kept units are checked only for sentence-safe / canonical event-safe boundaries plus the applicable C-6-style completion rule. |
| `L1_AUDIO_JOIN` | Rules below. |
| `L1_MICRO_EDIT_DENSITY` | At most one micro-edit per 2 s of output. |
| `L1_EVENT_INTERVALS` | Event-led plan has exactly one retained interval. |
| `L1_EVENT_ONSET_MISSING` | Event-led plan does not identify the seed onset (should not occur by construction; catches schema/pipeline bugs). |
| `L1_EVENT_ONSET_CUT` | **Start edge only.** The start edge lies later than `onset_ms − EVENT_ONSET_MARGIN_S` (1.0 s), i.e. less than 1.0 s of lead-in is retained, **and** the start edge is not the nearest safe cut point at or before the onset (`event.start_is_nearest_safe_before_onset = false`). The end edge is never tested by this rule (it is governed by `L1_EVENT_MAIN_CUT` and `L1_EVENT_SETTLE_TAIL_SHORT`). *(v4.4 said "a trim edge", which literally rejected every normal event clip, R18.)* |
| `L1_EVENT_SETTLE_MISSING` | The event record is internally inconsistent: `settle_source = detected` must have a resolver-identified `settle_ms` (start of stable interval) and a resolver-produced end with the required tail; `settle_source = capped` must have `settle_ms = null`, a resolver-produced `capped_end_ms`, and warning `settle_capped`. The cap case is valid and is not treated as a missing-settle failure. |
| `L1_EVENT_MAIN_CUT` | For `settle_source = detected`, the retained interval does not fully contain `[onset_ms, settle_ms]`. For `settle_source = capped`, only `onset_ms ≤ capped_end_ms` is required; there is no detected settle span to test. |
| `L1_EVENT_SETTLE_TAIL_SHORT` | For `settle_source = detected`, less than `SETTLE_TAIL_MIN_S` (1.5 s) of stable/reaction time is retained after `settle_ms`. For `settle_source = capped`, this check is not applicable because no settle interval was detected. |
| `L1_EVENT_BOUNDARY_UNSAFE` | An event edge is not on `event_safe_cut_v1` (2.36.0). |

**Order of evaluation inside Layer 1 (v5.0).** (1) `L1_SCHEMA`, `L1_ORDER`, `L1_CUT_IN_SPEECH`, `L1_GLUE`, `L1_FORCED`, `L1_INTERVALS`; (2) compute the `audio_join` of every content cut and its `applied_crossfade_ms` (`L1_AUDIO_JOIN`); (3) **recompute the timeline** with the applied crossfades and recompute `final_duration_ms`, `compression_ratio`, `compression_band`, `duration_profile`; (4) `L1_DURATION`, `L1_COMPRESSION`, `L1_MICRO_EDIT_DENSITY`; (5) the event checks for event-led plans. Nothing is checked against values that were computed before the joins were fixed.

Audio and video tracks are always retained together; the MVP has no track-level edits, so no required audio or visual component can be dropped.

**Cut timing definitions (speech-led).** For each cut, in source time:

```text
last_kept_word_end        end of the last retained word before the cut
first_deleted_word_start  start of the first deleted word after it
first_kept_word_start     start of the first retained word after the cut
last_deleted_word_end     end of the last deleted word before it
tail_gap_ms = first_deleted_word_start − last_kept_word_end     (silence after the kept material)
head_gap_ms = first_kept_word_start − last_deleted_word_end     (silence before the next kept material)
```

The plan's start and end edges are treated as half-cuts: a start needs `head_gap_ms`, an end needs `tail_gap_ms`, measured against the neighboring source word outside the plan.

**`L1_CUT_IN_SPEECH`:** fails if `tail_gap_ms < CUT_GAP_MIN_MS` or `head_gap_ms < CUT_GAP_MIN_MS` (20 ms). The rule applies to each side's whole gap independently. Word timestamps from ASR are approximate, so gaps must come from the forced-alignment output when available.

**`L1_AUDIO_JOIN`** is computed from actual audio, never from gap length alone:

```text
tail window = [last_kept_word_end, last_kept_word_end + min(tail_gap_ms, LOUDNESS_XFADE_MS)]
head window = [first_kept_word_start − min(head_gap_ms, LOUDNESS_XFADE_MS), first_kept_word_start]
nonspeech_tail_ms = length of the tail window, starting at the word edge, whose 10 ms-frame RMS ≤ local_nonspeech_rms_v1(t)
nonspeech_head_ms = the same for the head window, measured backwards from the word edge
crossfade_ms = min(CROSSFADE_MS, nonspeech_tail_ms, nonspeech_head_ms)
loudness_step_db = |short-term loudness (400 ms) after the cut − before the cut|
```

`local_nonspeech_rms_v1(t)` is the sole nonspeech threshold: the rolling 60 s, 20th-percentile RMS in linear amplitude. It is never replaced by a video-global percentile.

Recorded per cut as `audio_join`:

```json
{ "cut_id": "cut:U4>U9", "tail_gap_ms": 0, "head_gap_ms": 0, "nonspeech_tail_ms": 0, "nonspeech_head_ms": 0,
  "normal_crossfade_available": true, "extended_crossfade_available": true,
  "speech_overlap_allowed": false, "loudness_step_db": 0.0, "crossfade_ms": 30, "applied_crossfade_ms": 30 }
```

- `normal_crossfade_available` = `crossfade_ms ≥ MIN_XFADE_MS` (10).
- `extended_crossfade_available` = `min(LOUDNESS_XFADE_MS, nonspeech_tail_ms, nonspeech_head_ms) ≥ EXT_XFADE_MIN_MS` (60).
- Fail with `L1_AUDIO_JOIN` if `normal_crossfade_available` is false, or if `loudness_step_db > LOUDNESS_STEP_MAX_DB` (12) and `extended_crossfade_available` is false. If the step is above 12 dB and the extended crossfade is available, use it and record warning `loudness_step_xfade`; in that case `applied_crossfade_ms = min(LOUDNESS_XFADE_MS, nonspeech_tail_ms, nonspeech_head_ms)`, otherwise `applied_crossfade_ms = crossfade_ms`. Pause-shortening joins (micro-edits) fall inside silence and always use the fixed `CROSSFADE_MS`; they have no `audio_join` record.
- `speech_overlap_allowed` is always false in MVP.
- Layer 1 checks only that a join can be represented safely. It does not claim perceptual quality; that is Layer 3 (LATER). The renderer must apply the `applied_crossfade_ms` of each `audio_join` exactly, read from the `verified_edit_plan` (2.36.9.8a), which is the only authoritative source.

The LLM is not asked about audio artifacts; it sees only text.

##### 2.36.9.3 Layer 2 — structured coherence judge

**Input (built by code) — viewer-only (v4.5, R24).** The judge receives exactly one input: `short_transcript`, the final transcript with speaker labels and `[CUT k]` markers (k from 0 = `cut_index`; markers exist only for **content cuts**, `cuts[]` in 2.36.8.9, never for pause shortenings). Removed text is **not** included. Metadata is limited to output-timeline information (speaker labels, sentence breaks, output-time offsets). Source timestamps and the durations of removed spans are never sent, because they would reveal what the viewer cannot see.

**No pre-region context is sent.** v4.3 sent 30 s of transcript from before the region, labeled "not shown to the viewer". A language model cannot be mechanically prevented from using text it has been given when it scores the other dimensions, so that context could silently inflate `reference_resolution` or `setup_payoff`. It is also unnecessary: an opening that depends on unseen material shows itself inside the short (an unresolved "she", an unintroduced project), and the `opening_standalone` anchors describe exactly that. A context-aware opening check (context + opening only, in a separate call) is an **offline experiment**, compared with this judge on Task 3 labels; it is not part of the MVP call budget. `CONTEXT_BEFORE_S` is therefore used only by that experiment.

**Settings:** temperature 0; JSON-schema-constrained output where the API supports it; `JUDGE_MODEL` is a config value, re-verified at implementation time.

**LLM failure taxonomy (shared by verifier, hook and style calls).** Distinguish `transport_error` (timeout, connection failure, HTTP 429, HTTP 5xx or provider-unavailable response) from `invalid_output` (response received but schema/semantic validation fails). A `transport_error` retry uses exponential backoff up to `LLM_MAX_TRANSPORT_RETRIES = 2` and a per-call `LLM_CALL_TIMEOUT_S = 30`; it does **not** consume the judge lineage call budget. Exhausted transport retries return `RETRYABLE_TRANSPORT_ERROR` to the stage/job retry mechanism and do not produce a semantic verdict. `invalid_output` follows the existing single bounded retry and **does** consume the lineage call budget. The same taxonomy and timeout apply to `hook_prompt@1` and `style_prompt@1`.

**Prompt `verifier_prompt@2`:**

```text
SYSTEM
You review short-form video edits. A short was made by deleting parts of a longer video. You are given
its transcript with [CUT k] markers where material was removed. Judge only what a viewer of the short
experiences. The viewer has seen nothing except this short: anything it refers to without introducing it
is unknown to them. Do not decide whether the short is good or viral. Do not give an overall verdict.
Return JSON matching the schema and nothing else.

Score each dimension from 1 to 5 using these anchors.
flow                 5 every join reads naturally | 4 a join is slightly abrupt but clear | 3 at least one join is noticeably jumpy |
                     2 at least one join is a clear non-sequitur | 1 incoherent
reference_resolution 5 every pronoun/reference resolves inside the short | 4 one reference resolves only by inference |
                     3 one reference is ambiguous or unresolved | 2 a key reference is unresolved, or several | 1 most are unresolved
setup_payoff         5 the payoff is fully supported by its setup | 4 a small detail is missing but understanding is intact |
                     3 the payoff lands but a needed fact is missing | 2 the payoff cannot be understood | 1 no setup or no payoff
ending_completeness  5 ends on a completed thought | 4 completed but flat | 3 ends noticeably early or trails off |
                     2 ends mid-idea | 1 ends mid-sentence
opening_standalone   5 understandable with no outside context | 4 minor missing context that does not matter |
                     3 the viewer must guess who or what | 2 refers to content the viewer never saw | 1 incomprehensible

List every problem as an issue. Use severity "major" only if a typical viewer would be confused;
use "minor" if only a careful viewer would notice. If any score is 3 or lower you must list at least one issue.
For issues at a join, set location "cut" and cut_index to that marker's number. Use location "opening"
or "ending" otherwise, with cut_index null. Evidence is at most 20 words and may be a paraphrase.

USER
<short_transcript>...</short_transcript>
```

**Schema `verifier_output@1`:**

```json
{
  "schema_version": 1,
  "scores": { "flow": 1, "reference_resolution": 1, "setup_payoff": 1,
              "ending_completeness": 1, "opening_standalone": 1 },
  "issues": [ { "location": "cut | opening | ending", "cut_index": 0,
                "type": "dangling_reference | missing_setup | non_sequitur | abrupt_end | topic_jump | opening_dependent | other",
                "severity": "minor | major", "evidence": "<= 20 words" } ]
}
```

**Validation (code):** valid JSON; scores are integers 1–5; enums valid; `cut_index` null unless `location = cut` and within `[0, cut_count − 1]`; evidence ≤ 20 words; if any score ≤ 3 there is at least one issue. A violation counts as invalid output (2.36.9.5 rule 4).

**Normalization (code, before the verdict).** `cut_index` values are first resolved to `cut_id` through the plan's stored `cut_index ↔ cut_id` map. Issues are then deduplicated by `(location, cut_id, type)`. When duplicates disagree on severity, keep the highest severity and the first valid evidence string. Verbose repetition by the judge therefore cannot change the issue count. Evidence text is diagnostic only and never enters the verdict.

**Deterministic cross-field semantic validation (`validate_judge_semantics@1`).** JSON-schema validity is necessary but not sufficient. Before normalization, code rejects the output and consumes the retry when: (1) any required score is missing or outside 1–5; (2) any score ≤ 3 has no issue; (3) `location = cut` has a null or out-of-range `cut_index`; (4) `location = opening|ending` has a non-null `cut_index`; (5) issue type is outside the closed issue enum; (6) severity is not `major|minor`; (7) evidence exceeds `JUDGE_MAX_EVIDENCE_WORDS`; or (8) a cut index cannot resolve through the stored map. The validator never invents an issue, clamps a value or performs a repair. `judge_validation_version = validate_judge_semantics@1` is stored with every call.

**Score semantics.** Scores are ordinal anchors, not probabilities or interval measurements. `min` and `mean` are an initial heuristic; calibration (2.36.9.9) tests whether they track human coherence labels.

**Rubric mapping.**

| Dimension | Where it lives |
|---|---|
| Standalone comprehensibility | score `opening_standalone`, issue `opening_dependent` |
| Missing setup | score `setup_payoff`, issue `missing_setup` |
| Dangling references | score `reference_resolution`, issue `dangling_reference` |
| Topic continuity | score `flow`, issue `topic_jump` |
| Logical completion | scores `setup_payoff`, `ending_completeness` |
| Abrupt ending | score `ending_completeness`, issue `abrupt_end` |
| Non-sequitur / unnatural transition | score `flow`, issue `non_sequitur` |
| Audio/editing artifacts | Layer 1 `L1_AUDIO_JOIN`; Layer 3 later. Not judged by the LLM. |

##### 2.36.9.4 Verdict — hard gates versus soft scores (code, deterministic)

- **Hard gates** decide `PASS` / `FAIL`.
- **Soft scores** are never gates; every passing plan carries them to Tier 2: `coherence_min`, `coherence_mean`, `issue_count_minor`, `repair_applied`, `judged_band`, `unjudged`.

**Bands (half-open, one place for all uses).** `standard` if `compression_ratio ≤ STANDARD_RATIO_MAX` (2.0); `strict` if `STANDARD_RATIO_MAX < ratio ≤ effective_max_compression_ratio`. A plan above the effective ceiling is invalid before band assignment.

```python
def verdict(plan, lineage, scores, issues_raw, band):
    issues = normalize(issues_raw)                       # dedupe by (location, cut_id, type), keep max severity
    if min(scores.values()) <= HARD_SCORE_MAX:           # 2
        return "HARD_FAIL"                               # not repairable
    major = [i for i in issues if i.severity == "major"]
    minor = [i for i in issues if i.severity == "minor"]
    critical_minor = [i for i in minor if i.type in ("dangling_reference", "missing_setup")]
    ok = min(scores.values()) >= PASS_MIN_SCORE and not major           # any major issue blocks PASS in both bands
    if band == "standard":
        ok = ok and mean(scores.values()) >= PASS_MEAN_STANDARD        # 4.2
    else:
        ok = (ok and mean(scores.values()) >= PASS_MEAN_STRICT         # 4.5
                 and not critical_minor
                 and len(minor) <= STRICT_MINOR_ISSUES_MAX)            # 1
    if ok:
        return "PASS"
    return "REPAIRABLE" if repair_feasible(plan, issues, lineage) else "HARD_FAIL"
```

The type matters more than the count: a major issue of any type always blocks, and in the strict band a minor `dangling_reference` or `missing_setup` also blocks. The count of minor issues is only a secondary restriction. All thresholds are **provisional** and are tested against human labels in V-G5. Issue type and severity are stored with every judgment so future calibration can weigh them differently (a minor `opening_dependent` and a minor `non_sequitur` are not equivalent). The strict rule must not be loosened until human-labeling results show that the accepted plans remain coherent.

**`repair_feasible` (v4.5, R22) — exact contract.** It is a pure, deterministic function defined together with Stage R (2.36.9.6):

```text
repair_feasible(plan, issues, lineage) =
        lineage.repairs_used < MAX_REPAIR_ITERATIONS_PER_PLAN
    and no issue of type "abrupt_end"                       (→ HARD_FAIL J_ABRUPT_END)
    and no issue of type "other" with severity "major"
    and len( plan_repair(plan, issues, lineage) ) ≥ 1       (a dry run of Stage R; nothing is applied)
```

**Band bookkeeping after a repair.** A repaired plan is judged by the rule of the band it now has. The audit record keeps both values: `origin_band` (the plan before repair) and `judged_band` (the band actually used), plus `origin_intensity`. A repair that moves a plan from strict to standard is visible in the record and is analyzed separately in calibration. Tier 2 receives `judged_band`.

##### 2.36.9.5 Judge-call budget

```text
MAX_PLANS_PER_REGION       = 3
MAX_JUDGE_CALLS_PER_PLAN   = 2      (per plan lineage)
MAX_JUDGE_CALLS_PER_REGION = 6      (total, including repairs; must be ≥ MAX_PLANS_PER_REGION × MAX_JUDGE_CALLS_PER_PLAN)
VERIFY_ALL_PLANS           = true
EARLY_STOP_ACCEPTED_PLANS  = disabled   (experiment flag only; see rule 6)
PLAN_VERIFY_ORDER          = [minimal, balanced, aggressive]   (recorded in every artifact)
```

A **plan lineage** is an original plan plus its repaired descendant (`lineage_id`). The budget belongs to the lineage; a new plan id created by repair never resets it.

1. Each production plan that passes Layer 1 and Layer 2 applies (2.36.9.1) receives one initial judge call. A plan that fails Layer 1 receives none. Study-only ratio-target plans use the separate `STUDY_MAX_JUDGE_CALLS_PER_REGION` budget and do not consume the production region budget.
2. `PASS` → done, never repaired. `HARD_FAIL` → done.
3. `REPAIRABLE` → Stage R (deterministic, no call). If it yields a new plan that passes Layer 1 and is not a duplicate, and the lineage has a call left → call 2 judges it. Any verdict other than `PASS` ends the lineage as `FAIL`. No second repair.
4. **Invalid output:** call 1 invalid → retry once (this is call 2). Call 2 valid → the verdict is computed; if `REPAIRABLE`, the lineage has no call left, so it ends `FAIL` with `repair_unfunded`. Call 2 invalid → `FAIL` with `J_INVALID_OUTPUT`.
5. The production region total never exceeds `MAX_JUDGE_CALLS_PER_REGION`. Study-only verification has a separate `STUDY_MAX_JUDGE_CALLS_PER_REGION` ceiling. These maxima are ceilings, not targets.
6. **`VERIFY_ALL_PLANS = true` in production and in evaluation.** Every plan that passes Layer 1 is judged. Early stopping would change the population Tier 2 sees (fewer verified plans per region, plan-order effects, a pool biased toward plans that are cheaper to verify, less consistent ranking comparisons across regions), so it is disabled. A code path for `EARLY_STOP_ACCEPTED_PLANS = N` may exist only behind an explicit experiment flag; evaluation runs ignore it; no production experiment may change the candidate-pool policy silently; and any early-stopping experiment must report both the cost saved and the downstream ranking quality. `PLAN_VERIFY_ORDER` is stored in every artifact (`verify_order`) and is an experimental variable, not a semantic policy.

##### 2.36.9.6 Stage R — repair (deterministic, no search)

Stage R performs **at most one repair pass per plan lineage** (`MAX_REPAIR_ITERATIONS_PER_PLAN = 1`). A repair pass may apply several deterministic operations (one per repairable issue). It never asks the LLM to rewrite anything and never re-runs the DP. All constraints are recomputed by Layer 1 afterward. **Every operation targets a stable `cut_id` (2.36.8.9), never an ordinal `cut_index`**, because restoring material changes the set and the numbering of cuts.

| Issue | Operation |
|---|---|
| `dangling_reference` or `missing_setup` at a cut (`location = cut`) | **R1 restore-before-cut(cut_id):** restore the last deleted super-unit of the span that ends at that cut, with its glue group (`REPAIR_RESTORE_DEPTH` = 1 super-unit, see the depth note below). Applied unconditionally: the issue itself says something needed is missing. |
| `non_sequitur` or `topic_jump` at a cut | **R1, only if the bridge test passes** (below). If it fails, the issue is not repairable. |
| `opening_dependent`, or `dangling_reference` / `missing_setup` with `location = opening` | **R2 earlier-opening:** use the previous untried opening candidate (2.36.8.5) and restore every unit between the new and old opening. Infeasible if the plan already uses the first opening. |
| `dangling_reference` or `missing_setup` with `location = ending` | Not repairable (no operation applies to the ending). |
| `abrupt_end` | Not repairable. `HARD_FAIL` with `J_ABRUPT_END`; also written to the qualification-error log (the region's end was wrong, since the completion unit is forced). |
| `other` | Not repairable. `HARD_FAIL`. Any `(type, location)` pair not listed in this table is also not repairable. |

**Bridge test.** It compares the repaired join with the *current* join; it never uses an absolute similarity threshold. Let `a` = last kept unit before the target cut, `b` = first kept unit after it, `r` = the unit R1 would restore. If restoring `r` closes the cut completely (the deleted span was exactly one super-unit), the test passes automatically. Otherwise, with sentence embeddings:

```text
S_cur = cos(a, b)                   the current join
S_in  = cos(r, b)                   restored unit into the next kept unit
S_out = cos(a, r)                   preceding kept unit into the restored unit
S_new = min(S_in, S_out)            weakest link of the resulting join
T_r   = topic-boundary score (2.36.5) between r and b in source order
PASS iff  S_new >= S_cur + BRIDGE_MARGIN   and   T_r < TOPIC_STOP
```

The second condition rejects a restored unit that starts a new topic instead of bridging the existing one. `a`, `b` and `r` use `super_unit_embedding_v1` (2.36.0). `S_cur` (pre-repair) and `S_in, S_out, S_new, T_r` (post-repair) are recorded in the verification artifact.

**Selection and application.**
1. Take the repairable issues. Order: `major` before `minor`, the opening issue first, then ascending **source position of the cut** (not `cut_index`).
2. Apply operations in that order. Each operation is first resolved against the **current** plan by `cut_id`; if that cut no longer exists (an earlier operation closed or changed it), the operation is skipped and recorded as `stale_target`. Before each applied operation, check the resulting plan against plan minimum duration, duration-profile validity, interval count and the effective compression ceiling; restoring units can only lower the ratio, so do not require the operation to remain inside the pre-repair generation band. `R2` means the previous opening candidate in the deterministic opening-candidate list, not an arbitrary earlier sentence.
3. If nothing was applied: `HARD_FAIL` with `repair_infeasible`.
4. Re-run Layer 1. Failure → `HARD_FAIL` with that Layer 1 code.
5. If the result has retained-time overlap ≥ `REPAIR_DUPLICATE_OVERLAP` (0.9) with the original or with another plan of the region: discard it, no call, `repair_duplicate`.
6. Otherwise re-judge (2.36.9.5 rule 3).

**`plan_repair` (v4.5, R22).** `plan_repair(plan, issues, lineage)` is the dry-run form of the selection above: for each issue in the stated order it maps the issue to R1 or R2 by the table, resolves the `cut_id`, checks the bridge test where required, checks R2 availability and the duration / interval / compression caps of the resulting plan, and returns the list of operations that pass every check. It applies nothing and calls no LLM. Stage R = `plan_repair` + apply + Layer 1 + duplicate check.

**Restoration depth (v4.5, R23).** R1 restores exactly `REPAIR_RESTORE_DEPTH` (initial 1) deleted super-unit(s), counted backwards from the cut. Depth 1 is deliberate: the lineage has one repair pass and one re-judgment, and restoring a growing chain would turn repair into a search over edits, which 2.10 forbids. It can be insufficient when the missing referent lies two or more units back. This is **measured, not assumed**: the repair record stores `repair_insufficient = true` when the re-judgment still reports the same issue type at the same `cut_id`. If at least 30% of repaired lineages on the Task 3 plans end that way, an offline experiment compares depth 2 (one extra unit, only while the bridge test still passes) with depth 1 against human labels; changing the depth is an owner decision, not an automatic tuning.

**Diagnostics without exposing removed text.** The repair engine works from the Edit Plan and unit metadata (for example `cut_id = cut:U4>U9, removed_units = [U11, U12], restore_candidate = U11`); the deleted transcript is never sent to the judge. An "editor-aware" judge that sees removed text is an offline experiment, compared against the viewer-only judge on Task 3 labels, not an MVP feature.

**Input separation.** The **judge** receives only the edited transcript, the `[CUT k]` markers and output-timeline metadata (no context from before the region, 2.36.9.3). The **repair engine** receives the judge's issue metadata, removed-unit metadata, candidate restoration units, embedding and bridge-test features, and the original Edit Plan structure. The judge never receives the repair engine's inputs.

**No fallback window.** v4.1's "best contiguous no-cut window" is removed: the `minimal` plan is already the no-cut version when `D_clean ≤ max_s`, and a shorter core of a long region is reachable as a nested region (2.36.7). If no plan of a region passes, the region ends as `no_valid_plan`.

##### 2.36.9.7 What differs between standard and strict

| | standard (final ratio ≤ 2.0) | strict (2.0 < final ratio ≤ `effective_max_compression_ratio`) |
|---|---|---|
| Layer 1 | same | same |
| Minimum score | ≥ 4 | ≥ 4 |
| Mean score | ≥ 4.2 | ≥ 4.5 |
| Major issues | none | none |
| Minor issues | unlimited | at most 1, never `dangling_reference` / `missing_setup` |
| Repair | once | once |

##### 2.36.9.8 Verification artifact (schema v1)

```json
{
  "verification_id": "uuid",
  "edit_plan_id": "uuid",
  "lineage_id": "uuid",
  "schema_version": 1,
  "stage_version": "verifier@2",
  "verdict_code_version": "verdict@1",
  "config_version": "config@1",
  "config_sha256": "…",
  "study_mode": false,
  "evaluation_mode": false,
  "effective_max_compression_ratio": 4.0,
  "layer1": { "passed": true, "failures": [], "warnings": [], "audio_joins": [] },
    "judge_calls": [
    { "call_index": 1, "plan_id_judged": "uuid",
      "prompt_version": "verifier_prompt@2", "model_id": "…", "temperature": 0,
      "judge_validation_version": "validate_judge_semantics@1",
      "normalized_input_sha256": "…", "transcript_sha256": "…", "normalized_input_ref": "storage://…",
      "cut_map": [ { "cut_index": 0, "cut_id": "cut:U4>U9" } ],
      "raw_output": {}, "valid": true,
      "normalized_issues": [], "judged_band": "standard|strict", "verdict": "PASS|REPAIRABLE|HARD_FAIL" } ],
  "repair": { "applied_ops": [ { "op": "R1", "cut_id": "cut:U4>U9", "restored_unit_ids": ["U11"],
                "bridge": { "S_cur": 0.0, "S_in": 0.0, "S_out": 0.0, "S_new": 0.0, "T_r": 0.0, "closed_cut": false, "passed": true } } ],
              "stale_targets": [], "repair_insufficient": false,
              "repaired_plan_id": "uuid|null",
              "result": "judged | repair_infeasible | repair_duplicate | repair_unfunded | null" },
  "origin_intensity": "minimal|balanced|aggressive|study_ratio|user_edit",
  "origin_band": "standard|strict",
  "judged_band": "standard|strict",
  "final_status": "TRANSCRIPT_VERIFIED_PASS | LAYER1_ONLY_PASS | FAIL",
  "verification_scope": "speech_judged | event_layer1_only",
  "semantic_validation": "passed | failed | skipped",
  "semantic_judge_status": "JUDGED | SKIPPED_LOW_TRANSCRIPT",
  "human_validation_required": false,
  "selection_policy": "verify_all",
  "verify_order": ["minimal", "balanced", "aggressive", "study_ratio:4.5", "study_ratio:5.0", "study_ratio:6.0", "study_ratio:7.0", "study_ratio:8.0"],
  "verified_edit_plan_id": "uuid|null",
  "fail_reason": "L1_* | J_HARD_SCORE | J_INVALID_OUTPUT | J_ABRUPT_END | repair_infeasible | repair_duplicate | repair_unfunded | thresholds_not_met | null",
  "tier2_features": { "coherence_min": 0.0, "coherence_mean": 0.0, "issue_count_minor": 0,
                      "repair_applied": false, "judged_band": "standard", "unjudged": false }
}
```

The normalized judge input is stored (or referenced) together with its SHA-256, and the raw model output is stored unmodified. Historical judgments can then be re-scored offline with a new `verdict_code_version` or compared across judge models without re-calling the LLM.

##### 2.36.9.8a Verified Edit Plan artifact (v5.0) — the single authority

Verification ends by writing, for every plan whose `final_status` is not `FAIL`, an immutable **`verified_edit_plan`** (for a repaired lineage, built from the repaired plan). It is the **only** plan artifact read by hook analysis (2.37), reframe planning (2.24), Tier 2 (2.39), the review UI, captions and the renderer. The raw Edit Plan of 2.36.8.9 is provenance and is never read after verification.

```json
{
  "verified_edit_plan_id": "uuid",
  "schema_version": 1,
  "stage_version": "verified_plan@1",
  "config_version": "config@1",
  "config_sha256": "…",
  "study_mode": false,
  "evaluation_mode": false,
  "effective_max_compression_ratio": 4.0,
  "verification_id": "uuid",
  "edit_plan_id": "uuid",
  "source_region_id": "uuid",
  "lineage_id": "uuid",
  "plan_origin": "model | user_edit",
  "parent_edit_plan_id": "uuid | null",
  "replaces_short_candidate_id": "uuid | null",
  "export_profile_id": "youtube_shorts",
  "export_profile_sha256": "…",
  "final_status": "TRANSCRIPT_VERIFIED_PASS | LAYER1_ONLY_PASS",
  "human_validation_required": false,
  "region_kind": "speech_led | event_led",
  "intensity": "minimal | balanced | aggressive | study_ratio | user_edit",
  "study_target_ratio": null,
  "retained_intervals": [], "cuts": [], "micro_edits": [],
  "audio_joins": [ { "cut_id": "cut:U4>U9", "applied_crossfade_ms": 30, "loudness_step_db": 0.0 } ],
  "crossfades": [ { "at_ms": 0, "type": "audio", "duration_ms": 30, "provisional": false } ],
  "timeline": [],
  "final_duration_ms": 0, "compression_ratio": 0.0,
  "compression_band": "standard | strict", "duration_profile": "primary | extended",
  "opening_unit_id": "U3 | null",
  "completion_unit_id": "U27 | null",
  "short_hook": { "score": 0.0, "type": "question|number|claim|none", "text": "…" },
  "content_style_id": "uuid | null",
  "final_face_ratio": 0.0, "final_screen_ratio": 0.0,
  "final_visual_format": "talking_head | screen_capture | mixed | other_visual",
  "event": null, "reframe": null
}
```

Rules: (1) `crossfades`, `audio_joins` and `timeline` are the **final** ones, recomputed from the applied crossfades; the timeline invariant of 2.36.8.9 holds (output milliseconds). (2) The artifact is immutable; a later reframe result is stored in its own artifact that references `verified_edit_plan_id`. (3) A user edit (2.26.1) produces a new lineage and a new `verified_edit_plan`.

##### 2.36.9.9 Calibration and acceptance gates

**Task 3 labels (revised).** 100 speech-led plans, at least 20 in each band below, plus at least 15 event-led or low-speech plans (labeled only to check Layer-1-only acceptance). Pass/fail on coherence with reason codes `dangling_reference, missing_setup, non_sequitur, abrupt_end, topic_jump, opening_dependent, audio_glitch` (`audio_glitch` is human-only). Sampling is stratified by compression band × structural type as specified in 2.36.1 (v4.5); the band of a plan is always computed from its **final** compression ratio.

**Compression bands (half-open; every plan falls in exactly one):** `[1.0, 1.5)`, `[1.5, 2.5)`, `[2.5, 4.0]`, `(4.0, 6.0]`, `(6.0, 8.0]`. The 4.0 edge is inclusive because the production cap is inclusive. Because the standard/strict boundary (2.0) falls inside `[1.5, 2.5)`, every table is reported twice: by compression band and by rule band (standard / strict).

**Study mode (v5.0).** `effective_max_compression_ratio` is resolved once as `STUDY_MAX_RATIO` when `STUDY_MODE = true`, otherwise `MAX_COMPRESSION_RATIO`. Study-mode plans use that same effective value in generation, post-filtering, Layer 1, band assignment and artifacts; they are never shown to users and never used to train the final ranker. Every study artifact stores `study_mode`, `evaluation_mode`, and `effective_max_compression_ratio` so the mode cannot be inferred or changed downstream.

**Statistics rule (v4.5, R2.3).** Plans in this study are clustered (several plans per region, several regions per video), so a binomial interval that treats plans as independent is not a valid decision statistic. **Decision statistic = video-cluster bootstrap:** resample **videos** with replacement `BOOTSTRAP_B` (2000) times, recompute the metric on each resample (pooling the plans of the resampled videos), and take the 2.5th percentile as the lower bound (the same procedure as H-G4). Every reported rate also includes `N`, `K`, the observed rate and the **Wilson 95% lower bound**; the Wilson bound is an *operational reference only*: it assumes independence and is therefore optimistic. Wilson reference values (observed rate → plans needed for a lower bound): observed 0.90 needs about 40 plans for a bound of 0.75 and about 70 for 0.80; observed 0.95 needs about 20 plans for 0.75 and about 40 for 0.80; at 20 plans even a perfect score has a lower bound of only 0.84. The bootstrap is evaluated only when plans come from at least `STUDY_MIN_VIDEOS` (8) videos; with so few clusters its interval is coarse, and a result near a threshold should trigger more labeling, not a decision.

**Reporting for every band and ceiling decision.** A pass rate is not precision, so report all of: labeled plans (`N`); plans passing the verifier; plans judged coherent by humans; observed precision with its cluster-bootstrap and Wilson lower bounds; observed human-coherence rate over all labeled plans in the band; number of distinct source regions and videos represented; and the split between speech-led and event-led plans (event-led results are reported in their own table). A band decision is valid only if its plans come from at least `STUDY_MIN_REGIONS` (15) distinct regions across at least `STUDY_MIN_VIDEOS` (8) videos, with no single video contributing more than `STUDY_MAX_VIDEO_SHARE` (25%), so a few easy regions cannot set the ceiling.

**Gates** (dev set first; then once on the sealed test set):

| Gate | Condition |
|---|---|
| V-G1 | Layer 1 unit tests pass 100% on synthetic plans containing each violation code, including all cut-timing and event cases. |
| V-G2 | **Precision.** Of plans the verifier passes: `N_passed ≥ 40`, observed precision ≥ 0.90 and **video-cluster-bootstrap lower bound ≥ 0.75** (the Wilson bound is reported but is not decisive). If `N_passed < 40` the gate is *not evaluated* and more plans are labeled. Reported per rule band and per compression band. For unjudged event-led plans, report Layer-1-only precision separately; never pool it with speech-led precision. |
| V-G3 | **Not trivially strict.** Recall (share of human-coherent plans that pass) ≥ 0.50 (observed value decides; its video-cluster-bootstrap interval is reported), and at least 70% of regions with a labeled acceptable duration yield ≥ 1 passing plan (the single source for the region-yield gate; E-G2 defers to it). |
| V-G4 | **Judge stability**, two independent runs per dev plan: verdict agreement ≥ 0.90; mean absolute score difference ≤ 0.5 per dimension; issue agreement (Jaccard on the sets of `(location, type)`) ≥ 0.70. Numbers are initial and are recalibrated on the pilot. |
| V-G5 | **Compression study.** (a) *Keeping or lowering:* `MAX_COMPRESSION_RATIO` is the upper edge of the highest band in `[1.0, 4.0]` whose own observed human-coherence rate is ≥ 0.85 **and every lower band up to that edge also meets ≥ 0.85** (N ≥ 20 per evaluated band). (b) *Raising above 4.0* needs stronger evidence, because it widens production behavior: the candidate band needs `N ≥ 40`, observed ≥ 0.85, video-cluster-bootstrap lower bound ≥ 0.70, V-G2/V-G3 must hold for the candidate band, and **every lower compression band in the proposed production range must also satisfy its applicable gate**. Because the base study has only 20 per band, raising the ceiling requires a top-up labeling round of at least 20 more plans in the candidate band. The ceiling is changed only by an owner decision after the study report, never automatically, and study-mode plans passing the verifier never raise it by themselves. (c) *Rule check:* compare the standard rule and the strict rule on the same `[2.5, 4.0]` plans against human labels; keep the strict rule only if it improves precision without recall dropping below 0.50. Then recompute `MAX_REGION_S` (2.36.3). |

V-G2, V-G3 and V-G4 replace G5's condition; V-G5 replaces G6's. Prefer false rejects to false passes: if V-G2 and V-G3 conflict, V-G2 wins, and thresholds are loosened only after a labeled review.

##### 2.36.9.10 Constants (all initial)

| Constant | Value |
|---|---|
| `MAX_PLANS_PER_REGION` / `MAX_JUDGE_CALLS_PER_PLAN` / `MAX_JUDGE_CALLS_PER_REGION` | 3 / 2 / 6 |
| `MAX_REPAIR_ITERATIONS_PER_PLAN` / `REPAIR_RESTORE_DEPTH` | 1 / 1 |
| `VERIFY_ALL_PLANS` / `EARLY_STOP_ACCEPTED_PLANS` / `EVALUATION_MODE` | true / disabled / false |
| `PLAN_VERIFY_ORDER` | minimal, balanced, aggressive; study adds deterministic ratio targets 4.5, 5.0, 6.0, 7.0, 8.0 |
| `HARD_SCORE_MAX` / `PASS_MIN_SCORE` | 2 / 4 |
| `PASS_MEAN_STANDARD` / `PASS_MEAN_STRICT` | 4.2 / 4.5 |
| `STANDARD_RATIO_MAX` / `STRICT_MINOR_ISSUES_MAX` | 2.0 / 1 |
| `JUDGE_MIN_WORDS` / `LLM_CALL_TIMEOUT_S` | 25 / 30 s |
| `LLM_MAX_TRANSPORT_RETRIES` / `STAGE_MAX_ATTEMPTS` | 2 / 3 |
| `MAX_JUDGE_CALLS_PER_REGION` / `STUDY_MAX_JUDGE_CALLS_PER_REGION` | 6 / 10 |
| `CONTEXT_BEFORE_S` (offline context-aware experiment only) / `JUDGE_MAX_EVIDENCE_WORDS` | 30 / 20 |
| `CUT_GAP_MIN_MS` / `CROSSFADE_MS` / `MIN_XFADE_MS` | 20 / 30 / 10 |
| `LOUDNESS_STEP_MAX_DB` / `LOUDNESS_XFADE_MS` / `EXT_XFADE_MIN_MS` | 12 / 100 / 60 |
| `NONSPEECH_RMS` | derived via `local_nonspeech_rms_v1` (rolling 60 s, 20th-percentile RMS) |
| `BRIDGE_MARGIN` / `REPAIR_DUPLICATE_OVERLAP` | 0.05 / 0.9 |
| `EVENT_ONSET_MARGIN_S` / event-led minimum duration / `SETTLE_TAIL_MIN_S` / `SETTLE_SNAP_MAX_S` | 1.0 s / 6 s / 1.5 s / 3.0 s |
| `STUDY_MODE` / `STUDY_MAX_RATIO` | false / 8.0 |
| `STUDY_TARGET_RATIOS` / `STUDY_TARGET_TOL` / `STUDY_TARGET_SLACK_S` / `STUDY_MAX_PLANS_PER_REGION` | 4.5, 5.0, 6.0, 7.0, 8.0 / 0.05 / 0.5 s / 5 |
| `STUDY_MIN_REGIONS` / `STUDY_MIN_VIDEOS` / `STUDY_MAX_VIDEO_SHARE` | 15 / 8 / 0.25 |

##### 2.36.9.11 Owner decisions (resolved in v4.3)

| # | Decision | Resolution |
|---|---|---|
| V1 | Rubric and schema | **AGREED:** 5 scores, 7 issue types, `severity`, prompt `verifier_prompt@1` (superseded by `verifier_prompt@2` in v4.5); issue normalization; scores are ordinal. |
| V2 | Who decides | **AGREED:** the LLM scores, code decides; normalized input, hashes and raw output stored. |
| V3 | Repair | **AGREED (v4.5: targets are stable `cut_id`s, one repair pass may apply several operations):** R1 (unconditional for `dangling_reference`/`missing_setup`; bridge test for `non_sequitur`/`topic_jump`), R2; `abrupt_end` and `other` unrepairable; full Layer 1 revalidation; bridge scores recorded. |
| V4 | Strict band | **AGREED, provisional:** min score 4, mean 4.5, no major issue, no critical minor issue, at most one minor issue; not to be loosened before labeled results. |
| V5 | Gates | **AGREED:** V-G1 to V-G5 with sample counts, lower bounds, diversity requirements, Task 3 = 100 speech-led + 15 event-led plans. |
| V6 | Early stopping | **AGREED:** disabled; `VERIFY_ALL_PLANS = true`; experiment flag only; plan order recorded. |
| V7 | Viewer-only judge | **AGREED:** removed text never reaches the judge; judge and repair-engine inputs are separate. *(v4.5: the pre-region context is removed from the MVP judge as well, 2.36.9.3.)* |
| V8 | Invalid output | **AGREED:** the retry consumes the plan lineage's budget. |
| V9 | Low-transcript plans | **AGREED:** `LAYER1_ONLY_PASS`, flagged `unjudged`, reported separately, never equivalent to `TRANSCRIPT_VERIFIED_PASS`. |
| V10 | Artifacts and scope | **AGREED:** `verification_scope`, `semantic_validation`, `selection_policy`, original and judged bands stored independently; study-mode plans excluded from ranking and training. |

**Identifier namespaces (v5.0).** To prevent ambiguity in implementation and logs, current normative identifiers use these prefixes: `QC-1…QC-6` for qualification checks, `GLUE-1/GLUE-2` for glue rules, `GATE-*` for gates, `REPAIR-R1/R2` for repair operations, `R_DISC/R_T1/R_EDIT` for rate constants, and `LEDGER-*` for historical review rows. Historical ledgers may retain their old identifiers for traceability.

#### 2.36.10 Consolidated constants (all initial)

| Constant | Value | Section |
|---|---|---|
| `ROBUST_Z_ZERO_MAD` / `DEPTH_MAD_FLOOR` / `RMS_MAD_FLOOR` | 6.0 / 0.01 / 0.01 | 2.36.0, 2.36.5, 2.37 |
| `PROFILE_BIN_S` | 10 | 2.36.4 |
| `CP_WINDOW_BINS` / `CP_SIGMA` / `CP_MIN_DIST` | 6 / 1.5 / 1.0 | 2.36.4 |
| `CP_MIN_SEGMENT_S` / `CP_MIN_VIDEO_S` | 60 / 180 | 2.36.4 |
| `NORM_WPM`, `NORM_CUT_RATE`, `NORM_MOTION`, `NORM_PEAK_RATE` | 140, 12, 0.15, 3 | 2.36.4 |
| Activation thresholds `S_sem` / `S_vis` / `S_evt` | 0.30 / 0.35 / 0.35 | 2.36.4 |
| `WEIGHT_FLOOR` | 0.1 | 2.36.4 |
| `DEPTH_ABS_MIN` (`semantic` / `topic`) | 0.08 / 0.06 | 2.36.5 |
| `START_MIN` / `END_MIN` | 0.35 / 0.35 | 2.36.5 |
| `SEEDS_PER_10MIN` | 10 | 2.36.6 |
| `LOOKBACK_S` / `PREFERRED_EVENT_LEADIN_S` / `EVENT_MAX_LEADIN_S` / `LEADOUT_MIN_S` / `MAX_EVENT_S` | 20 / 6 / 15 / 4 / 45 | 2.36.6 |
| `EVENT_SAFE_PAUSE_MIN_S` / `EVENT_SAFE_SILENCE_MIN_S` | 0.5 / 1.5 | 2.36.0 |
| `TOPIC_STOP` | 0.6 | 2.36.6 |
| `CONT_MIN` | calibrated (25th percentile rule) | 2.36.6 |
| `MIN_REGION_SPEECH` / `MIN_REGION_EVENT` / `MIN_FINAL_DURATION_S_DEFAULT` | 10 / 6 / 8 | 2.36.3 |
| `LANGUAGE_SAMPLE_S` / `LANGUAGE_MIN_WORDS` / `LANGUAGE_CONF_MIN` | 60 / 20 / 0.90 | 2.14 |
| `MAX_COMPRESSION_RATIO` / `MAX_REGION_S` / `SINGLE_IDEA_EXTENSION` | 4.0 / 240 / 1.25 | 2.36.3 |
| `R_DISC` / `R_T1` / `R_EDIT` / `N_SHOW` | 1.0 / 0.4 / 0.25 per min / 10 | 2.36.7 |
| `T1_MIN_VIDEOS` | 8 | 2.38 |
| `T4_DEV_MIN_VIDEOS` / `T4_SEALED_MIN_VIDEOS` / `T4_MAX_VIDEO_SHARE` / `T4_MIN_CROSS_REGION_SHARE` / `T4_SAMPLING_SEED` | 32 / 12 / 0.10 / 0.50 / 20260920 | 2.36.1 |
| Dedup IoU thresholds | 0.7 / 0.5 | 2.36.7 |
| MMR λ; max shown-list source overlap | 0.7; 30% | 2.36.7 |
| `MAX_INTERVALS` / `MIN_KEEP_INTERVAL_S` | 6 / 3 (speech), 2 (event) | 2.36.8 |
| `MAX_PLANS_PER_REGION` / `DP_POOL` / `DP_BUCKET_S` | 3 / 20 / 0.1 | 2.36.8 |
| `REFRAME_GRID_PX` / `REFRAME_MAX_CENTER_JUMP_PX` / `REFRAME_MEDIAN_WINDOW_FRAMES` | 16 / 120 / 5 | 2.24 |
| `CAPTION_MAX_CHARS_PER_LINE` / `CAPTION_SAFE_ZONE` | 32 / x=0.05–0.95, y=0.78–0.93 | 2.24 |
| `LOUDNESS_TARGET_LUFS` / `TRUE_PEAK_MAX_DBTP` | −14 / −1.0 | 2.24 |
| `LONG_UNIT_S` / `SPLIT_PAUSE_MS` | 15 / 500 (glue rule G0 retired in v4.5) | 2.36.8 |
| `LAMBDA_CUT` | 0.15 | 2.36.8 |
| `DENSITY_NORM` / `PAYOFF_DECAY_UNITS` | 2.5 / 8 | 2.36.8 |
| `OPENING_CANDIDATES` / `CTX_MAX` | 3 / 0.5 | 2.36.8 |
| `OPENING_OBJ_TOL` | 0.10 | 2.36.8 |
| `AGGR_FACTOR` / `PLAN_DEDUP_DURATION_REL` / `MINIMAL_CLEANUP_RATIO_CAP` | 0.7 / 0.10 / 1.10 | 2.36.8 |
| `PAUSE_SHORTEN_THRESHOLD_S` / `PAUSE_TARGET_S` / micro-edit max density | 0.7 s / 0.35 s / 1 per 2 s | 2.36.8 |
| Filler-word removal confidence (LATER, unused in MVP) | 0.8 | 2.36.8 |
| `PASS_MIN_SCORE` / `PASS_MEAN_STANDARD` / `PASS_MEAN_STRICT` | 4 / 4.2 / 4.5 | 2.36.9 |
| `HARD_SCORE_MAX` / `STANDARD_RATIO_MAX` / `STRICT_MINOR_ISSUES_MAX` | 2 / 2.0 / 1 | 2.36.9 |
| `VERIFY_ALL_PLANS` / `EARLY_STOP_ACCEPTED_PLANS` / `EVALUATION_MODE` | true / disabled / false | 2.36.9 |
| `PLAN_VERIFY_ORDER` | minimal, balanced, aggressive; study adds deterministic ratio targets 4.5, 5.0, 6.0, 7.0, 8.0 | 2.36.9 |
| `JUDGE_MIN_WORDS` / `CONTEXT_BEFORE_S` / `JUDGE_MAX_EVIDENCE_WORDS` | 25 / 30 / 20 | 2.36.9 |
| `CUT_GAP_MIN_MS` / `CROSSFADE_MS` / `MIN_XFADE_MS` | 20 / 30 / 10 | 2.36.9 |
| `LOUDNESS_STEP_MAX_DB` / `LOUDNESS_XFADE_MS` / `EXT_XFADE_MIN_MS` | 12 / 100 / 60 | 2.36.9 |
| `NONSPEECH_RMS` | derived by `local_nonspeech_rms_v1` (rolling 60 s, 20th-percentile RMS) | 2.36.0 |
| `BRIDGE_MARGIN` / `REPAIR_DUPLICATE_OVERLAP` | 0.05 / 0.9 | 2.36.9 |
| `EVENT_ONSET_MARGIN_S` / `EVENT_MIN_FINAL_S` / `EVENT_EDIT_MAX_RATIO` / `SETTLE_TAIL_MIN_S` | 1.0 s / 6 s / 1.5 / 1.5 s | 2.36.9, 2.36.8 |
| `STUDY_MODE` / `STUDY_MAX_RATIO` / effective ceiling | false / 8.0 / `STUDY_MAX_RATIO if STUDY_MODE else MAX_COMPRESSION_RATIO` | 2.36.0, 2.36.9 |
| `STUDY_MIN_REGIONS` / `STUDY_MIN_VIDEOS` / `STUDY_MAX_VIDEO_SHARE` | 15 / 8 / 0.25 | 2.36.9 |
| `OPENING_WINDOW_S` / `OPENING_MIN_WORDS` / `OPENING_MAX_WORDS` / `HOOK_LLM_MIN_WORDS` | 3.0 / 15 / 40 / 8 | 2.37 |
| `HOOK_MAX_TYPES` / `HOOK_TYPE_CONF_MIN` / `MIN_TYPE_POSITIVES` / `STYLE_CONF_MIN` | 2 / 0.6 / 5 / 0.6 | 2.37 |
| `AUDIO_SIGNAL_Z` / `MOTION_SIGNAL_Z` / `FACE_SAMPLE_FPS` / `BOOTSTRAP_B` | 2.0 / 2.0 / 5 / 2000 | 2.37 |
| `RMS_MAD_FLOOR` / `MOTION_MAD_FLOOR` / `DEPTH_MAD_FLOOR` / `REL_MAD_FLOOR` | 0.01 / 0.01 / 0.01 / 0.05 | 2.36.0, 2.37, 2.39 |
| `MAX_REPAIR_ITERATIONS_PER_PLAN` / `MAX_JUDGE_CALLS_PER_PLAN` / `MAX_JUDGE_CALLS_PER_REGION` / `STUDY_MAX_JUDGE_CALLS_PER_REGION` | 1 / 2 / 6 / 10 | 2.36.9 |
| `REPAIR_RESTORE_DEPTH` | 1 (depth 2 is an offline experiment) | 2.36.9.6 |
| `ABSOLUTE_REGION_CEILING` / `MAX_SINGLE_IDEA_REGION_S` | 360 s / min(1.25 × 240, 360) = 300 s | 2.36.3 |
| `COH_A_WINDOW` / `COH_B_WINDOW` / `COH_A_MIN` / `COH_B_MIN` | 5 / 3 / 3 / 2 | 2.36.6 |
| `SETTLE_SNAP_MAX_S` | 3.0 s | 2.36.6 |
| `MIN_REGION_WORDS` / `SPEECH_RATIO_MIN` / `END_CONNECTIVES` | 30 / 0.4 / {and, but, so, because, or, then, which, that, if, when} | 2.9 |
| `context_dependency` weights (R, C, P) | 0.6 / 0.6 / 0.4 | 2.9.3 |
| Config artifacts (versioned) | `glue_lists@1`, `filler_hedge_vocab@1`, `stopwords_en@1`, hook opener filler list | 2.36.8, 2.37 |
| Prompts (versioned) | `verifier_prompt@2`, `hook_prompt@1`, `style_prompt@1` | 2.36.9, 2.37 |
| `visual_format` thresholds | `mixed` iff face≥0.20 AND screen≥0.20; else `screen_capture` iff screen≥0.50; else `talking_head` iff face≥0.20; else `other_visual` | 2.37.5 |
| Tier 1 constants | see 2.38.9 | 2.38 |
| Tier 2 constants | see 2.39.12 | 2.39 |

#### 2.36.11 Acceptance gates

| Gate | Condition | Blocks |
|---|---|---|
| G1 | Dataset built, agreement report passes (2.36.1). | Everything below. |
| G2 | Both baselines and the evaluation harness run on the dev set (2.17). | G3 onward. |
| G3 | Routing and local segmentation each clear the adoption gate (2.36.4), or the simpler variant becomes default. | Region-discovery default. |
| Q-G1 | Qualification loses at most 5 points of recall (2.9.4). | G4. |
| G4 | Recall@1.0 regions/min ≥ 0.85 (one-to-one loose matching, macro average, cluster-bootstrap interval reported) with ≥ 60% tight hits on dev, then confirmed on the sealed test (2.36.6). | Tier 1 and edit planning. |
| T1-G1..T1-G3 | Tier 1 retention ratio, precision lift, and comparison with the RS-only baseline (2.38.7). | Edit planning. |
| E-G1, E-G3, E-G4 | Edit-plan generation unit tests (including dedup invariants), diversity yield, p95 runtime (2.36.8.11; E-G2 is retired, its yield condition lives in V-G3). | Verification (2.36.9) sign-off. |
| G5 | V-G1 to V-G4 pass (2.36.9.9): Layer 1 tests, verifier precision with sample counts and video-cluster-bootstrap lower bound, recall and region yield, judge stability. Event-led Layer-1-only results reported separately. | Rendering and the review UI. |
| G6 | V-G5 compression study completed and reported; `MAX_COMPRESSION_RATIO` and `MAX_REGION_S` updated only by owner decision after the report (2.36.9.9). | Any compression above 4:1. |
| S-G1 | Style classifier macro-F1 (2.37.5). Must pass before edit planning may use extended ranges. | Extended-duration plans. |
| H-G1..H-G4 | Hook analyzer gates (2.37.7). | Tier 2 hook groups. |
| T2-G1..T2-G5, H-G5 | Tier 2 determinism, baseline comparison, cross-class comparability, exclusion audit, runtime, hook-group non-degradation (2.39.10). | Tier 2 sign-off and the review UI. |

---

### 2.37 Hook analysis, style taxonomy and Tier 2 opening inputs (F-2)

**Status: NORMATIVE in v5.0.** The hook-analysis, style and visual-format contracts below are implementation-authoritative. All numbers are *initial*. Hook feature adoption into Tier 2 remains gated by H-G4/H-G5 (2.37.7).

#### 2.37.1 Consumers and the two hook computations

The hook has two consumers with different cost limits, so there are two computations:

| Name | Consumer | Cost | Definition |
|---|---|---|---|
| `hook_lexical@1` | Opening selection in edit planning (2.36.8.5) and Tier 1; up to 3 openings × 2 intensities per region | CPU-only, near free | The lexical formula of 2.36.5 (`hook_potential`), unchanged. A labeled heuristic. |
| `hook_analysis_v1` | Tier 2 features; review UI ("hook excerpt", "why selected", 2.26) | CPU signals plus one bounded LLM call per distinct opening | This section. |

`hook_analysis_v1` runs **only** on plans whose `final_status` is not `FAIL`, reading the plan's `verified_edit_plan` (2.36.9.8a). It never runs on failed plans.

**Caching (v5.0).** The cache key is built from the **canonical analysis input**, not from the opening unit id. The canonical representation includes the actual verified output timeline prefix so semantically identical words with different timing are not conflated. Two plans can share `opening_unit_id` and opening text yet differ in the first 3 output seconds (a cut or a pause shortening inside the window) or in the timeline mapping, and would then wrongly share an analysis.

- **LLM cache key** = `sha256(canonical_llm_input)` + `prompt_version` + `model_id` + `timeline_mapping_version`, where `canonical_llm_input` serializes, in order, the selected sentence IDs, speaker labels, normalized sentence text and `[CUT]` markers, plus the output-time anchors derived from the verified timeline mapping. The exact byte serialization is versioned as `HOOK_CANONICAL_INPUT_VERSION`.
- **Signal cache key** = `sha256(canonical_signal_input)` + `signal_extractor_version` + `timeline_mapping_version`, where `canonical_signal_input` serializes `source_video_id`, the final verified timeline segments intersecting the first `OPENING_WINDOW_S` of output, their source/output start/end values and any applied crossfades. Signal cache reuse therefore depends on the actual mapped media window, not merely on an opening or region identifier.

"Same opening" stays a human-friendly notion (common for `minimal` and `balanced` plans of one region), but reuse happens only when the keys are identical. A change of prompt version, model, extractor, transcript, or of the opening part of the verified timeline produces a new key and therefore a new analysis.

There is **no composite hook score** in Tier 2. Tier 2 receives the structured features below; combining them is the ranker's job (2.39.4).

#### 2.37.2 Plan kind, output timeline and opening windows

**Plan kind.** `region_kind` is `event_led` if the Source Region's seed pattern is P4 (an EVENT seed, 2.36.6), otherwise `speech_led`. It is recorded in the Edit Plan (2.36.8.9). It decides the edit shape only; whether text analysis runs is decided separately by text applicability (below).

**Output timeline (canonical).** Every temporal value in `hook_analysis_v1` is in **output milliseconds** of the final plan; source timestamps are provenance only. Output time is defined once, by the `timeline` of the `verified_edit_plan` (2.36.9.8a; the generator's `timeline` in 2.36.8.9 is its provisional form), and every consumer (verifier transcript builder, hook analyzer, captions, renderer) reads it; none reconstructs it. A plan whose opening begins at a nonzero source timestamp, or that contains cuts, crossfades or pause micro-edits, is handled by that mapping, not by extractor-specific arithmetic.

**Windows** (both on the output timeline):

- `signal_window` = the first `OPENING_WINDOW_S` (3.0 s) of output. Used by deterministic audio/visual signals.
- `text_window` = complete sentences, built by these rules **in this precedence**:
  1. Start with every sentence that overlaps the `signal_window`. This step is mandatory, even if it exceeds the maximum.
  2. While `word_count < OPENING_MIN_WORDS` (15), add the next complete sentence **only if** the total stays ≤ `OPENING_MAX_WORDS` (40); otherwise stop.
  3. Never cut mid-sentence. If step 1 alone exceeds 40 words, keep the complete sentence(s) and set `over_max_words = true`.
  4. If the plan ends before the window is complete, set `window_truncated_by_plan_end = true`.
  
  Recorded metadata: `sentence_ids`, `word_count`, `over_max_words`, `under_min_words`, `window_truncated_by_plan_end`. The hook LLM sees only the `text_window`, with speaker labels, `[CUT]` markers for any content cut inside the window, and no context before the region (the viewer has none).

**Text applicability.** The LLM part runs iff the `text_window` has at least `HOOK_LLM_MIN_WORDS` (8) words. Otherwise it is skipped with `missing_reason = not_applicable` and `analysis_status = "partial"` (typical for event-led plans).

#### 2.37.3 Signals and extraction contracts

Every feature is stored as `{ "v": value | null, "m": missing_reason | null }`. `m` is one of:

| `m` | Meaning |
|---|---|
| `not_run` | The stage did not execute (disabled, or an experiment flag). |
| `not_applicable` | The required input does not exist by design (no text window; an unjudged plan has no verifier scores). |
| `extraction_failed` | The extractor errored or the media/timestamps needed were unavailable. |
| `invalid_output` | LLM output failed validation after the single retry. |
| `not_available_in_stage` | The feature cannot exist at this stage yet. |
| `no_detection` | *(v4.5, R28)* The extractor ran successfully on valid input and found nothing (for example, no question rule fired in the `text_window`, or the model reports no explicit promise). This is a legitimate **negative observation**, not a failure. |

A computed feature is `{ "v": value, "m": null }`; otherwise `{ "v": null, "m": reason }`. `no_detection` differs from every other reason in that the observation *is* available and informative ("there is no question hook"), whereas `not_run`, `not_applicable`, `extraction_failed`, `invalid_output` and `not_available_in_stage` mean the observation is unavailable. Tier 2 must not treat these nulls as equivalent. Extractor versions are recorded per feature **group** (a group shares one extractor); each feature's version is derived from its group. Nothing is imputed silently.

**A. Deterministic signals (CPU, cost class `low`)**

Definitions used below: *filler tokens* = `um, uh, erm, so, okay, ok, hey, hi, hello, welcome, guys, yeah, well` (configurable, English). *Content words* = tokens not in the English stopword list and not filler.

| feature_id | Algorithm | Output / normalization |
|---|---|---|
| `hook.first_content_ms` | Output time of the first non-filler word in the plan. | int ms |
| `hook.immediate_content_ratio` | Sum over non-filler words of the overlap of the word interval with the `signal_window`, divided by `OPENING_WINDOW_S`. | 0–1, clipped |
| `hook.info_density` | Content words in the `text_window` divided by the output duration of the `text_window` in seconds; `min(1, x / DENSITY_NORM)`. | 0–1 |
| `hook.first_question_ms`, `hook.first_number_ms`, `hook.first_claim_ms` | **Temporal anchors (v4.5, R29).** *Question* is evaluated per sentence of the `text_window`: if the lexical rule fires (ASR punctuation OR the interrogative-opener rule of 2.36.5) the anchor is the output time of the **sentence's first word**; otherwise, if the rising-pitch check fires, the anchor is the **start of the qualifying pitch interval** (the terminal rise, usually at the sentence end). `first_question_ms` = the earliest anchor over the sentences of the `text_window`; log `question_rule` (`punctuation`, `interrogative_opener`, `pitch_rise`) and `anchor_type` (`sentence_start`, `pitch_interval_start`). *Number* and *claim* are token-level rules: the anchor is the output time of the first matching token (number, currency or percent; claim-word list). If no rule fires: `v = null`, `m = no_detection`. | int ms |
| `hook.cue_question`, `hook.cue_number`, `hook.cue_claim_word` | `true` iff the matching `first_*_ms` has a value; `false` with `m = no_detection` when the matching feature has `no_detection`; if the matching feature is null for another reason, the cue carries that same `m`. | bool |
| `hook.first_audio_event_ms` | First output time in the `signal_window` where RMS has `robust_z_v1(RMS, rolling_median, rolling_MAD, RMS_MAD_FLOOR) ≥ AUDIO_SIGNAL_Z` (2.0) against the 60 s rolling baseline (the peak definition of 2.36.4). | int ms |
| `hook.first_motion_ms` | First output time in the `signal_window` where `robust_z_v1(motion, video_median, video_MAD, MOTION_MAD_FLOOR) ≥ MOTION_SIGNAL_Z` (2.0), sustained ≥ 0.3 s. A threshold **crossing**, not the peak. | int ms |
| `hook.audio_onset_in_window` | `true` iff `first_audio_event_ms` is non-null. | bool |
| `hook.motion_in_window` | `robust_z_v1(mean_motion, video_median, video_MAD, MOTION_MAD_FLOOR)` | float, clipped to [−3, 6] |
| `hook.cuts_in_window` | Shot cuts inside the `signal_window`, mapped to output time. | int |
| `hook.face_ratio_in_window` | Share of samples with a face, sampled at `FACE_SAMPLE_FPS` (5); null with `extraction_failed` if fewer than 5 samples. | 0–1 |
| `hook.first_signal_ms` | Derived from the five component anchors as follows: if any applicable component has a value, use the earliest value; else if all components are `not_applicable`, return `null, m = not_applicable`; else if any applicable component has `extraction_failed` or `invalid_output`, return `null, m = extraction_failed`; else return `null, m = no_detection`. | int ms |

`first_signal_ms` is a convenience feature. Each component is stored and can be null, validated and ablated on its own. A lexical rule can fire incidentally ("in today's video I spent three hours…"), so `first_signal_ms` is never a hard penalty and is subject to ablation (H-G4).

**B. Reused from the verifier (no new computation)**

| feature_id | Source |
|---|---|
| `hook.context_independence` | Raw score `opening_standalone` ÷ 5 from the **final judgment** of the plan (the repaired plan's judgment if the lineage was repaired). |
| `hook.requires_prior_context` | Whether the normalized issue list of that judgment contains `opening_dependent`. |

Provenance is recorded: `verification_id`, verifier `stage_version`, `prompt_version`, `judge_call_index`, and the raw `opening_standalone` integer. Values are computed from the stored raw output, never from a reinterpretation. For `LAYER1_ONLY_PASS` plans both features are null with `m = not_applicable`. Plans that failed judgment never reach hook analysis, so `invalid_output` cannot occur here. The hook analyzer does not ask the LLM about context dependence a second time (2.16: no duplicate, possibly conflicting, features).

**C. LLM signals (cost class `medium`, one call per distinct opening)**

Output schema `hook_llm_output@1`; temperature 0; JSON-schema-constrained output where supported; validated by code; invalid output → one retry → otherwise these fields are null with `m = invalid_output` and `analysis_status = "partial"`:

```json
{
  "schema_version": 1,
  "hook_types": ["question"],
  "type_confidence": 0.0,
  "curiosity_gap": 1,
  "promise_clarity": 1,
  "emotional_intensity": 1,
  "promise_sentence_index": null
}
```

- `curiosity_gap` (1–5): 1 nothing left open | 3 an implied open question | 5 an explicit, specific, unresolved promise.
- `promise_clarity` (1–5): 1 cannot tell what the short is about | 3 the topic is clear but not what the viewer will get | 5 topic and payoff are both clear.
- `emotional_intensity` (1–5): 1 flat | 3 mild | 5 strong expressed emotion in the words.
- `hook_types`: up to `HOOK_MAX_TYPES` (2) tags from 2.37.4. `primary_hook_type` = the first tag if `type_confidence ≥ HOOK_TYPE_CONF_MIN` (0.6), else null.
- `promise_sentence_index`: 0-based index **into the `text_window`** of the sentence where the promise is established, or null.

Scores are ordinal anchors, not calibrated probabilities. Prompt `hook_prompt@1`:
```text
SYSTEM
You classify the form and immediate hook signals of the supplied short opening. Judge only what a viewer can infer from the visible/audible opening itself. Do not use or infer information outside the supplied opening. Do not judge whether the short is good, viral, or likely to perform well. Return JSON only.
USER
Return exactly the requested fields: hook_types (0–2 tags from the taxonomy), type_confidence (0–1), curiosity_gap (1–5), promise_clarity (1–5), emotional_intensity (1–5), promise_sentence_index (0-based into the supplied text_window or null).
Validation `validate_hook_semantics@1`: `hook_types` must be a duplicate-free subset of the versioned taxonomy with length 0–2; `type_confidence`, `curiosity_gap`, `promise_clarity`, and `emotional_intensity` must be numeric and in their declared ranges; `promise_sentence_index` must be null or an integer in `[0, sentence_count(text_window)-1]`; out-of-range or cross-field-invalid outputs are `invalid_output` and consume the single bounded retry.
TEXT_WINDOW
<text_window>...</text_window>
```

**`validate_hook_semantics@1`.** In addition to JSON-schema validation, code requires: `hook_types` is a duplicate-free subset of 2.37.4 with length ≤ `HOOK_MAX_TYPES`; `type_confidence ∈ [0,1]`; all three ordinal scores are integers 1–5; `primary_hook_type` is either the first supplied type when confidence ≥ `HOOK_TYPE_CONF_MIN` or null; `promise_sentence_index` is null or an integer; a non-null index is within `[0, sentence_count−1]`. Any cross-field violation is `invalid_output` and consumes the hook lineage retry exactly once.


**Conversion contract for `hook.promise_established_ms` (code, deterministic):**

| Model output | Result |
|---|---|
| Valid index into the `text_window` | Output time of the first word of that sentence; `promise_sentence_index_valid = true`. |
| `null` | `v = null`, `m = no_detection` (the model reports no explicit promise). |
| Index outside `[0, sentence_count − 1]` | `v = null`, `m = invalid_output`, reason recorded (`promise_index_out_of_range`). Never clamped. |
| Valid index but the sentence has no usable word timestamps | `v = null`, `m = extraction_failed`. |
| Event-led plan without a text window | `v = null`, `m = not_applicable`. |

Whether the indexed sentence really contains the promise cannot be checked deterministically. It is monitored through run-to-run agreement of the index (H-G2), not asserted.

**Deliberately not in the MVP** (each is a later experiment that must pass the H-gates): `novelty` (no baseline); facial emotion or any VLM interpretation of the opening (2.32); `starts_mid_sentence` (false by construction, `L1_FORCED`); a stored `long_setup` flag (Tier 2 derives it from `first_content_ms` / `promise_established_ms`).

**Time-to-hook is three separate features:** `hook.first_content_ms`, `hook.promise_established_ms`, `hook.first_signal_ms`. None is a hard penalty in MVP; Tier 2 sees all three with their missingness.

#### 2.37.4 Hook type taxonomy (MVP)

Types describe the **form** of the opening, not its quality.

| Type | Meaning |
|---|---|
| `question` | Opens with a direct question or problem statement |
| `claim` | A strong assertion or an unexpected fact/reversal |
| `curiosity_gap` | Creates an explicit information gap or promise |
| `result_first` | States or shows the outcome before the explanation |
| `story_setup` | Starts a situation, event, conflict or stakes |
| `direct_value` | Immediately gives an answer, instruction or insight |
| `context_intro` | Introduction or setup before the main value |
| `visual_or_reaction` | A visual event or expressive reaction is the opening (event-led; deterministic signals only in MVP) |
| `other` | None of the above |

**Retention rule.** Hook-type labels are collected in Task 2 by A1 and a blind A2 on at least 30% of videos (2.36.1). Human agreement and model consistency are separate metrics (2.37.7 H-G2 measures the model). For each type report: prevalence (number of positive labels by each annotator), one-vs-rest Cohen's κ on the blind subset, and, as a secondary multi-label diagnostic, the Jaccard similarity of the two annotators' tag sets. Disposition:

| Condition | Outcome |
|---|---|
| κ ≥ 0.6 and at least `MIN_TYPE_POSITIVES` (5) positive labels in the blind subset | Retained; eligible as a Tier 2 categorical feature after an ablation shows lift (H-G4). |
| κ not evaluable (fewer than 5 positives) but the type is meaningful | Explanation-only (review UI); not a Tier 2 feature. |
| κ < 0.6 | Merged into `other`. |

Any change to a type's definition or membership increments the taxonomy version. The list merges an earlier 11-type draft (bold claim + surprise reveal → `claim`; narrative setup + conflict/tension → `story_setup`; visual event + reaction → `visual_or_reaction`) because annotators are unlikely to separate those reliably.

#### 2.37.5 Style taxonomy — three separate axes

| Axis | Values | Consumer | Assignment |
|---|---|---|---|
| `content_style` | `story`, `tutorial`, `explanation`, `conversation_qa`, `commentary`, `event`, `other` | 2.36.2 rule 2; review UI; annotation | One bounded LLM classification call per region sent to edit planning, on the canonical style passage defined in 2.37.5.1. It runs in `CLASSIFYING_STYLE`, **before** `PLANNING_EDITS`. `event_led` regions are `event` by rule with no call. On failure, invalid output, or confidence < `STYLE_CONF_MIN`, code returns `other` conservatively. |
| `visual_format` | `talking_head`, `screen_capture`, `mixed`, `other_visual` | Coarse region-level visual descriptor used before editing | Deterministic from region-level rates using the explicit precedence below. It is retained for explanation/routing only. The **final** `verified_edit_plan.final_visual_format` is the authoritative reframe input. |
| `editing_intensity` | `minimal`, `balanced`, `aggressive` | Already defined (2.36.8.7) | From the plan. |

**`visual_format@1` decision rule.** Compute `face_ratio` and `screen_ratio` over the retained source samples before editing. Apply the first matching rule: (1) `mixed` if both rates exist and `face_ratio >= VIS_FACE_MIXED_MIN` and `screen_ratio >= VIS_SCREEN_MIXED_MIN`; (2) `screen_capture` if `screen_ratio` exists and `screen_ratio >= VIS_SCREEN_MIN`; (3) `talking_head` if `face_ratio` exists and `face_ratio >= VIS_FACE_MIN`; otherwise `other_visual`. If both rates are missing, return `other_visual` with `visual_format_missing = true`. If only one is missing, skip rules that require the missing rate and record the missing input; never substitute zero. The same rule is applied to `final_visual_format` on the verified retained timeline. Thresholds are initial and must be calibrated against labeled visual-format/reframe outcomes before production sign-off; the calibration reports confusion by format and crop-confidence outcomes.

**Label definition and migration.** Task 2 collects `content_style` with the seven values above (replacing the earlier undefined "editing-style tag"). If any labeling was already done with the old field, keep a mapping table `legacy_annotation → content_style | visual_format | editing_intensity`; any legacy value with no unambiguous mapping must be relabeled on the affected regions before S-G1 is measured. Macro-F1 against a field that mixes axes would not measure this classifier.

**Gate S-G1.** Against the human `content_style` labels, the classifier must reach macro-F1 ≥ 0.70 over the classes with at least 5 labeled regions; otherwise `content_style` is forced to `other` everywhere and the extended range stays disabled until fixed. S-G1 also requires the visual-format calibration report to be complete before production sign-off: it must report confusion by `visual_format`, missing-signal branch coverage, and the relationship between `final_visual_format`, reframe strategy and `crop_confidence`. Threshold changes require an explicit config/version bump. S-G1 also reports a reliability table (accuracy per confidence bin 0.6–0.7, 0.7–0.8, 0.8–0.9, 0.9–1.0) and the style confusion matrix.

##### 2.37.5.1 `content_style_v1` extraction contract (v5.0 — NORMATIVE)

This is the normative classifier contract. The axis decision H7 and owner decision T3 are resolved in 2.39.13.

| Field | Contract |
|---|---|
| Stage / state | `CLASSIFYING_STYLE`, after Tier 1 and before `PLANNING_EDITS`. Runs for every region in the `send_to_edit` set and in each backfill batch (2.38.6). Cost class `medium`, about 0.25 calls per source minute. |
| Input | Build `canonical_passage` from the full region transcript (speaker labels, sentence breaks, no source timestamps). If tokenized length ≤ `STYLE_MAX_INPUT_TOKENS` (4000), use it unchanged. If longer, deterministically keep exactly the first `STYLE_HEAD_TOKENS` (2000) tokens, then one literal `<TRUNCATED>` marker, then exactly the last `STYLE_TAIL_TOKENS` (1900) tokens. The marker is not taken from the source. No text from outside the region is permitted; do not rebalance the head/tail counts. Record `STYLE_TOKENIZER_VERSION`, the final token count (≤3901), the truncation flag, and the exact canonical-passage SHA-256. This canonical passage is the only classifier input. |
| Event-led regions | `content_style = event`, `style_status = rule_event`, **no call**. |
| Settings | Temperature 0, JSON-schema-constrained output where supported, `STYLE_MODEL` config value re-verified at implementation time. |
| Validation | Valid JSON; `content_style` in the six model classes; `confidence` a number in [0, 1]; `evidence` ≤ 20 words. Invalid → one bounded retry → `content_style = other`, `style_status = invalid_output`. Transport errors use the shared non-budgeted transport retry taxonomy of 2.36.9.3. |
| Decision (code) | `content_style` = the model class if `confidence ≥ STYLE_CONF_MIN` (0.6); otherwise `other` with `style_status = low_confidence`. `other` never allows the extended range. |
| Confidence semantics | The model's self-reported ordinal estimate, **not** a calibrated probability. It is only compared with the threshold; S-G1's reliability table shows how it behaves. Changing the threshold is an owner decision. |
| Cache key | `sha256(STYLE_CACHE_VERSION + STYLE_TOKENIZER_VERSION + canonical_passage) + prompt_version + model_id`. The canonical passage is byte-identical before hashing, and the tokenizer/truncation versions are part of the key. |

Prompt `style_prompt@1`:

```text
SYSTEM
You classify the content style of a spoken passage taken from a longer video. Choose exactly one class.
story            a personal or narrative account of events, with a beginning, development and outcome
tutorial         step-by-step instruction or a demonstration of how to do something
explanation      explains why or how something works, or argues a point, without step-by-step instruction
conversation_qa  a question that is answered, or a back-and-forth between speakers, is the main structure
commentary       opinion, reaction or analysis about something
other            none of the above fits clearly
Return JSON matching the schema and nothing else. "confidence" is your own estimate from 0 to 1.
USER
<passage>...</passage>
```

Output schema `content_style_output@1`:

```json
{ "schema_version": 1,
  "content_style": "story | tutorial | explanation | conversation_qa | commentary | other",
  "confidence": 0.0,
  "evidence": "<= 20 words" }
```

Artifact `content_style_v1`:

```json
{ "content_style_id": "uuid", "source_region_id": "uuid", "schema_version": 1, "stage_version": "content_style@1",
  "config_version": "config@1", "config_sha256": "…",
  "language_code": "en", "prompt_version": "style_prompt@1", "model_id": "…", "temperature": 0,
  "tokenizer_version": "style_tokenizer@1",
  "canonical_passage_sha256": "…",
  "input_tokens": 0, "truncated": false, "raw_output": {}, "valid": true,
  "style_status": "ok | low_confidence | invalid_output | rule_event",
  "content_style": "story | tutorial | explanation | conversation_qa | commentary | event | other",
  "confidence": 0.0,
  "visual_format": "talking_head | screen_capture | mixed | other_visual",
  "extended_range_allowed": false }
```

`extended_range_allowed` = `content_style ∈ {story, tutorial, explanation}` (2.36.2 rule 2); it is a derived boolean read by edit planning.

#### 2.37.6 Failure behavior and cost report

- `analysis_status`: `complete` (all groups present) | `partial` (LLM group missing or not applicable) | `failed` (nothing usable) | `retryable_transport_error` | `not_applicable`.
- Every null carries a `missing_reason` (2.37.3). Tier 2 defines its own treatment of each (2.39.4).
A stage may make at most `STAGE_MAX_ATTEMPTS = 3` end-to-end attempts; each LLM call may use at most `LLM_MAX_TRANSPORT_RETRIES = 2` transport retries. Exhausting stage attempts returns `retryable_transport_error` to the job orchestrator; it does not invent a semantic verdict.

- **Cost is defined by the LLM cache key (2.37.1), not by the number of plans.** Per source video, record: `hook_calls_requested`, `cache_hits`, `initial_calls`, `retries`, `successful_analyses`, `failed_analyses`, `style_calls`, `reprocessed_after_version_change`, and cost per source minute (2.28). The structural worst case for a 60-minute video is 45 hook calls (15 regions × 3 plans) plus 15 style calls; the measured number is expected to be lower because openings are shared.

#### 2.37.7 Validation and adoption gates

**Labels.** Task 2 collects hook quality 1–5 per region opening. Task 3 adds hook quality 1–5 for the opening of every plan (the Short hook after editing). Hook-type tags are collected on Task 2 openings.

**Models compared** on the labeled **speech-led, text-eligible Task 3 openings** only: (i) `hook_lexical@1`; (ii) adoption unit `A+B` with ridge regression; (iii) adoption unit `A+B+C` with ridge regression. Hook adoption is therefore evaluated at the same granularity used by Tier 2; C is an optional incremental unit after `A+B`. Event-led and low-speech/class-B openings are evaluated separately for deterministic signal validity and are not pooled into the text-model correlation analysis.

**Procedure (identical for all models).**
- **Folds:** leave-one-video-out on the dev set, the same folds for every model (splits by source video, 2.20). The ridge penalty is chosen from a fixed grid by an inner leave-one-video-out over the training videos of each fold.
- **Missing values:** imputed with the training-fold median plus a missingness indicator, fitted inside each fold. Rows are not dropped for missing features. Rows with a missing human label are excluded, and their number is reported.
- **Metric:** Spearman ρ between out-of-fold predictions and human hook quality, with ties given average ranks.
- **Bootstrap:** resample videos with replacement `BOOTSTRAP_B` (2000) times; for each replicate recompute ρ for each model from the fixed out-of-fold predictions (no refit) and take the difference; the interval is the 95% percentile interval of the difference.
- The sealed test set is evaluated once per phase.

| Gate | Condition |
|---|---|
| H-G1 | Deterministic extractors pass unit tests: filler stripping, output-timeline windows (including a plan that starts at a nonzero source timestamp and plans with cuts and crossfades), the text-window precedence rules, and null/`missing_reason` handling. |
| H-G2 | LLM output valid ≥ 99% after one retry; two runs agree: mean absolute difference ≤ 0.5 per ordinal signal, type-set Jaccard ≥ 0.7, `promise_sentence_index` agreement ≥ 0.8. |
| H-G3 | Human agreement on hook quality: quadratic-weighted κ between A1 and blind A2 ≥ 0.5; otherwise rewrite the guidelines and relabel. |
| H-G4 | **Hook-feature adoption (necessary, not sufficient).** Adoption unit `A+B` must beat (i), and `A+B+C` must beat `A+B`, each with a bootstrap 95% interval for the ρ difference whose lower bound is above 0. A failed unit is not used and stays an experiment. |
| H-G5 | **Tier 2 incremental adoption (evaluated when the Tier 2 ranker exists).** A hook feature group that passed H-G4 is adopted into Tier 2 only if adding it does not degrade the Tier 2 ranking objective, evaluated on held-out videos with duration, payoff, context and edit-density features already included. The objective and pairwise protocol are defined in 2.39.9. |

Correlation with human hook ratings alone never supports the claim that a hook feature improves short selection. The bootstrap rule is deliberate: uncertainty is reported at the video level, and the usable text-opening sample size is reported explicitly rather than assumed to be 115. Event-led/class-B signal results are reported separately.

#### 2.37.8 Artifact `hook_analysis_v1`

Each `{v, m}` pair follows 2.37.3; the schema is abbreviated to values for readability.

```json
{
  "hook_analysis_id": "uuid",
  "edit_plan_id": "uuid",
  "schema_version": 1,
  "stage_version": "hook_analysis@1",
  "config_version": "config@1",
  "config_sha256": "…",
  "language_code": "en",
  "region_kind": "speech_led | event_led",
  "verified_edit_plan_id": "uuid",
  "llm_cache_key": "…",
  "signal_cache_key": "…",
  "timeline_ref": "verified_edit_plan_id#timeline",
  "text_window": { "sentence_ids": [], "word_count": 0, "over_max_words": false,
                   "under_min_words": false, "window_truncated_by_plan_end": false, "text_sha256": "…" },
  "signal_window_ms": 3000,
  "deterministic": { "extractor_version": "hook_signals@1",
                     "first_content_ms": {}, "immediate_content_ratio": {}, "info_density": {},
                     "first_question_ms": {}, "first_number_ms": {}, "first_claim_ms": {},
                     "cue_question": {}, "cue_number": {}, "cue_claim_word": {},
                     "first_audio_event_ms": {}, "first_motion_ms": {}, "audio_onset_in_window": {},
                     "motion_in_window": {}, "cuts_in_window": {}, "face_ratio_in_window": {},
                     "first_signal_ms": {} },
  "from_verifier": { "verification_id": "uuid", "verifier_stage_version": "verifier@2",
                     "prompt_version": "verifier_prompt@2", "judge_call_index": 1,
                     "opening_standalone_raw": null,
                     "context_independence": {}, "requires_prior_context": {} },
  "llm": { "prompt_version": "hook_prompt@1", "model_id": "…", "temperature": 0,
           "hook_types": {}, "primary_hook_type": {}, "type_confidence": {},
           "curiosity_gap": {}, "promise_clarity": {}, "emotional_intensity": {},
           "promise_sentence_index": null, "promise_sentence_index_valid": null,
           "promise_established_ms": {}, "raw_output": {}, "valid": true },
  "analysis_status": "complete | partial | failed | retryable_transport_error | not_applicable"
}
```

#### 2.37.9 Constants (all initial)

| Constant | Value |
|---|---|
| `OPENING_WINDOW_S` | 3.0 |
| `OPENING_MIN_WORDS` / `OPENING_MAX_WORDS` / `HOOK_LLM_MIN_WORDS` | 15 / 40 / 8 |
| `HOOK_MAX_TYPES` / `HOOK_TYPE_CONF_MIN` / `MIN_TYPE_POSITIVES` | 2 / 0.6 / 5 |
| `LANGUAGE_SAMPLE_S` / `LANGUAGE_MIN_WORDS` / `LANGUAGE_CONF_MIN` | 60 s / 20 / 0.90 | 2.14 |
| `STYLE_CONF_MIN` | 0.6 |
| `STYLE_MAX_INPUT_TOKENS` / `STYLE_HEAD_TOKENS` / `STYLE_TAIL_TOKENS` | 4000 / 2000 / 1900 | 2.37.5.1 |
| `STYLE_TOKENIZER_VERSION` / `STYLE_CACHE_VERSION` | 1 / 1 | 2.37.5.1 |
| `HOOK_CANONICAL_INPUT_VERSION` / `TIMELINE_MAPPING_VERSION` / `HOOK_SEMANTIC_VALIDATOR_VERSION` | 1 / 1 / 1 | 2.37.1–2.37.3 |
| `VIS_FACE_MIXED_MIN` / `VIS_SCREEN_MIXED_MIN` | 0.20 / 0.20 | 2.37.5 |
| `VIS_SCREEN_MIN` / `VIS_FACE_MIN` | 0.50 / 0.20 | 2.37.5 |
| `AUDIO_SIGNAL_Z` / `MOTION_SIGNAL_Z` | 2.0 / 2.0 |
| `FACE_SAMPLE_FPS` | 5 |
| Motion z clip range | [−3, 6] |
| `BOOTSTRAP_B` | 2000 |
| Filler list, English stopword list | configurable |
| `DENSITY_NORM` | 2.5 (shared with 2.36.8.4) |

#### 2.37.10 Owner decisions (resolved in v4.4)

| # | Decision | Resolution |
|---|---|---|
| H1 | Scope | **AGREED:** speech-led plans get the full analysis; event-led plans get deterministic audio/visual signals only; no VLM in MVP. `region_kind` comes from the seed pattern; text applicability is decided separately (`HOOK_LLM_MIN_WORDS`). |
| H2 | Composite score | **AGREED:** none in Tier 2; `hook_lexical@1` stays for opening selection and Tier 1. *(v4.5: the Tier 2 hook term uses only groups adopted by H-G4/H-G5 and there is no `hook_lexical@1` fallback in Tier 2 unless the owner decides otherwise, 2.39.4 / decision T5.)* |
| H3 | Signal set | **AGREED:** as in 2.37.3, with explicit algorithms and normalization; `novelty`, `starts_mid_sentence` and a stored `long_setup` dropped. |
| H4 | Verifier reuse | **AGREED:** reused from the final judgment with provenance; never recomputed. |
| H5 | Taxonomy | **AGREED:** eight types plus `other`, up to 2 tags; retention needs κ ≥ 0.6 and a minimum number of positives; explanation-only and merge dispositions defined. |
| H6 | Time-to-hook | **AGREED:** three separate features; `first_signal_ms` derived from independently stored components (threshold crossings, not peaks); sentence index converted by code with an explicit invalid-index contract. |
| H7 | Style | **AGREED:** three axes; conservative `content_style` default; label migration rule; S-G1. *(Historical v4.5 note: the `content_style_v1` contract was originally drafted there; it is **NORMATIVE in v5.0** below. `visual_format` precedence is explicit and style runs before edit planning.)* |
| H8 | Adoption | **AGREED:** identical folds, imputation, ties and cluster bootstrap specified (H-G4); Tier 2 incremental gate H-G5 added. |
| — | Timeline | **AGREED (amendment):** a canonical output-timeline mapping in the Edit Plan; all temporal features are in output milliseconds. *(v4.5: after verification the authoritative timeline is the one in the `verified_edit_plan`, 2.36.9.8a.)* |


### 2.38 Tier 1 — Region prioritizer (v5.0 — NORMATIVE)

**Status: NORMATIVE in v5.0.** Owner decisions T1–T2 are resolved in 2.39.13. All numbers remain *initial* and are changed only by the calibration/gate procedures.

#### 2.38.1 Contract

**Input:** the qualified regions that survived dedup and the `R_DISC` cap (2.9, 2.36.7), each with its `qualification_record`, `RS`, pattern, seed, sentences, signals.
**Output:** one `tier1_score_v1` artifact per region (2.38.8), the ordered `keep_T1` set, the ordered `send_to_edit` set and the ordered `backfill` queue.
**Cost class:** low. Deterministic, CPU-only, **no LLM** in MVP. Tier 1 is an *opportunity* score aimed at recall; it is never called a virality score (2.2).

#### 2.38.2 Feature vector

Every feature is in [0, 1], absolute (no percentile rank, no per-video z-score), and stored as `{ "v", "m" }` with the missing reasons of 2.37.3. Higher is better.

| feature_id | Definition | Null (reason) when |
|---|---|---|
| `t1.hook` | Best `hook_lexical@1` (2.36.5) over the first `OPENING_CANDIDATES` (3) valid **super-unit starts** of the region (2.36.8.5). If none exists, null with `m = no_valid_opening`. | event-led (`not_applicable`) or no valid opening (`no_valid_opening`) |
| `t1.boundary` | `0.5·StartScore(region start) + 0.5·EndScore(region end)` (2.36.5). | never |
| `t1.completeness` | `pattern_completeness` (2.36.6). | never |
| `t1.standalone` | `1 − context_dependency(first sentence)` (2.9.3). | event-led (`not_applicable`) |
| `t1.density` | `min(1, content_words_per_second / DENSITY_NORM)` over the region's speech time. | event-led or fewer than 8 words (`not_applicable`) |
| `t1.energy` | `mean( norm(audio_peak_rate, NORM_PEAK_RATE), norm(motion_peak_rate, NORM_PEAK_RATE) )`, rates per minute of region time, peak definition of 2.36.4; a null input is excluded. | both inputs null (`extraction_failed`) |
| `t1.duration_fit` | From shared `d_clean_v1(region, export_profile_id)` and the **production** compression ceiling `MAX_COMPRESSION_RATIO`: 1.0 if `plan_min_s ≤ D_clean ≤ primary_range_max_s`; 0.7 if `D_clean ≤ 2.0 × primary_range_max_s`; 0.4 if `D_clean ≤ MAX_COMPRESSION_RATIO × primary_range_max_s`; else 0. Event-led uses `plan_min_s = EVENT_MIN_FINAL_S`. Study-mode ceilings never change Tier-1 production ranking. | never |
| `t1.live_air` | `1 − dead_air_ratio`, where `dead_air_ratio` = share of region time that is silent (RMS ≤ `local_nonspeech_rms_v1(t)`) and has no word. | never |

#### 2.38.3 Score, normalization, missingness

```text
weights (initial):  hook 0.15, boundary 0.20, completeness 0.15, standalone 0.15,
                    density 0.10, energy 0.10, duration_fit 0.10, live_air 0.05        (sum = 1.00)

region_priority_score = Σ_{f present} w_f · f  /  Σ_{f present} w_f          (present = non-null)
coverage              = Σ_{f present} w_f
low_evidence          = coverage < 0.5
```

- Missing features are excluded and the remaining weights renormalized (the same convention as `StartScore`, 2.36.5). The artifact stores `coverage` and every `m`, so nothing is hidden.
- Scores are **absolute**: a uniform, low-variance video may produce uniformly modest scores (2.31). An absolute floor `T1_MIN_SCORE` (0.25) applies: a region below it is not kept, **except** that the per-video floors of 2.36.7 always win (`R_T1` floor 4, `R_EDIT` floor 3).
- Event-led regions have fewer applicable features, so their renormalized scores are computed from fewer inputs. Their recall is therefore reported separately (2.38.7).

#### 2.38.4 Ordering and tie-break (deterministic)

Sort key: `(round(region_priority_score, 4) descending, RS descending, start_ms ascending, region_id ascending)`.

#### 2.38.5 Selection and budgets

```text
n_min      = duration in minutes
K_T1       = clip( round(R_T1  × n_min), 4, 40 )      (R_T1 = 0.4)     also ≤ number of qualified regions
K_EDIT     = clip( round(R_EDIT × n_min), 3, 25 )     (R_EDIT = 0.25)

keep_T1      = the first K_T1 regions in sort order whose score ≥ T1_MIN_SCORE, topped up (in sort order) to the
               per-video floor of 4 if fewer qualify
send_to_edit = walk the ranked `keep_T1` set in order; take a region unless it overlaps an already taken region with
               temporal IoU ≥ T1_OVERLAP_IOU (0.5) and is not a nested pair (2.36.7 nesting rule); stop at K_EDIT regions
backfill     = one monotonic cursor over the **entire ranked T1 population** after `keep_T1`, including ranked T1 candidates
               outside the initial `keep_T1` prefix. The cursor considers each candidate at most once across all backfill rounds.
               An overlap-skipped candidate is permanently skipped when the cursor passes it; accepted candidates are never
               reconsidered. The cursor advances on every candidate, and each round takes the next eligible batch at or above
               the score floor. Total edit-planned regions never exceeds `K_T1` and the bounded backfill rounds of 2.38.6.
```

Regions in `send_to_edit` go to `CLASSIFYING_STYLE` and then `PLANNING_EDITS` (2.25).

#### 2.38.6 Backfill loop (bounded)

After `RANKING_SHORTS`, if the number of **distinct source regions** with an eligible Short Candidate (2.39.1) is below `N_SHOW`, `backfill` is non-empty and fewer than `BACKFILL_MAX_ROUNDS` (2) rounds have run, advance the single monotonic backfill cursor over the whole ranked T1 population. Take up to `BACKFILL_BATCH` (3) not-yet-accepted candidates that satisfy the score floor; overlap-skipped candidates are permanently skipped once the cursor passes them, while accepted candidates are removed permanently. Run the chosen batch through style classification, edit planning, verification, hook analysis, reframe planning and Tier 2. The pool grows; existing candidates keep their absolute Tier 2 scores (only candidate-relative features, unused by heuristic v0, are recomputed). The total number of edit-planned regions never exceeds `K_T1`.

#### 2.38.7 Evaluation, calibration and gates

Metrics (dev set, one-to-one loose matching and macro averaging as in 2.36.1, with video-cluster bootstrap intervals):
- `Recall@R_DISC` (all qualified discovered regions), `Recall@keep_T1`, `Recall@send_to_edit`; grade A+B and A only; speech-led and event-led reported separately.
- **Retention ratio** = `Recall@keep_T1 / Recall@R_DISC`.
- **Precision lift** = (share of `send_to_edit` regions that hit an A/B label) ÷ (share of all `R_DISC` regions that hit one).
- Baselines: **B-RS** = the same budgets ordered by `RS` only; **B-rand** = random order, mean of 100 seeds.

| Gate | Condition |
|---|---|
| T1-G1 | Retention ratio ≥ 0.90; report the video-cluster-bootstrap 95% lower bound and require at least `T1_MIN_VIDEOS` (8) dev videos for a gate decision. |
| T1-G2 | Precision lift ≥ 1.3 at `send_to_edit`; report the video-cluster-bootstrap 95% interval and distinct-video count. |
| T1-G3 | Median per-video paired `Recall@send_to_edit` difference against B-RS is ≥ 0 and at least 60% of videos are no worse; otherwise B-RS ordering becomes the default (the simpler variant wins, 2.17). |

**Weight fitting (after labels exist).** Fit a non-negative, L2-regularized logistic regression on the eight features to predict "this region has a loose hit with an A/B label"; leave-one-video-out. Adopt the fitted weights only if held-out average precision beats the hand weights by ≥ 0.03 (the rule of 2.36.5). Version the weights either way.

#### 2.38.8 Artifact `tier1_score_v1`

```json
{ "tier1_id": "uuid", "source_region_id": "uuid", "schema_version": 1, "stage_version": "tier1@1",
  "config_version": "config@1", "config_sha256": "…",
  "study_mode": false, "evaluation_mode": false, "effective_max_compression_ratio": 4.0,
  "weights_version": "t1_weights@1",
  "features": { "t1.hook": {}, "t1.boundary": {}, "t1.completeness": {}, "t1.standalone": {},
                "t1.density": {}, "t1.energy": {}, "t1.duration_fit": {}, "t1.live_air": {} },
  "region_priority_score": 0.0, "coverage": 0.0, "low_evidence": false,
  "rank": 0, "in_keep_T1": true, "queue": "send_to_edit | backfill | dropped", "drop_reason": null }
```

#### 2.38.9 Constants (all initial)

| Constant | Value |
|---|---|
| Tier 1 weights | hook 0.15, boundary 0.20, completeness 0.15, standalone 0.15, density 0.10, energy 0.10, duration_fit 0.10, live_air 0.05 |
| `T1_MIN_SCORE` / `T1_OVERLAP_IOU` | 0.25 / 0.5 |
| `duration_fit` levels | 1.0 / 0.7 / 0.4 / 0 |
| `BACKFILL_BATCH` / `BACKFILL_MAX_ROUNDS` | 3 / 2 |

---

### 2.39 Tier 2 — Short Candidate feature vector and ranker (v5.0 — NORMATIVE)

**Status: NORMATIVE in v5.0.** Owner decisions T4–T8 are resolved in 2.39.13. All numbers remain *initial* and change only through the stated gates/calibration procedures. This is the Tier 2 specification consumed by 2.36.9.1 and 2.37.

#### 2.39.1 Scope, population and eligibility

- **Scope.** Tier 2 ranks **within one source video**. The **pool** = every Short Candidate of that video (one `verified_edit_plan` = one Short Candidate, so a region can contribute up to 3). Nothing is compared across videos.
- **Reference population** for every candidate-relative feature (2.39.5) = all *eligible* Short Candidates of the same source video, before final ranking (one canonical definition; review item R35).
- **Eligibility gate (deterministic, evaluated in this order; the first failure sets `exclusion_reason`; excluded candidates are stored, never deleted):**

| ID | Condition | `exclusion_reason` |
|---|---|---|
| X1 | `final_status ∈ { TRANSCRIPT_VERIFIED_PASS, LAYER1_ONLY_PASS }` | `verification_failed` |
| X2 | not a study-mode plan (2.36.9.9) | `study_mode` |
| X3 | `hook_analysis.analysis_status ≠ failed` (a `partial` or `not_applicable` status is eligible) | `hook_analysis_failed` |
| X4 | `reframe.status ∈ { ok, degraded }` (2.39.3) | `no_usable_vertical` |
| X5 | Tier 2 evidence: `coverage ≥ T2_MIN_COVERAGE` (0.5, 2.39.4) | `insufficient_evidence` |
| X6 | all required feature groups have no `not_run` / `not_available_in_stage` reason | `pipeline_incomplete` |

- **Duration** is a context feature and a hard gate only (2.36.2 rule 5); there is **no monotone "shorter is better" prior** anywhere in Tier 2.

#### 2.39.2 Short Candidate artifact `short_candidate_v1`

```json
{ "short_candidate_id": "uuid", "verified_edit_plan_id": "uuid", "source_region_id": "uuid",
  "source_video_id": "uuid", "schema_version": 1, "stage_version": "short_candidate@1",
  "config_version": "config@1", "config_sha256": "…",
  "plan_origin": "model | user_edit", "parent_short_candidate_id": "uuid | null", "replaces_short_candidate_id": "uuid | null", "export_profile_id": "youtube_shorts", "export_profile_sha256": "…", "comparability_class": "A | B",
  "hook_analysis_id": "uuid", "content_style_id": "uuid", "reframe_plan_id": "uuid", "caption_plan_id": "uuid | null",
  "features": { "<feature_id>": { "v": null, "m": null } },
  "eligible": true, "exclusion_reason": null }
```

`comparability_class`: **A** = `TRANSCRIPT_VERIFIED_PASS`; **B** = `LAYER1_ONLY_PASS` (event-led plans and speech plans below `JUDGE_MIN_WORDS`).

#### 2.39.3 Feature vector

Every feature is `{ "v", "m" }` (2.37.3). Each group records the extractor `stage_version`. "score/5" means the verifier's raw 1–5 integer divided by 5.

| Group | feature_id | Definition (output timeline of the `verified_edit_plan`) |
|---|---|---|
| Duration | `dur.final_s`, `dur.profile` | Final duration in seconds; `0` primary / `1` extended. Context only. |
| Edit | `edit.compression_ratio`, `edit.interval_count`, `edit.cuts_per_10s`, `edit.micro_edit_count` | Final ratio (after micro-edits and audio joins); retained intervals; content cuts per 10 s of output; number of applied pause shortenings. |
| Source Region | `reg.start_score`, `reg.end_score`, `reg.pattern_completeness`, `reg.pattern_id`, `reg.context_dependency`, `reg.single_idea` | From discovery and 2.9. `reg.pattern_completeness` is explicitly a **Source Region proxy**, not a recomputed property of the edited short. The Tier 1 score is **not** a Tier 2 feature by default (it would double-count; ablation `T2-A1`). |
| Hook (2.37.3) | group A: `hook.first_content_ms`, `hook.immediate_content_ratio`, `hook.info_density`, `hook.cue_question`, `hook.cue_number`, `hook.cue_claim_word`, `hook.first_signal_ms`, `hook.audio_onset_in_window`, `hook.motion_in_window`, `hook.cuts_in_window`, `hook.face_ratio_in_window`; group B: `hook.requires_prior_context`; group C: `hook.primary_hook_type`, `hook.curiosity_gap`, `hook.promise_clarity`, `hook.emotional_intensity`, `hook.promise_established_ms` | Exactly as 2.37.3, with their missing reasons. **Which groups are used is decided by H-G4/H-G5** (2.39.4). |
| Coherence (verifier) | `coh.flow`, `coh.reference_resolution`, `coh.setup_payoff`, `coh.ending_completeness`, `coh.opening_standalone`, `coh.min`, `coh.mean`, `coh.issue_count_minor`, `coh.repair_applied`, `coh.judged_band` | From the plan's **final judgment** (repaired plan's judgment if repaired), via the stored raw output. Class B plans: all `not_applicable`. |
| Ending / payoff | `end.end_event_present` | `end_event` of the region's pattern (2.36.6 table). *Payoff presence and quality* are `coh.setup_payoff`; *ending completeness* is `coh.ending_completeness`. There is no separate payoff-timing feature in MVP: the completion unit is forced to be the last one (2.36.8.5), and time-to-core-idea is `hook.promise_established_ms`. |
| Speech | `speech.wpm`, `speech.pause_ratio`, `speech.density_full` | Words per output minute; share of output time that is silent (RMS ≤ `local_nonspeech_rms_v1(t)`) and has no word; content words per output second, `min(1, x / DENSITY_NORM)`. `not_applicable` for event-led plans with no text. |
| Audio | `audio.peak_rate`, `audio.rms_std_db` | Audio peaks (2.36.4 definition) per output minute; standard deviation of short-term loudness. |
| Visual | `vis.face_ratio`, `vis.motion_mean_z`, `vis.motion_peak_rate`, `vis.cuts_per_min`, `vis.screen_ratio` | Share of retained samples (at `FACE_SAMPLE_FPS`) with a face; mean motion over retained intervals as a robust z against the video, clipped to [−3, 6]; motion peaks per output minute; source shot cuts inside retained intervals per output minute; share with screen content. |
| Reframe | `reframe.status`, `reframe.crop_confidence` | From the reframe plan (below). |
| Context | `ctx.content_style`, `ctx.visual_format`, `ctx.final_visual_format`, `ctx.region_kind`, `ctx.comparability_class` | Categorical, from the style artifact and the plan. `final_visual_format` is computed from the verified retained timeline and feeds the reframer. Not scoring terms in heuristic v0. |
| Relative | `rel.<term>` | 2.39.5. |

**Event-led / class-B feature subset (explicit).** For event-led plans the following are present: `dur.*`, `edit.*`, `reg.start_score`, `reg.end_score`, `reg.pattern_completeness`, `reg.pattern_id`, hook group A signals that need no text (`hook.audio_onset_in_window`, `hook.motion_in_window`, `hook.cuts_in_window`, `hook.face_ratio_in_window`, `hook.first_audio_event_ms`, `hook.first_motion_ms`, `hook.first_signal_ms`), `audio.*`, `vis.*`, `reframe.*`, `ctx.*`. These are `not_applicable`: `coh.*`, hook groups B and C, `hook.first_content_ms`, `hook.immediate_content_ratio`, `hook.info_density`, the text cues, `speech.*`, `reg.context_dependency`. Speech-led plans below `JUDGE_MIN_WORDS` (class B) lose only `coh.*` and hook group B.

**Reframe input contract (v5.0).** `PLANNING_REFRAME` writes an immutable `reframe_plan_v1` per verified plan. Input is the verified retained timeline plus `final_visual_format` and final retained face/screen rates. The strategy is chosen from that **final** visual state. `status = ok` iff the strategy is one of `fixed_center | face_aware | multi_speaker` and `crop_confidence ≥ REFRAME_CONF_MIN`; `degraded` if the fallback `blurred_background` is used or confidence is lower; `infeasible` if no composition keeps the important content.

```json
{
  "reframe_plan_id": "uuid",
  "reframe_lineage_id": "uuid",
  "parent_reframe_plan_id": "uuid | null",
  "verified_edit_plan_id": "uuid",
  "content_unchanged": true,
  "schema_version": 1,
  "stage_version": "reframe_plan@1",
  "config_version": "config@1",
  "config_sha256": "…",
  "final_visual_format": "talking_head | screen_capture | mixed | other_visual",
  "strategy": "fixed_center | face_aware | multi_speaker | blurred_background",
  "status": "ok | degraded | infeasible",
  "crop_confidence": 0.0,
  "reasons": []
}
```

#### 2.39.4 Heuristic ranker v0

Used until a learned ranker passes its gates (Phase 5). Deterministic, CPU-only.

```text
coherence_term    = 0.5·coh.min + 0.5·coh.mean                              absent for class B (coh.* are already score/5 in [0,1])
hook_term         = mean over the ENABLED hook groups g of term_g               absent if no group is enabled
   term_A = mean of the available items:
            hook.immediate_content_ratio ; 1 − min(1, hook.first_content_ms / 3000) ;
            max(cue_question, cue_number, cue_claim_word) ; hook.audio_onset_in_window ;
            clip(hook.motion_in_window, 0, 3) / 3
   term_B = 1.0 if hook.requires_prior_context = false, else 0.0 (present only when group B is enabled and the verifier produced `requires_prior_context`)
   term_C = mean( hook.curiosity_gap / 5 , hook.promise_clarity / 5 )
completeness_term = reg.pattern_completeness  # source-region proxy only; edited-short completeness is captured by verifier coherence where applicable
density_term      = speech.density_full                                         absent if not applicable
pacing_term       = 0.5·wpm_fit + 0.5·(1 − min(1, speech.pause_ratio / PAUSE_RATIO_REF))
   wpm_fit = 1 − min(1, | speech.wpm − WPM_TARGET | / WPM_TOL)                  absent if not applicable
energy_term       = mean( norm(audio.peak_rate, NORM_PEAK_RATE), norm(vis.motion_peak_rate, NORM_PEAK_RATE) )
visual_term       = mean of available { vis.face_ratio ; clip(vis.motion_mean_z, 0, 3) / 3 }
edit_term         = 1 − 0.5·clip( (edit.compression_ratio − 1) / (effective_max_compression_ratio − 1), 0, 1 )
                      − 0.25·clip( edit.cuts_per_10s / 2, 0, 1 )
reframe_term      = 1.0 if reframe.status = ok ; 0.6 if degraded

weights (initial): coherence 0.20, hook 0.20, completeness 0.10, density 0.10, pacing 0.10,
                   energy 0.10, visual 0.05, edit 0.10, reframe 0.05                (sum = 1.00)

final_rank_score = Σ_{t present} w_t · t / Σ_{t applicable} w_t       (rounded to 4 decimals)
applicable_weight = Σ_{t applicable} w_t
present_weight    = Σ_{t present} w_t
failed_weight     = Σ_{t applicable and extraction_failed/invalid_output} w_t
coverage          = present_weight / applicable_weight if applicable_weight > 0 else 0
X5                = coverage ≥ T2_MIN_COVERAGE (0.5)

`not_applicable` features are excluded from both numerator and denominator. A feature is **applicable** only when its group is enabled by configuration, supported by the candidate's class/region kind, and the required stage executed for that feature. A disabled hook group is therefore not applicable. A designed N/A feature does not reduce evidence coverage. Extraction failures/invalid outputs remain **applicable**: they reduce coverage, add to `failed_weight`, and set `degraded_features = true`. `no_detection` is present negative evidence, not missingness.
```

**Missingness policy (v0 and learned).** Per missing reason:

| `m` | Heuristic v0 | Learned ranker |
|---|---|---|
| `no_detection` | Counts as the informative negative (`0` / `false`). | Native value plus indicator. |
| `not_applicable` | The item is skipped from both term and coverage denominator; a term with no applicable items is absent. | Native missing plus one-hot of `m`. |
| `extraction_failed`, `invalid_output` | The feature remains in the **applicable denominator**, contributes zero to `present_weight`, contributes its weight to `failed_weight`, and the candidate is flagged `degraded_features = true` (shown in the UI). It is not equivalent to N/A. | Missing indicator + failed flag; retain it in the applicability mask so training/evaluation can distinguish failure from designed absence. |
| `not_run`, `not_available_in_stage` | Must not occur at Tier 2 → X6 excludes the candidate. | Same. |

**Hook policy (T5).** `hook.context_independence` remains stored for provenance/review but is not a separate Tier 2 hook feature; group B uses the boolean `requires_prior_context` instead, so the same numeric verifier signal is not double-counted. `HOOK_GROUPS_ENABLED` is empty by default. The adoption units are `{A+B}` followed by `{C}`; there is no separate adoption decision for A versus B. A unit is added only after it passes H-G4 (2.37.7) and H-G5 (2.39.9). While no group is enabled the hook term is absent. `hook_lexical@1` is **not** a fallback (H2). If the owner prefers a fallback, that is a separate decision.

**Not used by v0:** duration (context only), `content_style`, trend features (2.22, experimental flag `TREND_FEATURES_ENABLED = false`), candidate-relative features (2.39.5, computed and stored for explanation and for the learned ranker), Tier 1 score.

**Tie-break (deterministic):** `(final_rank_score descending, coverage descending, coh.min descending with absent last, source start ms ascending, verified_edit_plan_id ascending)`.

#### 2.39.5 Candidate-relative features

For a term `t` in {coherence, hook, density, pacing, energy, visual}: over **all eligible Short Candidates from the same source video before per-region best-plan selection and before display MMR** (2.39.1) for which `t` is present, `rel.t = clip( (t − median) / max(1.4826·MAD, REL_MAD_FLOOR), −3, 3 )`. The feature is `null` with `m = not_applicable` if the population has fewer than `REL_MIN_POP` (8) candidates with that term, or the candidate's own term is absent. Relative features are supplementary signals (2.31): they never replace the absolute values, and a uniform video may still score uniformly low.

#### 2.39.6 Comparability classes and unjudged plans (review item R34)

- **Class A** (`TRANSCRIPT_VERIFIED_PASS`) and **class B** (`LAYER1_ONLY_PASS`, badge "not semantically validated") are ranked **within their own class**. No arbitrary penalty is invented for class B.
- `CROSS_CLASS_MERGE_ENABLED = false` by default. It may be enabled only when gate T2-G3 passes.
- **Same-region rule (the verifier's interim rule, now final):** for one source region, a class-A plan is preferred over a class-B plan regardless of score.
- **Slot allocation while merging is disabled** (the display has two sections, class A first):

```text
n_A, n_B      = number of regions with a best plan in class A / B (after 2.39.8 step 1)
slots_B0      = 0 if n_B = 0 else max(1, round( N_SHOW · n_B / (n_A + n_B) ))
slots_A       = min( n_A , N_SHOW − slots_B0 )
slots_B       = min( n_B , N_SHOW − slots_A )
```

#### 2.39.7 Determinism

Same artifacts, same versions and same configuration produce byte-identical scores, ranks and display order. No randomness, no wall-clock dependence, no LLM call in Tier 2.

#### 2.39.8 Display selection (separate from the score order; review item R36)

```text
1. Per region: keep the best plan (class A over class B, then final_rank_score, then the tie-break). The other plans
   are stored as alternates and stay reachable through "simpler edit" (2.26).
2. Within each class, maximal marginal relevance with λ = MMR_LAMBDA (0.7):
      pick  argmax_c [ λ · final_rank_score(c)  −  (1 − λ) · max_{s ∈ selected} sim(c, s) ]
      sim(c, s) = retained_source_overlap(c, s) / min(retained_source_duration(c), retained_source_duration(s))
      where both numerator and denominator use unions of the candidates' retained source intervals, producing [0,1]
      a candidate with sim > DISPLAY_MAX_OVERLAP (0.30) to any selected one is ineligible (hard exclusion)
      ties: the 2.39.4 tie-break; stop at the class's slot count (2.39.6)
3. Output: `display_rank` (position shown) and `score_rank` (position in the class's score-ordered pool). Both are logged (2.18). Persist an immutable `display_selection_v1` artifact containing the selected candidate IDs, class/slot allocation, MMR parameters, retained-overlap values, exclusion reasons, both rank orders, and the common artifact identity fields `config_version` / `config_sha256` (plus `study_mode` / `evaluation_mode` when applicable) so UI ordering is auditable and reproducible.
```

`final_rank_score` order and display order are different objects: only the first is model output.

`display_selection_v1` is an immutable decision artifact: `schema_version`, `stage_version`, `config_version`, `config_sha256`, ordered selected candidate IDs, class/slot allocation, `MMR_LAMBDA`, `DISPLAY_MAX_OVERLAP`, retained source-interval overlaps for every exclusion/selection comparison, exclusion reasons, `score_rank` and `display_rank` are persisted exactly as used by the displayed list. Re-running from the same input artifacts and config must reproduce the same selection byte-for-byte.


#### 2.39.9 Learned ranker boundary and gate H-G5

- **Learned ranker (Phase 5):** gradient-boosted trees with a pairwise ranking objective on the 2.39.3 vector (including `rel.*` and missingness indicators), trained only from the **400 same-class base Task 4 pair pool** plus later first-party same-class preference data. The 400-pair **dev** pool is split into group-by-video training/validation folds; the 160-pair sealed pool is held out for final confirmation only; a video must not appear in both the training and held-out evaluation fold for a learned-ranker measurement. H-G5 remains the separate heuristic-vs-hook gate defined below. The separate cross-class evaluation pairs never enter training or weight fitting.
- **H-G5 protocol (the protocol 2.37.7 referred to):** the **dev adoption run** uses the 400 same-video, same-class dev Task 4 pairs with the sampling constraints of 2.36.1; the same computation is repeated once on the 160-pair sealed pool only for confirmation; the separate cross-class evaluation set is excluded. `M0` = heuristic v0 with the hook term absent; `Mg` = `M0` plus the hook group(s) `g` enabled. Metric = pairwise accuracy (a tie counts 0.5). `Δ = acc(Mg) − acc(M0)`. Bootstrap over **videos** (`BOOTSTRAP_B` = 2000, same folds for both). A group is adopted iff `Δ ≥ 0` (point estimate) **and** the 95% lower bound of `Δ` is ≥ `−H5_MARGIN` (0.03). *This is a non-degradation check:* the 400-pair base study is sized for a stronger empirical comparison, but this gate still tests non-degradation rather than claiming proof of improvement. Any future increase in pair count is a versioned study change.

#### 2.39.10 Gates

**Ablation `T2-A1` (Tier-1-score feature).** Owner: ranking owner. Before any experiment or production proposal that adds the Tier 1 `region_priority_score` to the Tier 2 vector, compare v0 with and without that feature on the dev Task 4 pool using the same video-cluster bootstrap protocol. Adoption requires a non-negative point-estimate accuracy change and a 95% lower bound ≥ `−H5_MARGIN`; the sealed pool confirms once. The feature remains excluded by default until this ablation passes. Owner: ranking owner; decision artifact: `tier2_ablation_t2_a1_v1`; any adoption requires a config/version bump and the same sealed confirmation rule as T2-G2.

| Gate | Condition |
|---|---|
| T2-G1 | Unit tests: determinism (2.39.7), each row of the missingness table, tie-break order, per-region best-plan rule (class A preferred), slot allocation, MMR hard exclusion. 100% pass. |
| T2-G2 | Dev: heuristic v0 vs baselines on the 400 same-class **dev** Task 4 pairs; v0 must beat B1 with video-cluster-bootstrap lower bound > 0. B2 remains class-A-only. If v0 fails, revise weights only on dev data by explicit owner decision. Then run one **sealed confirmation** on `T4_SEALED_PAIRS`; no weight, threshold or feature decision may use sealed results. Report pair count, distinct videos, max pair share and cross-region share separately for dev and sealed pools. |
| T2-G3 | **Separate cross-class evaluation set only:** at least 40 cross-class pairs across at least 8 videos; accuracy ≥ 0.60 with video-cluster-bootstrap lower bound ≥ 0.50. These pairs are never used to train or tune the ranker. Only then may `CROSS_CLASS_MERGE_ENABLED` be set to true. |
| T2-G4 | Exclusion audit on the dev set: at most 10% of candidates excluded by X3–X6; reasons reported per class. |
| T2-G5 | Scoring p95 runtime under 0.1 s per candidate on CPU. |
| H-G5 | Run on the dev Task 4 pool for adoption/tuning and repeat once on the sealed Task 4 pool for confirmation; sealed results never trigger tuning. |

#### 2.39.11 Artifact `tier2_score_v1`

```json
{ "tier2_id": "uuid", "short_candidate_id": "uuid", "schema_version": 1, "stage_version": "tier2_heuristic@1",
  "config_version": "config@1", "config_sha256": "…", "export_profile_id": "youtube_shorts", "export_profile_sha256": "…",
  "weights_version": "t2_weights@1", "hook_groups_enabled": [],
  "terms": { "coherence": null, "hook": null, "completeness": null, "density": null, "pacing": null,
             "energy": null, "visual": null, "edit": null, "reframe": null },
  "applicable_weight": 0.0, "present_weight": 0.0, "failed_weight": 0.0, "coverage": 0.0, "degraded_features": false,
  "final_rank_score": 0.0, "comparability_class": "A | B",
  "score_rank": 0, "display_rank": null, "shown": false, "alternate_of": null,
  "exclusion_reason": null }
```

#### 2.39.12 Constants (all initial)

| Constant | Value |
|---|---|
| Tier 2 weights | coherence 0.20, hook 0.20, completeness 0.10, density 0.10, pacing 0.10, energy 0.10, visual 0.05, edit 0.10, reframe 0.05 |
| `T2_MIN_COVERAGE` | 0.5 |
| `WPM_TARGET` / `WPM_TOL` / `PAUSE_RATIO_REF` | 150 / 75 / 0.25 |
| `REL_MIN_POP` / `REL_MAD_FLOOR` | 8 / 0.05 |
| `MMR_LAMBDA` / `DISPLAY_MAX_OVERLAP` | 0.7 / 0.30 |
| `REFRAME_CONF_MIN` / degraded factor | 0.6 / 0.6 |
| `T4_BASE_PAIRS` / `T4_SEALED_PAIRS` / `T4_MAX_VIDEO_SHARE` | 400 / 160 / 0.10 |
| `T4_MIN_CROSS_REGION_SHARE` / `T4_CROSS_CLASS_PAIRS` / `T4_CROSS_CLASS_MIN_VIDEOS` | 0.50 / 40 / 8 |
| `T4_SAMPLING_SEED` | fixed, versioned integer |
| `H5_MARGIN` | 0.03 |
| `HOOK_GROUPS_ENABLED` / `CROSS_CLASS_MERGE_ENABLED` / `TREND_FEATURES_ENABLED` | [] / false / false |

#### 2.39.13 Owner decisions (RESOLVED in v4.9)

| # | Decision | Resolution |
|---|---|---|
| T1 | Tier 1 feature vector, weights, absolute normalization, `T1_MIN_SCORE` (2.38.2–2.38.3) | **AGREED:** confirm as written; all initial values are versioned/calibrated through T1-G1…T1-G3. |
| T2 | Budget interplay: `keep_T1` / `send_to_edit` / `backfill`, overlap rule, bounded backfill loop (2.38.4–2.38.6) | **AGREED:** use the ranked cursor/backfill contract as written; no total edit-planning count may exceed `K_T1`. |
| T3 | `content_style_v1` contract (2.37.5.1) | **AGREED:** use the contract as written, including deterministic truncation and conservative fallback to `other`. |
| T4 | Tier 2 scope, eligibility gate X1–X6, feature vector, reframe input contract (2.39.1–2.39.3) | **AGREED:** use the contract as written, including applicable-weight coverage and `final_visual_format`. |
| T5 | Tier 2 hook term policy | **AGREED:** only H-G4/H-G5-adopted groups may enter the hook term; no `hook_lexical@1` fallback. |
| T6 | Missingness, comparability classes, no class-B penalty, slot allocation, merge gate (2.39.4, 2.39.6) | **AGREED:** N/A is excluded from coverage; class A/B rank separately; cross-class merge is disabled until T2-G3. |
| T7 | Heuristic v0 terms, weights and tie-break (2.39.4) | **AGREED:** documented starting weights; changes require T2-G2 owner decision and version bump. |
| T8 | Display selection and H-G5 protocol (2.39.8–2.39.9) | **AGREED:** retained-interval MMR and 400-pair Task 4 base study; same-class H-G5 is a non-degradation test. |

---

## Part 3 — Step-by-step build plan

### Phase 0 — Foundations and evaluation harness
- [ ] Lock English-only MVP scope and enforce the language gate during normalization.
- [ ] Select exactly one `export_profile_id` per job and persist its immutable profile/hash.
- [ ] Register one immutable content-addressed config snapshot (`config_version` + `config_sha256`).
- [ ] Implement the shared helpers `robust_z_v1`, `event_safe_cut_v1`, `earliest_safe_after`, `latest_safe_before`, `local_nonspeech_rms_v1`, `d_clean_v1` and `super_unit_embedding_v1` with unit tests.
- [ ] Implement `sentence_seg_v1`, mandatory forced alignment, `TextTiling_depth_v1`, deterministic embedding persistence and the explicit no-diarization fallback (2.14.1).
- [ ] Define machine-checkable JSON Schemas for the normative artifacts (including `caption_plan_v1`, `reframe_plan_v1`, `verified_edit_plan`, `tier1_score_v1`, `tier2_score_v1`).
- [ ] Define Source Region / Edit Plan / Short Candidate / Rendered Short schemas.
- [ ] Build an evaluation dataset spanning multiple structural video types.
- [ ] Implement fixed-window + sentence-boundary baseline.
- [ ] Implement uniform/fixed-weight boundary baseline.
- [ ] Define Region Recall@K, boundary error, redundancy, and compute-budget metrics with **one-to-one maximum matching**, macro averaging and **video-cluster bootstrap** intervals (2.36.1).
- [ ] Split the dataset **stratified by structural type** and by creator (2.36.1); plan Task 3 sampling stratified by compression band × type.
- [ ] Set up object storage with presigned uploads.
- [ ] Set up resumable background job orchestration.
- [ ] Define artifact versioning and stage contracts.
- [ ] Run a thin vertical slice: one video through normalize → ASR/alignment → regions → one verified plan → reframe/captions → render before scaling the full evaluation dataset.
- [ ] Complete legal/retention/terms review before public launch.

### Phase 1 — Adaptive candidate-discovery MVP
- [ ] Upload → normalize → ASR → language gate → mandatory forced alignment for transcript-bearing jobs → cheap audio/CV/scene analysis.
- [ ] Global + local Structural Profile with the deterministic segmentation and routing (2.36.4).
- [ ] Boundary map and boundary scores (2.36.5).
- [ ] Region discovery Steps 1–3 with the exact cohesion function, the single-idea rule and the event settle semantics (2.36.6).
- [ ] Qualification QC-1…QC-6 and `context_dependency` (2.9); run gate Q-G1.
- [ ] RS scoring, dedup and the `R_DISC` budget (2.36.6 Steps 5–6, 2.36.7).
- [ ] Compare adaptive discovery against both required baselines with the one-to-one metrics (2.17, 2.36.1); run gates G3 and G4.
- [ ] Tier 1 prioritizer, budgets and backfill queue (2.38); run T1-G1…T1-G3.
- [ ] Do not proceed to expensive edit planning if adaptive discovery does not earn its complexity.

### Phase 2 — Style, constrained edit planning, verification, hooks, Tier 2

Implementation order (each step's gates must pass before the next step is signed off):

- [ ] **Content-style classifier** `content_style_v1` and the `visual_format` rule (2.37.5, 2.37.5.1); run S-G1. It runs *before* edit planning (state `CLASSIFYING_STYLE`).
- [ ] Edit-unit construction for speech-led regions: sentence units, run-on guard, glue groups G1–G2 (G0 retired), super-units (2.36.8.2).
- [ ] Trim-only editing for event-led regions (2.36.8.3).
- [ ] Unit value function (bounded terms, versioned vocabularies), forced opening/completion units, DP with the explicit base state (2.36.8.4–2.36.8.6).
- [ ] Edit intensities with the single build order, plan dedup, pause-shortening micro-edits with the budgeted application, recompute of final band/profile, Edit Plan schema v1 with `cut_id`s (2.36.8.7–2.36.8.9).
- [ ] Pass the E-gates (2.36.8.11) before implementing the verifier.
- [ ] Layer 1 in the specified order: checks, audio joins, timeline recompute, duration/compression, event checks (2.36.9.2).
- [ ] Judge: prompt `verifier_prompt@2` (viewer-only), schema validation, semantic cross-field validation, issue normalization by `cut_id`, input hashing, and transport-error taxonomy (2.36.9.3).
- [ ] Verdict function with `repair_feasible`, compression bands, judge-call budget (2.36.9.4–2.36.9.5).
- [ ] Stage R with `plan_repair`, stable `cut_id` targets, bridge test (2.36.9.6).
- [ ] Write the `verified_edit_plan` artifact (2.36.9.8a); every later stage reads only it.
- [ ] Study mode, the Task 3 label set (stratified), and gates V-G1 to V-G5 with cluster-bootstrap statistics (2.36.9.9).
- [ ] Hook analyzer: deterministic signals with the corrected anchors, verifier-feature reuse, LLM call, `validate_hook_semantics@1`, conversion contract, canonical cache keys, `no_detection` missingness, transport-error taxonomy and cost report (2.37.1–2.37.6). Run H-G1 to H-G4 (2.37.7).
- [ ] Reframe planning and `reframe_plan_v1` with deterministic crop strategy/confidence (2.24, 2.39.3).
- [ ] Caption planning `caption_plan_v1` from verified output-timeline word timings, with safe-zone/line-length rules (2.24).
- [ ] Define and test render-profile loudness normalization and true-peak enforcement (2.24), plus caption/reframe artifact conformance.
- [ ] Short Candidate features (2.39.3) and the Tier 2 heuristic ranker v0 (2.39.4–2.39.7); run T2-G1, T2-G2, T2-G4, T2-G5; H-G5 with the Task 4 pairs.
- [ ] Display selection (2.39.8) and comparability classes (2.39.6); run T2-G3 if class-B candidates exist. Verify candidate-level lifecycle transitions and immutable selection revisions.
- [ ] Build the review UI, including the user-edit lifecycle (2.26.1), and capture accept/reject/trim actions with `plan_origin`.

### Phase 3 — Rendering and publication/performance loop
- [ ] Render vertical shorts with captions and safe audio transitions.
- [ ] Store immutable rendered artifacts.
- [ ] Add optional YouTube connection using OAuth.
- [ ] Collect authorized Analytics metrics where available.
- [ ] Collect public statistics for published videos where appropriate.
- [ ] Normalize outcome labels by platform/account/video age and record exposure context.
- [ ] Build first-party preference + performance dataset.

### Phase 4 — Trend experiment
- [ ] Build metadata-only YouTube trend index.
- [ ] Add retrieval features behind a feature flag.
- [ ] Run no-trend vs trend ablation.
- [ ] Keep trends disabled by default if the measured improvement is weak or unstable.

### Phase 5 — Learned ranking
- [ ] Train a ranker only after enough first-party preference/performance data exists.
- [ ] Split by creator/source video and respect temporal ordering.
- [ ] Compare against heuristic baseline.
- [ ] Evaluate calibration, ranking metrics, subgroup/format performance, and drift.
- [ ] Add controlled exploration to reduce selection bias when enough traffic exists.

### Phase 6 — Scale and optional generation
- [ ] Move expensive inference to serverless GPU where justified by measured workload.
- [ ] Add caching and artifact reuse.
- [ ] Scale vector infrastructure only if the trend experiment proves useful.
- [ ] Add optional LLM title/caption generation after core extraction/ranking works.
- [ ] Consider fine-tuning only after prompting/general models fail a measured requirement.

---

## Part 4 — Component reference

| Component | Starting choice | Purpose | MVP status |
|---|---|---|---|
| Video normalization | ffmpeg | Canonical media format | Required |
| ASR | Whisper-class ASR + `forced_alignment_v1` | Transcript + word timestamps | Required; forced alignment is mandatory for MVP |
| Diarization | Lightweight diarization model | Speaker turns | Optional; speaker-dependent features become null when unavailable (2.14.1) |
| Shot/scene detection | PySceneDetect or equivalent | Visual boundaries | Required |
| Audio analysis | FFmpeg/librosa-style signal features | Pauses/energy/events | Required |
| Face/motion analysis | MediaPipe/OpenCV + optical flow | Visual signals | Required |
| Semantic analysis (LLM) | Structured LLM on bounded inputs | Verifier judge (2.36.9), hook analysis (2.37), content-style classification (2.37.5.1). **Not** used in discovery, qualification, Tier 1 or Tier 2. | Required, bounded |
| Embeddings | Low-cost embedding model | Sentence embeddings for topic/semantic boundaries and continuity (2.36.5); trend retrieval features | Required (boundaries) / Experimental (trends) |
| Trend store | pgvector/Postgres | Metadata trend retrieval | Experimental |
| Region prioritizer | Deterministic weighted features (2.38) | Tier 1 | Required |
| Final ranker | Heuristic v0 (2.39); learned model later | Tier 2 | Required |
| Edit verifier | Rule-based + structured semantic checks | Coherence validation | Required |
| Renderer | ffmpeg | Final 9:16 output | Required |
| Reframer | Deterministic face/screen-aware crop pipeline with `reframe_plan_v1` | Vertical composition | Required |
| Caption planner | `caption_plan_v1` on verified output-timeline timings | Timed captions | Required |
| Queue/orchestration | Redis/Celery or managed equivalent | Resumable stages | Required |
| Object storage | R2/S3 | Media/artifacts | Required |

Vendor-specific prices, quotas, and model-quality claims are intentionally kept out of normative architecture. Re-verify them immediately before implementation.

---

## Part 5 — Cost model

Cost must be measured empirically after the first pipeline exists.

Track per source-video minute:

- ASR cost;
- semantic LLM cost;
- embeddings cost;
- CV/VLM cost;
- CPU/GPU runtime;
- storage;
- egress;
- rendering;
- database/queue overhead.

The planning spreadsheet/budget should use current vendor pricing at the time of deployment. Do not rely on historical prices embedded in this document.

---

## Part 6 — Key risks

- **Candidate recall:** the biggest technical risk; a ranking model cannot recover a strong idea that discovery never proposes.
- **Over-compression:** aggressive editing can destroy coherence.
- **Selection bias:** training only on user-selected/high-ranked clips can reinforce the current system.
- **Platform drift:** duration rules, metrics, and recommendation behavior change.
- **Trend data access:** official APIs may not expose the data needed for transcript/audio-based trend analysis.
- **Processing cost:** long videos multiply ASR/CV/LLM/rendering cost.
- **Rendering quality:** a strong landscape source can become unusable after a naive vertical crop.
- **Legal/privacy:** uploaded copyrighted media, deletion/retention, third-party processing, and identity-linked features require explicit policy and legal review.
- **Model nondeterminism:** GPU/LLM components require versioning and tolerance-based evaluation.

---

## Part 7 — Product thesis

The product is not positioned as a generic "find viral clips" button.

Its core technical thesis is:

> **Understand the structure of the source video, discover complete ideas/events rather than arbitrary windows, construct a constrained coherent short, and rank the resulting shorts using multimodal evidence.**

Success should be measured empirically against simpler extraction baselines and existing workflows rather than assumed from the architecture.

---

## Appendix A — Earlier Feature Taxonomy Reference

The following taxonomy is retained as a reference during implementation. The normative stage ownership and constraints in Part 2 take precedence when terminology or stage placement differs.


**Status:** Working proposal — this taxonomy is the current design under discussion. It is not yet locked until reviewed together.

The system should not treat "virality" as one directly observable property. Each candidate clip will be represented by a structured feature vector spanning content, audio, visual, structure, trend/context, and later outcome signals.

### 1. Content / Semantic Features

These describe what the candidate is communicating.

| Feature group | Candidate features | Why it matters |
|---|---|---|
| Hook | hook strength, hook type, time-to-hook (specified in 2.37) | Determines whether the opening creates immediate interest |
| Curiosity | unanswered question, information gap, curiosity intensity | Gives the viewer a reason to continue |
| Value | informational value, practical usefulness, insight density | Measures whether the viewer gets something from watching |
| Surprise | unexpected claim, reversal, contradiction, novelty | Potential attention/retention signal |
| Emotion | emotional intensity, emotion type, emotional change | Strong emotional moments can increase engagement |
| Story | setup, development, payoff, narrative completeness | A self-contained mini-story is easier to consume |
| Payoff | payoff strength, payoff clarity, payoff timing | The clip should reward the attention it asks for |
| Standalone comprehension | context dependency, ambiguity, missing references | A short should make sense without the full video |
| Topic | topic/category, entities, semantic embedding | Enables topic analysis and trend matching |
| Claim quality | specificity, concreteness, strength of claim | More concrete claims are easier to understand and react to |

**Important:** semantic features should be extracted from the transcript and surrounding context. An LLM may help produce structured semantic features, but it should not directly decide the final virality score.

### 2. Audio / Speech Features

These describe how the clip sounds.

| Feature group | Candidate features | Why it matters |
|---|---|---|
| Speech pace | words/minute, syllables/minute | Very slow or very fast speech may affect retention |
| Pauses | total silence, longest pause, pause frequency | Useful for pacing and identifying dead sections |
| Energy | RMS/loudness, energy variation, peaks | Captures changes in intensity |
| Prosody | pitch variation, speaking-energy variation | Adds information beyond transcript text |
| Speaker dynamics | speaker count, speaker changes, turn frequency | Conversations/interviews often depend on interaction |
| Non-speech events | laughter, applause, music, sound effects | Can indicate emotionally salient moments |
| Audio quality | clipping, noise, speech/music balance | Poor quality can reduce usability |

For MVP, we should start with the inexpensive/robust signals and avoid building a complex emotion classifier before proving that audio features help.

### 3. Visual / Computer Vision Features

These describe what is happening on screen.

| Feature group | Candidate features | Why it matters |
|---|---|---|
| Face presence | face count, face area, face visibility | Human presence is a major visual signal for many formats |
| Facial dynamics | expression change, gaze direction, facial movement | Detects visually expressive moments |
| Motion | optical flow, motion magnitude, motion change | Captures visually dynamic moments |
| Camera | camera movement, zoom, framing change | Measures visual pacing |
| Scene | scene/shot changes, scene duration | Helps characterize visual rhythm |
| Objects | salient objects, object changes | Useful for non-talking-head content |
| On-screen text | OCR text amount, text changes, emphasis | Captures captions, memes, screenshots, titles |
| Composition | subject size, position, clutter | Helps assess visual readability |
| Visual novelty | change from surrounding frames | Detects visually distinct moments |

These features are particularly important for the project's computer-vision objective. The goal is to use CV as an actual feature-extraction layer, not simply call a multimodal LLM on the whole video.

### 4. Structural / Editing Features

These describe how the candidate is constructed.

| Feature group | Candidate features | Why it matters |
|---|---|---|
| Duration | total duration | Short-form performance can depend strongly on length |
| Opening | first 1s/2s/3s strength | The opening is especially important for retention |
| Pacing | cuts/minute, scene duration variance | Captures editing rhythm |
| Density | words/second, semantic events/minute | Measures how much happens in the clip |
| Context dependency | required context before start | Penalizes clips that begin mid-thought |
| Ending | conclusion quality, abruptness | Affects satisfaction and shareability |
| Loopability | ending-to-opening compatibility | Potentially useful for replay behavior |
| Boundary quality | start/end sentence completeness | Prevents awkward clipping |
| Captionability | whether speech/text can be cleanly captioned | Product quality consideration |

### 5. Trend / Context Features

These describe how the candidate relates to currently relevant content.

| Feature group | Candidate features | Why it matters |
|---|---|---|
| Topic similarity | embedding similarity to recent trending content | Measures topical relevance |
| Phrase similarity | similarity to recurring phrases/hooks | Can capture emerging formats |
| Similar-content performance | engagement statistics of retrieved neighbors | Adds empirical context |
| Trend age | age of matching trend items | Prevents stale trends dominating |
| Topic momentum | change in recent engagement | Potential signal of growing/declining interest |

Trend retrieval is a feature source, not the final decision-maker. The trend index should be continuously refreshed rather than re-fed into an LLM for every request.

### 6. Candidate-relative Features

These are important because the product ranks clips **within a video**.

| Feature | Meaning |
|---|---|
| Relative hook rank | How strong the hook is compared with other candidates from the same video |
| Relative emotion | Emotional intensity compared with the video's baseline |
| Relative pacing | Whether the candidate is unusually fast/slow for that speaker/video |
| Relative visual activity | Visual activity compared with the surrounding video |
| Relative semantic density | Information density compared with the source video |
| Local novelty | How different the candidate is from nearby content |

These features help prevent the model from treating every video with the same baseline. A naturally calm interview should not automatically lose to a high-energy vlog simply because its absolute audio energy is lower.

### 7. Quality / Safety / Usability Features

These should be treated separately from "virality."

| Feature group | Candidate features |
|---|---|
| Technical quality | resolution, frame quality, audio quality |
| Caption quality | transcript confidence, caption readability |
| Content suitability | configurable policy/safety filters |
| Copyright/platform concerns | metadata or workflow flags where applicable |
| Generation quality | whether the final crop/render is usable |

A clip can have strong engagement characteristics while still being unsuitable for publication. Product suitability should therefore not be collapsed into the virality score.

### 8. Outcome Features — Training Data Later

These are **not available at initial prediction time**. They become labels after users publish clips and provide/authorize performance data.

Potential outcomes include:

- views
- likes
- comments
- shares
- saves, where available
- watch time
- average watch duration
- completion rate
- follower/subscriber conversion, where available
- performance normalized by account size
- performance measured at fixed ages (for example 1h, 24h, 7d)

We should avoid training directly on raw views when possible. Account size, platform, clip age, posting time, and other exposure variables need to be considered.

---

## Part 2B — Feature Architecture Principle (SUPERSEDED — historical)

> **SUPERSEDED (v4):** see 2.2 and 2.15. Kept because the principle "feature extraction ≠ ranking" still holds.

The feature taxonomy should map to a modular pipeline:

```text
Video
  |
  +--> ASR / transcript --------------------+
  |                                         |
  +--> audio analysis ----------------------+
  |                                         |
  +--> CV / visual analysis ----------------+--> Candidate Feature Vector
  |                                         |
  +--> scene + structural analysis ----------+
  |                                         |
  +--> LLM semantic analysis ---------------+
  |                                         |
  +--> trend retrieval / embeddings --------+
                                            |
                                            v
                                      Ranking Model
                                            |
                                            v
                                      Ranked Clips
```

The important architectural boundary is:

**Feature extraction != ranking.**

Each subsystem should produce structured, versioned features. The ranking layer consumes those features. This allows individual models to be replaced without redesigning the entire system.

---

## Part 2C — Current Decisions (SUPERSEDED — historical)

> **SUPERSEDED (v4):** the current decisions are in 2.34.

1. The product should rank candidate clips rather than claim to predict guaranteed virality.
2. The first implementation should use a heuristic ranker before training a learned ranking model.
3. The core system should be multimodal: speech/text + audio + computer vision + structural signals.
4. An LLM should primarily provide structured semantic analysis/generation, not act as the final virality scorer.
5. RAG/retrieval should provide trend/context features rather than make the final ranking decision.
6. Fine-tuning is deferred until there is a demonstrated need and enough relevant data.
7. First-party performance data is intended to become the most valuable long-term training signal.
8. The taxonomy must distinguish **virality/performance signals** from **technical quality, safety, and publication suitability**.
9. Candidate-relative features should be included so the system can compare moments against the video's own baseline.
10. The initial product goal is to produce a ranked shortlist of strong candidates, not a promise that any candidate will go viral.

---

## Part 2D — Open Questions for the Next Planning Step (SUPERSEDED — historical)

> **SUPERSEDED (v4):** open questions are tracked in 2.35.

1. Which features are actually feasible/reliable enough for MVP?
2. Which features should be extracted deterministically vs. by ML vs. by an LLM?
3. What candidate-generation algorithm should create the initial pool of clips?
4. What exact candidate duration range should the MVP support?
5. Which signals should be hand-weighted in the first heuristic scorer?
6. What data schema should store candidates and feature versions?
7. How should we construct an initial evaluation/labeled dataset before real users provide outcome data?
8. What should the first ranking target be once we have performance data?

