"""Phase 3 REAL-MODEL exit-gate (owner decisions 2026-10-04 #12 and 2026-10-06 section 6).

`make smoke-real` must prove, with the real WhisperX / pyannote / fastText adapters:
 1 ASR detects language without forcing English          6 cut-anchor validation works on real alignment
 2 a non-English fixture fails the language gate         7 diarization: deterministic first-appearance speaker ids
 3 the English fixture reaches alignment                 8 word->speaker uses the existing max-overlap rule
 4 alignment produces real word timing                   9 nothing (model or VAD) is downloaded during execution
 5 unaligned words stay untimed (never interpolated)    10 same input/config/models -> same canonical transcript

Blocked today (skipped with an explicit reason): BLOCKED_BY_SPEC when a runtime contract is not FROZEN;
BLOCKED_BY_DEPENDENCY until the models are materialized (scripts/materialize_models.py) and
lid.176.ftz + punkt_tab are provisioned. REQUIRE_REAL_MODELS=1 (make smoke-real) turns every blocked
condition into a FAILURE.  The fake-backed suite does NOT pass this gate.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
from pathlib import Path

import pytest
from shorts_config import canonical_json, load_config, sentence_seg_v1

from workers.cpu.language_gate import FastTextLanguageID, language_gate_v1
from workers.cpu.speaker_assignment import assign_word_speaker, build_turns
from workers.cpu.transcript_builder import build_transcript_v1
from workers.gpu import model_materialization as mm
from workers.gpu.backends import default_backends
from workers.shared.failures import BlockedBySpec, StageFailure

pytestmark = pytest.mark.real_models
REQUIRE = os.environ.get("REQUIRE_REAL_MODELS") == "1"
MEDIA = Path("packages/fixtures/media")
SV = "22222222-2222-4222-8222-222222222222"
SHA = "a" * 64


def _blocked(reason: str):
    if REQUIRE:
        pytest.fail(f"BLOCKED (REQUIRE_REAL_MODELS=1): {reason}")
    pytest.skip(f"BLOCKED: {reason}")


def _wav(tmp_path_factory, name: str) -> Path:
    out = tmp_path_factory.mktemp("smoke") / f"{name}.wav"
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-i", str(MEDIA / f"{name}.mp4"), "-vn", "-ac", "1", "-ar", "16000",
                    "-c:a", "pcm_s16le", str(out)], check=True, capture_output=True)
    return out


@pytest.fixture(scope="module")
def cfg():
    return load_config()


@pytest.fixture(scope="module")
def backends(cfg):
    try:
        return default_backends(cfg)
    except (BlockedBySpec, StageFailure) as exc:
        _blocked(f"{type(exc).__name__}: {str(exc)[:300]}")


@pytest.fixture(scope="module")
def lid(cfg):
    try:
        return FastTextLanguageID.from_provisioned_artifact(cfg["LANGUAGE_ID_MODEL_ID"])
    except StageFailure as exc:
        _blocked(f"BLOCKED_BY_DEPENDENCY: {exc.reason}")


@pytest.fixture(scope="module")
def en_wav(tmp_path_factory):
    return _wav(tmp_path_factory, "fixture_speech_45s")


@pytest.fixture(scope="module")
def fr_wav(tmp_path_factory):
    return _wav(tmp_path_factory, "fixture_speech_non_english_fr")


@pytest.fixture(scope="module")
def ms_wav(tmp_path_factory):
    return _wav(tmp_path_factory, "fixture_multi_speaker")


@pytest.fixture(scope="module")
def en_asr(backends, en_wav):
    return backends.asr.transcribe(en_wav), backends.asr.last_language


@pytest.fixture(scope="module")
def en_words(backends, en_wav, en_asr):
    return backends.alignment.align(en_wav, en_asr[0])


def test_fasttext_loads_verifies_and_predicts_through_the_adapter(lid):
    assert lid.sha256_verified and lid.adapter_version == "fasttext_predict_v1"
    assert lid.contract_check()[0] == "en"


# 1 ----------------------------------------------------------------------------------------------
def test_01_asr_detects_language_and_is_not_forced_to_english(cfg, backends, en_asr, fr_wav):
    assert cfg.runtime_contract("asr_runtime@1")["transcription"]["language"] is None
    segs, lang = en_asr
    assert lang == "en" and sum(len(s["text"].split()) for s in segs) >= 25
    backends.asr.transcribe(fr_wav)
    assert backends.asr.last_language == "fr"  # detected, not forced


# 2 ----------------------------------------------------------------------------------------------
def test_02_non_english_fixture_fails_the_language_gate(cfg, backends, lid, fr_wav):
    segs = backends.asr.transcribe(fr_wav)
    with pytest.raises(StageFailure) as e:
        language_gate_v1(segs, lid, cfg)
    assert e.value.reason == "unsupported_language"


# 3 ----------------------------------------------------------------------------------------------
def test_03_english_fixture_passes_the_gate_and_reaches_alignment(cfg, lid, en_asr, en_words):
    assert language_gate_v1(en_asr[0], lid, cfg).gate_status == "passed"
    assert en_words


# 4 ----------------------------------------------------------------------------------------------
def test_04_alignment_gives_real_monotonic_word_timing(en_words):
    timed = [w for w in en_words if w["start_ms"] is not None]
    assert len(timed) >= 0.8 * len(en_words)
    assert all(w["end_ms"] >= w["start_ms"] for w in timed)
    assert [w["start_ms"] for w in timed] == sorted(w["start_ms"] for w in timed)


# 5 ----------------------------------------------------------------------------------------------
def test_05_regression_unaligned_and_wildcard_words_stay_untimed(backends, en_wav):
    """Version-pinned regression (owner 2026-10-06 section 2): ordinary word, number, currency token,
    punctuation-heavy token, completely unalignable token. Evidence is written for the owner."""
    text = "Here is the price $50 in 2026 and the (!!!) ... $ plan"
    words = backends.alignment.align(en_wav, [{"start_ms": 0, "end_ms": 9000, "text": text}])
    by = {w["text"]: w for w in words}
    evidence = {w["text"]: {"start_ms": w["start_ms"], "end_ms": w["end_ms"], "timed": w["start_ms"] is not None}
                for w in words}
    out = Path("tests/real_models/_evidence")
    out.mkdir(exist_ok=True)
    (out / "alignment_regression.json").write_text(json.dumps(
        {"whisperx": "3.8.6", "text": text, "words": evidence}, indent=2, sort_keys=True))
    assert by["Here"]["start_ms"] is not None and by["price"]["start_ms"] is not None  # ordinary
    for tok in ("$50", "2026", "(!!!)", "...", "$"):  # wildcard-only / unalignable: never a timestamp
        assert by[tok]["start_ms"] is None and by[tok]["end_ms"] is None, tok


# 6 ----------------------------------------------------------------------------------------------
def test_06_cut_anchor_validation_on_real_alignment(cfg, backends, en_asr, en_words):
    doc = build_transcript_v1(
        cfg=cfg, source_video_id=SV, input_sha256=SHA,
        language={"gate_status": "passed", "code": "en", "confidence": 1.0, "model_id": "m", "model_sha256": None,
                  "sample_word_count": 99},
        audio_availability="present",
        asr={"status": "completed", "runtime_id": None, "runtime_sha256": None, "segment_count": len(en_asr[0]),
             "word_count": sum(len(s["text"].split()) for s in en_asr[0])},
        alignment_words=en_words, alignment={"runtime_id": None, "runtime_sha256": None},
        diarization={"attempted": False, "status": "unavailable", "missing_reason": "not_available_in_stage",
                     "provider": None, "model_id": None, "error_category": None, "turns": []},
        model_manifest={})
    assert doc["sentences"]
    for s in doc["sentences"]:
        assert (s["start_ms"] is not None) == s["start_timing_usable"]
        assert (s["end_ms"] is not None) == s["end_timing_usable"]
    assert all(s["end_ms"] - s["start_ms"] <= cfg["SENTENCE_MAX_S"] * 1000 + 1
               for s in doc["sentences"] if s["start_timing_usable"] and s["end_timing_usable"])


# 7 / 8 ------------------------------------------------------------------------------------------
def test_07_diarization_first_appearance_ids_are_deterministic(backends, ms_wav):
    a, b = backends.diarization.diarize(ms_wav), backends.diarization.diarize(ms_wav)
    ta, tb = build_turns(a), build_turns(b)
    assert [(t.start_ms, t.end_ms, t.speaker_id) for t in ta] == [(t.start_ms, t.end_ms, t.speaker_id) for t in tb]
    assert ta and ta[0].speaker_id == "SPK_0"
    assert {t.speaker_id for t in ta} >= {"SPK_0", "SPK_1"}  # two-speaker fixture
    seen: list[str] = []
    for t in ta:  # ids appear strictly in first-appearance order
        if t.speaker_id not in seen:
            seen.append(t.speaker_id)
    assert seen == [f"SPK_{i}" for i in range(len(seen))]


def test_08_word_to_speaker_uses_the_max_overlap_rule(backends, ms_wav):
    segs = backends.asr.transcribe(ms_wav)
    words = backends.alignment.align(ms_wav, segs)
    turns = build_turns(backends.diarization.diarize(ms_wav))
    for w in (x for x in words if x["start_ms"] is not None):
        best = max(((max(0, min(w["end_ms"], t.end_ms) - max(w["start_ms"], t.start_ms)), -t.start_ms, t) for t in turns),
                   key=lambda x: (x[0], x[1]), default=None)
        expect = None if best is None or best[0] <= 0 else best[2].speaker_id
        assert assign_word_speaker(w["start_ms"], w["end_ms"], turns) == expect


# 9 ----------------------------------------------------------------------------------------------
def test_09_nothing_is_downloaded_during_execution(cfg, backends, en_wav, monkeypatch):
    root = mm.models_root()

    def tree():
        return {str(p): (p.stat().st_size, p.stat().st_mtime_ns) for p in sorted(root.rglob("*")) if p.is_file()}
    before = tree()
    real_connect = socket.socket.connect

    def guarded(self, address):
        host = address[0] if isinstance(address, tuple) else address
        if isinstance(host, str) and host not in ("127.0.0.1", "::1", "localhost") and not host.startswith("/"):
            raise AssertionError(f"network access attempted: {address}")
        return real_connect(self, address)
    monkeypatch.setattr(socket.socket, "connect", guarded)
    segs = backends.asr.transcribe(en_wav)
    backends.alignment.align(en_wav, segs)
    backends.diarization.diarize(en_wav)
    assert os.environ.get("HF_HUB_OFFLINE") == "1" and os.environ.get("TRANSFORMERS_OFFLINE") == "1"
    assert tree() == before  # no model / VAD / nltk file appeared or changed


# 10 ---------------------------------------------------------------------------------------------
def test_10_two_runs_give_the_same_canonical_transcript(cfg, backends, en_wav):
    def run():
        segs = backends.asr.transcribe(en_wav)
        words = backends.alignment.align(en_wav, segs)
        turns = backends.diarization.diarize(en_wav)
        return canonical_json(build_transcript_v1(
            cfg=cfg, source_video_id=SV, input_sha256=SHA,
            language={"gate_status": "passed", "code": "en", "confidence": 1.0, "model_id": "m", "model_sha256": None,
                      "sample_word_count": 99},
            audio_availability="present",
            asr={"status": "completed", "runtime_id": backends.asr.runtime_id,
                 "runtime_sha256": backends.asr.runtime_sha256, "segment_count": len(segs),
                 "word_count": sum(len(s["text"].split()) for s in segs)},
            alignment_words=words, alignment={"runtime_id": backends.alignment.runtime_id,
                                              "runtime_sha256": backends.alignment.runtime_sha256},
            diarization={"attempted": True, "status": "succeeded", "missing_reason": None, "provider": "gpu_dispatch",
                         "model_id": backends.diarization.model_id, "error_category": None, "turns": turns},
            model_manifest={**backends.asr.models, **backends.alignment.models, **backends.diarization.models}))
    assert run() == run()
    _ = sentence_seg_v1  # (import kept: sentence segmentation is part of the canonical output)
