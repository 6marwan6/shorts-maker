"""Phase 4 unit tests (synthetic signals / fake encoder only). Nothing here claims validation
against real Phase-3 output or the real embedding model (owner decision 2026-10-07 s1/s11)."""
from __future__ import annotations

import copy
import json
import math
import subprocess
from fractions import Fraction
from pathlib import Path

import jsonschema
import numpy as np
import pytest
from shorts_config import ConfigSpecGap, TextTiling_depth_v1, load_config, local_nonspeech_rms_v1
from shorts_config.registry import Config
from tests.support.fakes import FakeEncoder
from workers.cpu import audio_features as af
from workers.cpu.analysis_artifacts import SCHEMA_DIR, build_analysis_artifact
from workers.cpu.embeddings import (EmbeddingDeterminismError, assert_bitwise_deterministic,
                                    compute_sentence_embeddings, text_sha256)
from workers.cpu.frame_manifest import build_frame_manifest, sample_frames
from workers.cpu.shot_map import compute_shot_map, frame_to_ms, shots_from_scene_list
from workers.cpu.texttiling_stage import compute_texttiling

CFG = load_config()
JOB, SRC = "11111111-1111-4111-8111-111111111111", "22222222-2222-4222-8222-222222222222"
IDS = dict(job_id=JOB, source_video_id=SRC, input_artifact_ids=["33333333-3333-4333-8333-333333333333"],
           input_sha256s=["a" * 64], input_sha256="b" * 64)


def cfg_with_epsilon(eps: float = 1e-6) -> Config:
    """TEST-ONLY: rms_db_runtime@1 is BLOCKED_BY_SPEC in config@1; this builds a throwaway Config
    that pretends it is frozen so the dB code path can be exercised. The value is not a decision."""
    raw = json.loads(Path("packages/config/config@1.json").read_text())
    raw["runtime_contracts"]["rms_db_runtime@1"].update(status="FROZEN", values={"epsilon": eps})
    return Config(raw)


def art(kind, content):
    return build_analysis_artifact(kind, content, cfg=CFG, **IDS)


# ----------------------------------------------------------------------------- config freeze
def test_embedding_runtime_frozen_exactly():
    c = CFG.runtime_contract("embedding_runtime@1")
    assert c["model"]["revision"] == "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
    assert c["model"]["model_sha256"] == "3c9f31665447c8911517620762200d2245a2518d6e7208acc78cd9db317e21ad"
    assert (c["backend"]["device"], c["backend"]["dtype"]) == ("cpu", "float32")
    assert c["pooling"] == {"mode": "cls", "dimension": 384}
    assert c["execution"] == {"batch_size": 1, "torch_num_threads": 1, "torch_num_interop_threads": 1,
                              "deterministic_algorithms": True}
    assert c["runtime_downloads"] is False and c["tokenizer"]["prompt_prefix"] is None
    assert CFG["EMBEDDING_MODEL_ID"] == c["model"]["model_id"]


@pytest.mark.parametrize("name", ["face_runtime@1", "frame_resize_runtime@1", "rms_db_runtime@1"])
def test_unresolved_phase4_contracts_raise_not_default(name):
    with pytest.raises(ConfigSpecGap):
        CFG.runtime_contract(name)


def test_phase4_constants_are_owner_values():
    assert CFG["MOTION_EVENT_PROBE_FPS"] == 10 and CFG["MOTION_MAX_DIM_PX"] == 512 and CFG["SCREEN_MAX_DIM_PX"] == 1280
    assert CFG["FARNEBACK"] == {"pyr_scale": 0.5, "levels": 3, "winsize": 15, "iterations": 3,
                                "poly_n": 5, "poly_sigma": 1.2, "flags": 0}
    assert (CFG["RMS_FRAME_LENGTH_SAMPLES"], CFG["RMS_HOP_LENGTH_SAMPLES"]) == (400, 160)
    assert CFG["SHOT_CONTENT_THRESHOLD"] == 27.0 and CFG["SHOT_MIN_SCENE_FRAMES"] == 15


# ----------------------------------------------------------------------------- audio
def test_rms_constant_amplitude_and_no_padding():
    x = np.full(16000 + 80, 0.5)
    r10 = af.rms_stream_v1(x, 400, 160)
    assert np.allclose(r10, 0.5) and r10.size == 1 + (x.size - 400) // 160
    r1 = af.rms_stream_v1(x, 16000, 16000)
    assert r1.size == 1 and np.allclose(r1, 0.5)          # trailing partial second: no frame (R1)
    assert af.rms_stream_v1(np.ones(100), 400, 160).size == 0


def test_local_nonspeech_centered_edge_truncated_linear_percentile():
    r = np.arange(100, dtype=float)               # second j has RMS j
    # t=50.0 -> frames with centers in [20,80] -> j in 20..79 (center j+.5 in [20,80]) ; p20 of 20..79
    expected = np.percentile(np.arange(20, 80), 20)
    assert local_nonspeech_rms_v1(50.0, r) == pytest.approx(expected)
    # edge: t=0 -> centers in [-30,30] truncated -> j in 0..29
    assert local_nonspeech_rms_v1(0.0, r) == pytest.approx(np.percentile(np.arange(0, 30), 20))
    # centered, not trailing: a trailing window would see only low values at t=10
    assert local_nonspeech_rms_v1(10.0, r) == pytest.approx(np.percentile(np.arange(0, 40), 20))
    assert local_nonspeech_rms_v1(5.0, np.array([])) is None


def _burst_signal(sr=16000, seconds=12, burst=(2.0, 4.0), amp=0.3, floor=0.002):
    t = np.arange(sr * seconds) / sr
    x = np.full(t.size, floor)
    m = (t >= burst[0]) & (t < burst[1])
    x[m] = amp * np.sin(2 * np.pi * 220 * t[m])
    return (x * 32767).astype(np.int16)


def test_silence_and_pause_intervals_use_audio_not_word_gaps_alone():
    pcm = _burst_signal()
    # words: first ends at 1.0 s, next starts at 1.9 s (gap fully silent); second gap 4.2->... overlaps burst? use 3.0->3.5 inside burst
    words = [
        {"word_id": "W000001", "start_ms": 0, "end_ms": 1000}, {"word_id": "W000002", "start_ms": 1900, "end_ms": 3000},
        {"word_id": "W000003", "start_ms": 3500, "end_ms": 5000}, {"word_id": "W000004", "start_ms": None, "end_ms": None},
        {"word_id": "W000005", "start_ms": 6000, "end_ms": 6500},
    ]
    out = af.compute_audio_features(pcm, words, cfg_with_epsilon(), epsilon=1e-6)
    pauses = {(p["previous_word_id"], p["next_word_id"]): p for p in out["pause_intervals"]}
    assert pauses[("W000001", "W000002")]["fully_nonspeech"] is True and pauses[("W000001", "W000002")]["duration_ms"] == 900
    assert pauses[("W000002", "W000003")]["fully_nonspeech"] is False      # gap lies inside the loud burst
    assert not any("W000004" in k for k in pauses)                          # unaligned word is never a gap edge
    # silence intervals are contiguous nonspeech 10 ms frames, ms-aligned, duration consistent
    assert all(s["end_ms"] - s["start_ms"] == s["duration_ms"] and s["start_ms"] % 10 == 0 for s in out["silence_intervals"])
    assert any(s["start_ms"] <= 1000 and s["end_ms"] >= 1900 for s in out["silence_intervals"])


def test_audio_peaks_threshold_spacing_and_greedy_chronological():
    sr, hop = 16000, 160
    n = 6000 * 3                                   # 180 s of 10 ms frames
    rng = np.random.default_rng(0)
    r = 0.01 + 0.002 * rng.random(n)
    r[1000], r[1100], r[1400] = 0.4, 0.9, 0.5     # 1000 and 1100 are 1.0 s apart -> only the first accepted; 1400 is 4 s after 1000
    peaks = af.audio_peaks_v1(r, hop_ms=10, window_s=60, z_min=2.0, min_spacing_s=3.0, mad_floor=0.01)
    assert [p["time_ms"] for p in peaks] == [10_000, 14_000]
    assert all(p["robust_z"] >= 2.0 for p in peaks)
    # flat signal: no local maximum >= floor-based threshold
    assert af.audio_peaks_v1(np.full(500, 0.01), hop_ms=10, window_s=60, z_min=2.0, min_spacing_s=3.0, mad_floor=0.01) == []


def test_rms_db_requires_epsilon_and_uses_population_std():
    with pytest.raises(ValueError):
        af.compute_audio_features(_burst_signal(), [], CFG, epsilon=None)
    r = np.array([0.1, 0.01] * 500)
    out = af.rms_db_by_bin_v1(r, hop_ms=10, bin_s=10, epsilon=1e-6, duration_ms=10_000)
    db = 20 * np.log10(r)
    assert out[0]["rms_std_db"] == pytest.approx(float(db.std()))        # ddof=0
    assert out[0]["rms_mean_db"] == pytest.approx(float(db.mean()))
    zero = af.rms_db_by_bin_v1(np.zeros(1000), hop_ms=10, bin_s=10, epsilon=1e-6, duration_ms=10_000)
    assert math.isfinite(zero[0]["rms_mean_db"]) and zero[0]["rms_std_db"] == 0.0


def test_no_audio_stream_is_not_applicable_and_validates():
    c = af.compute_audio_features(None, [], CFG, epsilon=None)
    assert c["missing_reason"] == "not_applicable" and c["rms_samples"] == []
    a = art("audio_features_v1", {**c, "provenance": {"decoder": "soundfile", "decoder_version": "x", "rms_db_runtime_sha256": None,
                                                      "std_ddof": 0, "peak_local_maximum_rule": af.PEAK_LOCAL_MAX_RULE}})
    assert a["stage"] == "ANALYZING"


def test_full_audio_artifact_validates_and_is_deterministic():
    pcm = _burst_signal()
    cfg = cfg_with_epsilon()
    c1 = af.compute_audio_features(pcm, [], cfg, epsilon=1e-6)
    c2 = af.compute_audio_features(pcm, [], cfg, epsilon=1e-6)
    assert c1 == c2
    prov = {"decoder": "soundfile", "decoder_version": "x", "rms_db_runtime_sha256": "c" * 64, "std_ddof": 0,
            "peak_local_maximum_rule": af.PEAK_LOCAL_MAX_RULE}
    art("audio_features_v1", {**c1, "provenance": prov})


# ----------------------------------------------------------------------------- shot map
def test_frame_to_ms_round_half_up_exact():
    assert frame_to_ms(1, 24) == 42 and frame_to_ms(2, 24) == 83 and frame_to_ms(48, 24) == 2000
    assert frame_to_ms(1, 50) == 20 and frame_to_ms(0, 30) == 0


def test_shots_from_scene_list_contract():
    s = shots_from_scene_list([(0, 48), (48, 168)], 168, 24)
    assert [x["start_ms"] for x in s] == [0, 2000] and s[-1]["end_frame"] == 168
    assert shots_from_scene_list([], 10, 24)[0]["end_frame"] == 10      # no cut = one shot
    for bad in ([(0, 10), (11, 20)], [(0, 10), (10, 10)], [(0, 5)], [(0, 30)]):
        with pytest.raises(ValueError):
            shots_from_scene_list(bad, 20, 24)


def _probe(f):
    st = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                    "-show_entries", "stream=nb_read_frames,r_frame_rate", "-of", "json", str(f)]))["streams"][0]
    a, b = map(int, st["r_frame_rate"].split("/"))
    return a / b, int(st["nb_read_frames"])


def test_shot_map_on_real_fixture_is_frame_accurate_and_schema_valid():
    f = Path("packages/fixtures/media/fixture_event_6_8s.mp4")
    fps, n = _probe(f)
    sm = compute_shot_map(str(f), fps=fps, expected_frame_count=n, cfg=CFG)
    assert [(s["start_frame"], s["end_frame"]) for s in sm["shots"]] == [(0, 48), (48, n)]
    assert sm["shots"][1]["start_ms"] == 2000                # exact frame timestamp, not on any 2 fps grid rounding
    art("shot_map_v1", sm)
    with pytest.raises(ValueError):                           # decoded-vs-manifest frame count mismatch fails closed
        compute_shot_map(str(f), fps=fps, expected_frame_count=n + 1, cfg=CFG)


def test_shot_map_not_derived_from_2fps_grid():
    f = Path("packages/fixtures/media/fixture_multi_speaker.mp4")
    fps, n = _probe(f)
    sm = compute_shot_map(str(f), fps=fps, expected_frame_count=n, cfg=CFG)
    assert any(s["start_frame"] % 12 != 0 for s in sm["shots"][1:])   # 12 frames = 0.5 s grid at 24 fps


# ----------------------------------------------------------------------------- embeddings
SENTS = [{"sentence_id": f"S{i:06d}", "text": f"Sentence number {i} about topic {i % 3}.",
          "start_ms": None if i == 2 else i * 1000} for i in range(1, 8)]


def test_embeddings_one_per_sentence_including_unusable_timing_and_schema_valid():
    c = compute_sentence_embeddings(SENTS, FakeEncoder(), CFG)
    assert c["sentence_count"] == 7 and [s["sentence_id"] for s in c["sentences"]] == [s["sentence_id"] for s in SENTS]
    assert all(len(s["embedding"]) == 384 for s in c["sentences"])
    assert c["sentences"][0]["input_text_sha256"] == text_sha256(SENTS[0]["text"])    # exactly sentence.text
    assert c["model_revision"] == c["tokenizer_revision"] == "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
    art("sentence_embeddings_v1", c)


def test_embedding_truncation_recorded_not_split():
    long = {"sentence_id": "S000001", "text": " ".join(["word"] * 600)}
    c = compute_sentence_embeddings([long], FakeEncoder(), CFG)
    s = c["sentences"][0]
    assert c["sentence_count"] == 1 and s["truncated"] is True
    assert (s["original_token_count"], s["embedded_token_count"]) == (602, 512)


def test_embedding_bitwise_determinism_gate():
    assert_bitwise_deterministic(FakeEncoder(), [s["text"] for s in SENTS])
    with pytest.raises(EmbeddingDeterminismError):
        assert_bitwise_deterministic(FakeEncoder(nondeterministic=True), ["x", "y"])


def test_bad_vectors_fail_closed():
    class Bad(FakeEncoder):
        def encode_one(self, text):
            e = super().encode_one(text)
            return type(e)(e.vector * 2, e.original_token_count, e.embedded_token_count)
    with pytest.raises(ValueError):
        compute_sentence_embeddings(SENTS[:1], Bad(), CFG)


def test_embedding_schema_rejects_wrong_dimension():
    c = compute_sentence_embeddings(SENTS[:2], FakeEncoder(), CFG)
    c["sentences"][0]["embedding"] = c["sentences"][0]["embedding"][:383]
    with pytest.raises(jsonschema.ValidationError):
        art("sentence_embeddings_v1", c)


def test_embedding_not_materialized_is_blocked_by_dependency(tmp_path):
    from workers.gpu import model_materialization as mm
    from workers.shared.failures import FailureKind, StageFailure
    with pytest.raises(StageFailure) as e:
        mm.verify_embedding(CFG, tmp_path)
    assert e.value.kind == FailureKind.BLOCKED_BY_DEPENDENCY


# ----------------------------------------------------------------------------- TextTiling
def test_texttiling_matches_primitive_and_nulls_incomplete_windows():
    c = compute_sentence_embeddings([{"sentence_id": f"S{i:06d}", "text": f"t{i}"} for i in range(1, 31)], FakeEncoder(), CFG)
    embs = [s["embedding"] for s in c["sentences"]]
    ids = [s["sentence_id"] for s in c["sentences"]]
    tt = compute_texttiling(ids, embs, CFG)
    assert len(tt["boundaries"]) == 29
    assert [b["semantic_depth"] for b in tt["boundaries"]] == TextTiling_depth_v1(embs, 5)
    assert all(b["topic_depth"] is None and b["topic_missing_reason"] == "no_evidence" for b in tt["boundaries"])   # 30 < 2*25
    assert tt["boundaries"][0]["semantic_missing_reason"] == "no_evidence"
    assert any(b["semantic_depth"] is not None for b in tt["boundaries"])
    art("texttiling_depth_v1", tt)
    assert compute_texttiling(ids[:1], embs[:1], CFG)["missing_reason"] == "no_content"


# ----------------------------------------------------------------------------- frame manifest
def test_sample_frames_exact_rational_indices():
    s = sample_frames(48, Fraction(24), Fraction(5))
    assert s[0] == (0, 0) and s[1] == (4, 167) and s[2] == (9, 375)       # floor(k*24/5): 0,4,9
    assert len(sample_frames(24, Fraction(24), Fraction(2))) == 2          # t=0, 0.5 s ; t=1.0 s is frame 24 (out)
    assert [i for i, _ in sample_frames(30, Fraction(24), Fraction(10))][:4] == [0, 2, 4, 7]


def test_frame_manifest_streams_and_resolver_boundary_schema_valid():
    calls = []
    def resolve(sid, w, h, md):
        calls.append((sid, md)); return w, h, {"kind": "test_only_policy"}
    m = build_frame_manifest(source_fps=Fraction(24), source_frame_count=168, width=640, height=360, cfg=CFG, resolve_size=resolve)
    ids = [s["stream_id"] for s in m["streams"]]
    assert ids == ["face", "motion", "motion_probe", "screen", "scene_context", "shot_detection"]
    assert dict(calls)["motion"] == 512 and dict(calls)["screen"] == 1280 and dict(calls)["face"] is None
    shot = m["streams"][-1]
    assert shot["frames"] is None and shot["sampling_fps"] is None
    assert [s["sampling_fps"] for s in m["streams"][:5]] == [5.0, 2.0, 10.0, 1.0, 2.0]
    art("frame_manifest_v1", m)


# ----------------------------------------------------------------------------- visual schema (shape only)
def test_visual_schema_accepts_minimal_valid_and_rejects_unknown_field():
    base = {"face_sample_fps": 5, "motion_sample_fps": 2, "motion_event_probe_fps": 10, "screen_analysis_fps": 1,
            "face_samples": [], "motion_samples": [], "motion_z_baseline": "open", "motion_peaks": [],
            "motion_change_samples": [], "screen_samples": [], "face_count_by_bin": [], "face_ratio_by_bin": [],
            "largest_face_ratio_by_bin": [], "motion_mean_by_bin": [], "motion_peak_rate_by_bin": [],
            "motion_change_by_bin": [], "screen_ratio_by_bin": [], "screen_boxes": [], "missing_reason": "not_run",
            "provenance": {"face_runtime_sha256": None, "face_model_sha256": None, "face_backend": "none",
                           "frame_resize_runtime_sha256": None, "farneback": {}, "opencv_version": "5", "screen_detector_version": "1"}}
    art("visual_features_v1", base)
    with pytest.raises(jsonschema.ValidationError):
        art("visual_features_v1", {**base, "surprise": 1})


def test_all_phase4_schemas_present_and_generated_types_exist():
    for k in ("audio_features_v1", "visual_features_v1", "shot_map_v1", "sentence_embeddings_v1",
              "texttiling_depth_v1", "frame_manifest_v1"):
        assert (SCHEMA_DIR / f"{k}.schema.json").exists()
        assert (Path("packages/schemas/python") / f"{k}.py").exists()
