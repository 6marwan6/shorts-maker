"""Phase 0.7 unit tests: deterministic analysis primitives (impl plan 0.7/2.3, v5.0 2.14.1)."""
import math

import pytest
from shorts_config import (
    AlignmentUnavailable,
    EmbeddingProvenanceIncomplete,
    Sentence,
    TextTiling_depth_v1,
    Word,
    forced_alignment_gate_v1,
    load_config,
    sentence_seg_v1,
    speaker_dependent_feature_v1,
    speaker_id_v1,
    validate_embedding_provenance_v1,
)

CFG = load_config()
SENTENCE_GAP_MS = CFG["SENTENCE_GAP_MS"]
SENTENCE_MAX_S = CFG["SENTENCE_MAX_S"]
HARD_SPLIT_MIN_GAP_MS = CFG["HARD_SPLIT_MIN_GAP_MS"]


def seg(words):
    return sentence_seg_v1(
        words, sentence_gap_ms=SENTENCE_GAP_MS, sentence_max_s=SENTENCE_MAX_S,
        hard_split_min_gap_ms=HARD_SPLIT_MIN_GAP_MS,
    )


# --------------------------------------------------------------------------------------
# sentence_seg_v1
# --------------------------------------------------------------------------------------

def test_sentence_seg_config_constants_match_v5_0():
    # regression guard: this test file's constants must track config@1, not a hardcoded copy
    assert SENTENCE_GAP_MS == 500
    assert SENTENCE_MAX_S == 15
    assert HARD_SPLIT_MIN_GAP_MS == 20


def test_empty_input():
    assert seg([]) == []


def test_single_word_is_one_sentence_ending_at_end_of_input():
    words = [Word("Hello", 0, 500)]
    out = seg(words)
    assert len(out) == 1
    assert out[0] == Sentence(0, 0, 0, 500, "end_of_input", False)


def test_terminal_punctuation_ends_sentence():
    words = [
        Word("Hi.", 0, 400),
        Word("Bye.", 500, 900),
    ]
    out = seg(words)
    assert len(out) == 2
    assert out[0].end_reason == "terminal_punctuation"
    assert out[0].word_end_idx == 0
    assert out[1].word_end_idx == 1


def test_terminal_punctuation_without_usable_timestamp_is_skipped():
    # word 0 ends with "." but end_ms is None -> not a usable timestamp -> scanning continues
    words = [
        Word("Hi.", 0, None),
        Word("there.", 400, 900),
    ]
    out = seg(words)
    # only one sentence: word 0's punctuation boundary was not usable, word 1 is end_of_input
    assert len(out) == 1
    assert out[0].word_start_idx == 0 and out[0].word_end_idx == 1
    assert out[0].end_reason == "end_of_input"


def test_gap_with_speaker_change_ends_sentence_without_punctuation():
    words = [
        Word("okay", 0, 400, speaker_id="A"),
        Word("well", 400 + SENTENCE_GAP_MS, 1200, speaker_id="B"),
    ]
    out = seg(words)
    assert len(out) == 2
    assert out[0].end_reason == "gap_speaker_change"


def test_gap_with_uppercase_next_token_ends_sentence():
    words = [
        Word("okay", 0, 400),
        Word("Well", 400 + SENTENCE_GAP_MS, 1200),
    ]
    out = seg(words)
    assert len(out) == 2
    assert out[0].end_reason == "gap_uppercase"


def test_gap_without_speaker_change_or_uppercase_does_not_end_sentence():
    words = [
        Word("okay", 0, 400),
        Word("well", 400 + SENTENCE_GAP_MS, 1200),
        Word("then.", 1200, 1700),
    ]
    out = seg(words)
    assert len(out) == 1
    assert out[0].word_start_idx == 0 and out[0].word_end_idx == 2


def test_small_gap_alone_never_ends_sentence():
    words = [
        Word("okay", 0, 400, speaker_id="A"),
        Word("Well", 400 + SENTENCE_GAP_MS - 1, 1200, speaker_id="B"),  # 1ms short of threshold
        Word("then.", 1200, 1700, speaker_id="B"),
    ]
    out = seg(words)
    assert len(out) == 1  # gap < SENTENCE_GAP_MS -> rule never fires regardless of trigger


def test_never_splits_inside_a_word():
    # every returned (start,end) pair must reference whole word indices only
    words = [Word(f"w{i}", i * 100, i * 100 + 90) for i in range(5)]
    out = seg(words)
    covered = []
    for s in out:
        covered.extend(range(s.word_start_idx, s.word_end_idx + 1))
    assert covered == list(range(5))


def test_long_span_splits_at_largest_qualifying_gap():
    # Two tight clusters of short words (each well under 15s), joined by one huge inter-word
    # gap. The huge gap is by far the largest and clearly qualifies (>= 20ms), so the split
    # must land exactly there, producing two pieces that are each already <= 15s.
    left = [Word(f"l{i}", i * 210, i * 210 + 200) for i in range(5)]      # spans [0, 1040]
    right_base = 15040
    right = [Word(f"r{i}", right_base + i * 210, right_base + i * 210 + 200) for i in range(5)]
    words = left + right
    assert (words[-1].end_ms - words[0].start_ms) > SENTENCE_MAX_S * 1000
    out = seg(words)
    assert len(out) == 2
    assert out[0].word_start_idx == 0 and out[0].word_end_idx == 4
    assert out[0].end_reason == "hard_split_gap"
    assert out[0].synthetic_boundary is False
    assert out[1].word_start_idx == 5 and out[1].word_end_idx == 9
    assert out[1].end_reason == "end_of_input"
    for s in out:
        assert (s.end_ms - s.start_ms) <= SENTENCE_MAX_S * 1000


def test_long_span_with_no_qualifying_gap_uses_largest_available_and_marks_synthetic():
    # every inter-word gap is below HARD_SPLIT_MIN_GAP_MS (20ms), but total span > 15s
    n = 20
    words = []
    t = 0
    for i in range(n):
        words.append(Word(f"w{i}", t, t + 800))
        t += 800 + 5  # 5ms gaps everywhere -- below the 20ms hard-split threshold
    out = seg(words)
    assert (words[-1].end_ms - words[0].start_ms) > SENTENCE_MAX_S * 1000
    assert len(out) >= 2
    assert any(s.synthetic_boundary for s in out[:-1])
    assert all(s.end_reason in ("synthetic_split", "end_of_input") for s in out)


def test_recursive_split_keeps_every_piece_under_max_span():
    n = 40
    words = []
    t = 0
    for i in range(n):
        words.append(Word(f"w{i}", t, t + 900))
        t += 900 + 5
    out = seg(words)
    for s in out:
        assert (s.end_ms - s.start_ms) <= SENTENCE_MAX_S * 1000 or s.word_start_idx == s.word_end_idx


def test_tie_break_uses_earliest_gap():
    # Two equally-large qualifying gaps (both 7300ms) surrounding a small 100ms gap; total
    # span just over 15s so exactly one split is needed. The split must land at the EARLIER
    # of the two tied largest gaps (v5.0: "ties use the earliest gap").
    w0 = Word("a", 0, 100)
    w1 = Word("b", 100 + 7300, 7500)
    w2 = Word("c", 7500 + 100, 7700)
    w3 = Word("d", 7700 + 7300, 15100)
    words = [w0, w1, w2, w3]
    assert (words[-1].end_ms - words[0].start_ms) > SENTENCE_MAX_S * 1000
    gap_a = w1.start_ms - w0.end_ms
    gap_b = w3.start_ms - w2.end_ms
    assert gap_a == gap_b, "fixture must have two tied largest gaps"
    out = seg(words)
    assert len(out) == 2
    assert out[0].word_start_idx == 0 and out[0].word_end_idx == 0
    assert out[0].end_reason == "hard_split_gap"
    assert out[1].word_start_idx == 1 and out[1].word_end_idx == 3


# --------------------------------------------------------------------------------------
# TextTiling_depth_v1
# --------------------------------------------------------------------------------------

def _unit(v):
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v] if n else v


def test_texttiling_too_few_sentences_returns_empty():
    assert TextTiling_depth_v1([[1.0, 0.0]], window=2) == []


def test_texttiling_incomplete_window_is_null():
    # 3 sentences, window=5 -> no boundary has a complete pair of size-5 windows
    embeddings = [_unit([1, 0]), _unit([0, 1]), _unit([1, 1])]
    depths = TextTiling_depth_v1(embeddings, window=5)
    assert len(depths) == 2  # n-1 boundaries
    assert all(d is None for d in depths)


def test_texttiling_symmetric_topic_shift_has_higher_depth_at_the_shift():
    # two tight clusters of embeddings far apart in direction -> the boundary between clusters
    # should have a larger gap (1 - cosine) than boundaries inside a cluster.
    cluster_a = [_unit([1.0, 0.01 * i]) for i in range(4)]
    cluster_b = [_unit([0.01 * i, 1.0]) for i in range(4)]
    embeddings = cluster_a + cluster_b
    window = 3
    depths = TextTiling_depth_v1(embeddings, window=window)
    # boundary index 3 is the cluster_a/cluster_b transition (between sentence 3 and 4)
    shift_boundary = 3
    complete = [(i, d) for i, d in enumerate(depths) if d is not None]
    assert complete, "expected at least one complete-window boundary in this fixture"
    shift_depth = dict(complete).get(shift_boundary)
    if shift_depth is not None:
        others = [d for i, d in complete if i != shift_boundary]
        if others:
            assert shift_depth >= max(others)


def test_texttiling_gap_uses_cosine_distance_not_euclidean():
    # identical direction vectors of different magnitude -> cosine similarity 1 -> gap 0
    embeddings = [[1.0, 0.0], [2.0, 0.0], [3.0, 0.0], [4.0, 0.0], [5.0, 0.0], [6.0, 0.0]]
    depths = TextTiling_depth_v1(embeddings, window=2)
    complete = [d for d in depths if d is not None]
    assert complete and all(math.isclose(d, 0.0, abs_tol=1e-9) for d in complete)


# --------------------------------------------------------------------------------------
# Embedding provenance
# --------------------------------------------------------------------------------------

VALID_PROVENANCE = {
    "model_id": "BAAI/bge-small-en-v1.5",
    "model_revision": "abcdef1",
    "checksum": "sha256:" + "a" * 64,
    "backend": "sentence-transformers",
    "tokenizer": "bge-small-en-v1.5-tokenizer",
    "precision": "fp32",
    "deterministic": True,
}


def test_embedding_provenance_valid_passes():
    validate_embedding_provenance_v1(VALID_PROVENANCE, expected_model_id="BAAI/bge-small-en-v1.5")


@pytest.mark.parametrize("missing_field", list(VALID_PROVENANCE.keys() - {"deterministic"}))
def test_embedding_provenance_missing_field_raises(missing_field):
    bad = dict(VALID_PROVENANCE)
    del bad[missing_field]
    with pytest.raises(EmbeddingProvenanceIncomplete):
        validate_embedding_provenance_v1(bad, expected_model_id="BAAI/bge-small-en-v1.5")


def test_embedding_provenance_wrong_model_id_raises():
    bad = dict(VALID_PROVENANCE)
    bad["model_id"] = "some-other-model"
    with pytest.raises(EmbeddingProvenanceIncomplete):
        validate_embedding_provenance_v1(bad, expected_model_id="BAAI/bge-small-en-v1.5")


def test_embedding_provenance_non_deterministic_raises():
    bad = dict(VALID_PROVENANCE)
    bad["deterministic"] = False
    with pytest.raises(EmbeddingProvenanceIncomplete):
        validate_embedding_provenance_v1(bad, expected_model_id="BAAI/bge-small-en-v1.5")


def test_embedding_model_id_matches_config():
    assert VALID_PROVENANCE["model_id"] == CFG["EMBEDDING_MODEL_ID"]


# --------------------------------------------------------------------------------------
# No-diarization fallback
# --------------------------------------------------------------------------------------

def test_speaker_dependent_feature_available():
    assert speaker_dependent_feature_v1(True, diarization_available=True) == {"v": True, "m": None}


def test_speaker_dependent_feature_unavailable_is_null_not_zero():
    result = speaker_dependent_feature_v1(True, diarization_available=False)
    assert result == {"v": None, "m": "not_available_in_stage"}
    assert result["v"] is None  # explicitly not 0 / False / "" -- true null


def test_speaker_id_null_when_no_diarization():
    assert speaker_id_v1("spk_1", diarization_available=False) is None
    assert speaker_id_v1("spk_1", diarization_available=True) == "spk_1"


# --------------------------------------------------------------------------------------
# Forced alignment gate
# --------------------------------------------------------------------------------------

def test_zero_words_allows_event_only_path():
    assert forced_alignment_gate_v1(asr_word_count=0, alignment_produced_word_timestamps=False) == "not_applicable"


def test_words_with_successful_alignment_proceeds():
    assert forced_alignment_gate_v1(asr_word_count=120, alignment_produced_word_timestamps=True) == "aligned"


def test_words_without_alignment_raises_not_silently_substitutes():
    with pytest.raises(AlignmentUnavailable):
        forced_alignment_gate_v1(asr_word_count=120, alignment_produced_word_timestamps=False)
