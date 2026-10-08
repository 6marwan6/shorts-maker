"""Phase 3 unit tests (impl plan Phase 3; owner decisions 2026-09-30 C1-C4, G1-G8).

Real WhisperX / pyannote / fastText inference cannot run in the CI sandbox (no GPU, no model
files, no network), so every backend here is a deterministic fake behind the production
Protocols. The tests that need the real models are listed in docs/implementation_constraints.md
as BLOCKED_BY_DEPENDENCY / BLOCKED_BY_SPEC, not silently skipped as passing.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest
from shorts_config import (
    AlignmentUnavailable,
    ConfigSpecGap,
    Word,
    canonical_json,
    load_config,
    sentence_seg_v1,
    validate_cut_anchor_timing_v1,
)

from workers.cpu.language_gate import FastTextLanguageID, language_gate_v1, select_language_sample
from workers.cpu.speaker_assignment import assign_word_speaker, build_turns
from workers.cpu.transcript_builder import build_transcript_v1
from workers.gpu.backends import Backends, default_backends
from workers.shared.failures import BlockedBySpec, FailureKind, StageFailure
from workers.shared.gpu_provider import (
    ConfigIdentity,
    GPUJobState,
    LocalROCmGPUProvider,
)

SCHEMA = json.loads(Path("packages/schemas/json/transcript_v1.schema.json").read_text())
CFG = load_config()
SV = "11111111-1111-4111-8111-111111111111"
SHA = "a" * 64


class FakeLID:
    model_id = "fasttext/lid.176.ftz"
    model_sha256 = SHA

    def __init__(self, code="en", conf=0.99):
        self.code, self.conf = code, conf

    def predict(self, text):
        return self.code, self.conf


def _w(text, s, e, conf=0.9):
    return {"text": text, "start_ms": s, "end_ms": e, "confidence": conf}


def _words():
    return [_w("Hello", 0, 400), _w("everyone.", 450, 900), _w("This", 2000, 2300), _w("is", 2350, 2450),
            _w("a", 2500, 2550), _w("test.", 2600, 3000)]


def _doc(*, words=None, diar=None, asr_words=6, audio="present", lang=None):
    diar = diar or {"attempted": True, "status": "succeeded", "missing_reason": None, "provider": "gpu_dispatch",
                    "model_id": "pyannote/speaker-diarization-community-1", "error_category": None,
                    "turns": [{"start_ms": 0, "end_ms": 1000, "raw_label": "SPEAKER_07"},
                              {"start_ms": 1900, "end_ms": 3100, "raw_label": "SPEAKER_02"}]}
    lang = lang or {"gate_status": "not_applicable", "code": None, "confidence": None,
                    "model_id": "fasttext/lid.176.ftz", "model_sha256": SHA, "sample_word_count": 6}
    return build_transcript_v1(
        cfg=CFG, source_video_id=SV, input_sha256=SHA, language=lang, audio_availability=audio,
        asr={"status": "completed" if audio == "present" else "not_applicable_no_audio",
             "runtime_id": None, "runtime_sha256": None, "segment_count": 1, "word_count": asr_words},
        alignment_words=words, alignment={"runtime_id": None, "runtime_sha256": None},
        diarization=diar, model_manifest={})


def _valid(doc):
    jsonschema.Draft202012Validator(SCHEMA).validate(doc)


# ---------------- G1: transcript_v1 schema fixtures (5 required) ----------------------------

def test_fixture_1_normal_speech():
    d = _doc(words=_words())
    _valid(d)
    assert [s["sentence_id"] for s in d["sentences"]] == ["S000001", "S000002"]
    assert d["words"][0]["word_id"] == "W000001"
    # raw labels become SPK_n by first appearance (sorted by start) -- G5
    assert [t["speaker_id"] for t in d["speaker_turns"]] == ["SPK_0", "SPK_1"]
    assert d["sentences"][0]["speaker_id"] == "SPK_0" and d["sentences"][1]["speaker_id"] == "SPK_1"


def test_fixture_2_zero_word_event_only_input():
    d = _doc(words=None, asr_words=0, audio="not_applicable",
             diar={"attempted": False, "status": "not_applicable_no_speech", "missing_reason": None,
                   "provider": None, "model_id": None, "error_category": None, "turns": []})
    _valid(d)
    assert d["words"] == [] and d["sentences"] == [] and d["provenance"]["alignment"]["status"] == "not_applicable"
    assert d["provenance"]["audio"]["availability"] == "not_applicable"


@pytest.mark.parametrize("status,reason", [("unavailable", "not_available_in_stage"), ("failed", "extraction_failed")])
def test_fixture_3_diarization_unavailable_or_failed_is_null_not_zero(status, reason):
    d = _doc(words=_words(), diar={"attempted": status == "failed", "status": status, "missing_reason": reason,
                                   "provider": None, "model_id": None, "error_category": "x", "turns": []})
    _valid(d)
    assert all(w["speaker_id"] is None for w in d["words"]) and d["speaker_turns"] == []
    assert d["provenance"]["diarization"]["missing_reason"] == reason  # C4: distinct causes


def test_fixture_4_partial_word_timing_keeps_text_never_interpolates():
    # (a) sentence-EDGE word unaligned: job continues, sentence kept, edge marked unusable (owner 2026-10-02 #1)
    words = _words()
    words[2] = _w("This", None, None)
    d = _doc(words=words)
    _valid(d)
    s2 = d["sentences"][1]
    assert s2["text"].startswith("This") and s2["start_ms"] is None and s2["start_timing_usable"] is False
    assert s2["end_timing_usable"] is True and s2["end_ms"] == 3000
    assert d["sentences"][0]["start_timing_usable"] and d["sentences"][0]["end_timing_usable"]
    # (b) interior word unaligned: text kept, timing null, never interpolated, no speaker
    words = _words()
    words[3] = _w("is", None, None)
    d = _doc(words=words)
    _valid(d)
    w = d["words"][3]
    assert (w["text"], w["start_ms"], w["end_ms"], w["timing_status"], w["speaker_id"]) == ("is", None, None, "unaligned", None)
    assert d["provenance"]["alignment"]["unaligned_word_count"] == 1
    assert all(s["start_timing_usable"] and s["end_timing_usable"] for s in d["sentences"])
    # (c) one-sided timing is not usable timing -> normalized to unaligned; its '.' is no boundary
    words = _words()
    words[1] = _w("everyone.", 450, None)
    d = _doc(words=words)
    _valid(d)
    assert d["words"][1]["timing_status"] == "unaligned" and d["words"][1]["start_ms"] is None
    assert len(d["sentences"]) == 1
    # (d) the ONLY job-level failure: words exist but NONE received forced-aligned timing
    with pytest.raises(AlignmentUnavailable):
        _doc(words=[_w(x["text"], None, None) for x in _words()])


def test_unusable_edges_never_get_synthesized_or_coarse_timing():
    words = _words()
    words[5] = _w("test.", None, None)  # LAST word of the last sentence
    d = _doc(words=words)
    last = d["sentences"][-1]
    assert last["end_ms"] is None and last["end_timing_usable"] is False
    assert last["start_ms"] == 2000 and last["start_timing_usable"] is True


def test_fixture_5_deterministic_reserialization():
    a, b = _doc(words=_words()), _doc(words=_words())
    assert canonical_json(a) == canonical_json(b)
    again = json.loads(canonical_json(a))
    assert canonical_json(again) == canonical_json(a)


def test_schema_rejects_bad_ids_and_unknown_fields():
    d = _doc(words=_words())
    bad = copy.deepcopy(d); bad["sentences"][0]["sentence_id"] = "U1"
    with pytest.raises(jsonschema.ValidationError):
        _valid(bad)
    bad = copy.deepcopy(d); bad["extra"] = 1
    with pytest.raises(jsonschema.ValidationError):
        _valid(bad)


def test_generated_pydantic_model_round_trips():
    from packages.schemas.python.transcript_v1 import TranscriptV1 as Transcript
    m = Transcript.model_validate(_doc(words=_words()))
    assert m.sentences[0].sentence_id == "S000001"


# ---------------- G2: ids ----------------------------------------------------------------------

def test_sentence_ids_depend_only_on_order_not_time_or_text():
    shifted = [_w(w["text"], w["start_ms"] + 5000, w["end_ms"] + 5000) for w in _words()]
    a, b = _doc(words=_words()), _doc(words=shifted)
    assert [s["sentence_id"] for s in a["sentences"]] == [s["sentence_id"] for s in b["sentences"]]


# ---------------- G4: sentence_seg with null timing -------------------------------------------

def test_sentence_seg_handles_unaligned_words_without_crash_or_interpolation():
    ws = [Word("a", 0, 100), Word("b", None, None), Word("c.", 300, 400), Word("d", 500, 600)]
    sents = sentence_seg_v1(ws, sentence_gap_ms=500, sentence_max_s=15, hard_split_min_gap_ms=20)
    assert [(s.word_start_idx, s.word_end_idx) for s in sents] == [(0, 2), (3, 3)]
    validate_cut_anchor_timing_v1(ws, sents)


def test_terminal_punctuation_on_unaligned_word_does_not_end_sentence():
    ws = [Word("a", 0, 100), Word("b.", None, None), Word("c", 300, 400), Word("d.", 450, 500)]
    sents = sentence_seg_v1(ws, sentence_gap_ms=500, sentence_max_s=15, hard_split_min_gap_ms=20)
    assert len(sents) == 1  # the unaligned '.' never counts as a boundary


# ---------------- G5: speaker assignment ------------------------------------------------------

def test_speaker_max_overlap_tie_break_and_none():
    turns = build_turns([{"start_ms": 0, "end_ms": 500, "raw_label": "B"},
                         {"start_ms": 400, "end_ms": 1000, "raw_label": "A"}])
    # turns sorted by start: B -> SPK_0, A -> SPK_1
    assert assign_word_speaker(100, 300, turns) == "SPK_0"
    assert assign_word_speaker(450, 900, turns) == "SPK_1"      # more overlap with A
    assert assign_word_speaker(300, 600, turns) == "SPK_0"      # 200 vs 200 tie -> earliest turn start
    assert assign_word_speaker(2000, 2100, turns) is None       # no overlap
    assert assign_word_speaker(None, None, turns) is None       # unaligned
    assert assign_word_speaker(0, 100, []) is None


def test_overlapping_turns_preserved_not_merged():
    turns = build_turns([{"start_ms": 0, "end_ms": 1000, "raw_label": "A"},
                         {"start_ms": 500, "end_ms": 1500, "raw_label": "B"}])
    assert len(turns) == 2 and turns[0].end_ms > turns[1].start_ms


# ---------------- language gate -----------------------------------------------------------------

def _segs(n_words, start=0):
    return [{"start_ms": start, "end_ms": start + 1000, "text": " ".join(["word"] * n_words)}]


def test_language_gate_not_applicable_below_20_words():
    r = language_gate_v1(_segs(19), FakeLID("fr", 0.99), CFG)
    assert r.gate_status == "not_applicable" and r.sample_word_count == 19


def test_language_gate_pass_and_failures():
    assert language_gate_v1(_segs(20), FakeLID("en", 0.95), CFG).gate_status == "passed"
    # owner 2026-10-02 #3 (exact): non-en -> unsupported_language at ANY confidence; en & <0.90 -> uncertain
    with pytest.raises(StageFailure) as e:
        language_gate_v1(_segs(20), FakeLID("fr", 0.97), CFG)
    assert e.value.reason == "unsupported_language" and e.value.kind is FailureKind.PERMANENT_INPUT
    with pytest.raises(StageFailure) as e:
        language_gate_v1(_segs(20), FakeLID("fr", 0.50), CFG)
    assert e.value.reason == "unsupported_language"  # was language_uncertain under the earlier reading
    with pytest.raises(StageFailure) as e:
        language_gate_v1(_segs(20), FakeLID("en", 0.80), CFG)
    assert e.value.reason == "language_uncertain"
    assert language_gate_v1(_segs(20), FakeLID("en", 0.90), CFG).gate_status == "passed"  # boundary: >= 0.90


def test_language_sample_limited_to_first_60s_of_speech():
    segs = [{"start_ms": 10_000, "end_ms": 20_000, "text": "a b c"},
            {"start_ms": 69_999, "end_ms": 71_000, "text": "d e"},
            {"start_ms": 70_000, "end_ms": 72_000, "text": "NOT INCLUDED"}]
    words, _ = select_language_sample(segs, sample_s=60)
    assert words == ["a", "b", "c", "d", "e"]


def test_fasttext_artifact_must_be_provisioned_and_hash_verified(tmp_path):
    with pytest.raises(StageFailure) as e:
        FastTextLanguageID.from_provisioned_artifact("m", tmp_path)
    assert e.value.kind is FailureKind.BLOCKED_BY_DEPENDENCY and e.value.reason == "language_id_model_not_provisioned"
    (tmp_path / "lid.176.ftz").write_bytes(b"not a model")
    (tmp_path / "lid.176.ftz.sha256").write_text("0" * 64)
    with pytest.raises(StageFailure) as e:
        FastTextLanguageID.from_provisioned_artifact("m", tmp_path)
    assert e.value.reason == "language_id_model_checksum_mismatch"


def test_no_runtime_download_path_exists():
    src = Path("workers/cpu/language_gate.py").read_text()
    for forbidden in ("urlopen", "import requests", "import httpx", "urllib", "http://", "https://", "wget", "curl"):
        assert forbidden not in src


# ---------------- G3 / G7 / G8 -----------------------------------------------------------------

def test_runtime_contracts_are_frozen_by_the_owner_g3_decision():
    """2026-10-06: FROZEN with the owner's values; the identity hash is stable and content-addressed."""
    asr = CFG.runtime_contract("asr_runtime@1")
    assert (asr["software"], asr["execution"]["device"], asr["execution"]["compute_type"]) == (
        {"whisperx": "3.8.6", "faster_whisper": "1.2.1", "ctranslate2": "4.8.2"}, "cpu", "int8")
    assert asr["transcription"]["language"] is None and list(asr["transcription"]["temperatures"]) == [0.0]
    assert asr["runtime_downloads"] is False
    ali = CFG.runtime_contract("alignment_runtime@1")
    assert ali["model"]["model_id"] == "facebook/wav2vec2-base-960h" and ali["interpolation"]["method"] == "ignore"
    dia = CFG.runtime_contract("diarization_runtime@1")
    assert dia["model"]["revision"] == "3533c8cf8e369892e6b79ff1bf80f7b0286a54ee" and len(dia["model_files"]) == 5
    for n in ("asr_runtime@1", "alignment_runtime@1", "diarization_runtime@1"):
        assert len(CFG.runtime_contract_sha256(n)) == 64
    # software versions in the contracts equal the locked environment (no contract/lock drift)
    lock = Path("uv.lock").read_text()
    for pkg, key, contract in (("whisperx", "whisperx", asr), ("faster-whisper", "faster_whisper", asr),
                               ("ctranslate2", "ctranslate2", asr), ("pyannote-audio", "pyannote_audio", dia),
                               ("transformers", "transformers", ali), ("torch", "torch", ali)):
        ver = contract["software"][key]
        assert f'name = "{pkg}"\nversion = "{ver}"' in lock, (pkg, ver)


def test_runtime_contract_requires_every_field_when_frozen():
    import copy as cp

    from shorts_config import Config
    raw = cp.deepcopy(CFG._raw)
    c = raw["runtime_contracts"]["alignment_runtime@1"]
    c["status"], c["values"] = "FROZEN", {"model_id": "x"}
    with pytest.raises(ConfigSpecGap, match="missing required fields"):
        Config(raw).runtime_contract("alignment_runtime@1")
    c["values"] = {f: "v" for f in c["required_fields"]}
    assert Config(raw).runtime_contract_sha256("alignment_runtime@1")


def test_default_backends_never_guess_or_download(tmp_path):
    # frozen contracts + no materialized artifacts -> BLOCKED_BY_DEPENDENCY, never a download/guess
    with pytest.raises(StageFailure) as e:
        default_backends(CFG, root=tmp_path)
    assert e.value.kind is FailureKind.BLOCKED_BY_DEPENDENCY and e.value.reason == "vad_model_missing"
    import copy as cp

    from shorts_config import Config
    raw = cp.deepcopy(CFG._raw)
    raw["runtime_contracts"]["asr_runtime@1"]["status"] = "BLOCKED_BY_SPEC"
    with pytest.raises(BlockedBySpec, match="asr_runtime@1"):
        default_backends(Config(raw), root=tmp_path)


def test_pyproject_declares_pyannote_and_fasttext_and_lock_has_them():
    py = Path("pyproject.toml").read_text()
    assert "pyannote-audio" in py and '"fasttext"' in py
    lock = Path("uv.lock").read_text()
    assert 'name = "fasttext"' in lock and 'name = "pyannote-audio"' in lock


class _FakeResult:
    def __init__(self, id): self.id = id


class _FakeAsync:
    def __init__(self, state, result): self.state, self.result = state, result


class _FakeCelery:
    def __init__(self):
        self.sent, self.revoked, self.results = [], [], {}

        class _C:
            def revoke(_, tid, terminate=False): self.revoked.append(tid)
        self.control = _C()

    def send_task(self, name, kwargs, task_id, queue):
        self.sent.append((name, kwargs, task_id, queue))
        return _FakeResult(task_id)

    def AsyncResult(self, tid):
        return _FakeAsync(*self.results.get(tid, ("PENDING", None)))


@pytest.mark.asyncio
async def test_local_provider_uses_gpu_dispatch_and_opaque_job_id():
    app = _FakeCelery()
    p = LocalROCmGPUProvider(celery_app=app)
    h = await p.submit(task_name="asr", input_artifact_ids=("a",), model_manifest={},
                       config_identity=ConfigIdentity("config@1", SHA), request_id="req-1")
    assert app.sent[0][0] == "workers.gpu.execute_gpu_task" and app.sent[0][3] == "gpu_dispatch"
    assert app.sent[0][1]["transport_inputs"] == {}
    assert (await p.get_status(provider_job_id=h.provider_job_id)).state is GPUJobState.PENDING
    out = {"kind": "phase3_stage_output_v1", "stage": "asr", "schema_version": 1,
           "storage_location": "k", "checksum": SHA, "provenance": {}}
    app.results["req-1"] = ("SUCCESS", {"status": "ok", "outputs": [out]})
    st = await p.get_status(provider_job_id=h.provider_job_id)
    assert st.state is GPUJobState.SUCCEEDED and st.outputs[0].storage_location == "k"
    app.results["req-1"] = ("SUCCESS", {"status": "error", "kind": "PERMANENT_INPUT", "reason": "bad"})
    st = await p.get_status(provider_job_id=h.provider_job_id)
    assert st.state is GPUJobState.FAILED and st.failure_kind == "PERMANENT_INPUT"
    assert (await p.cancel(provider_job_id="req-1")).cancelled and app.revoked == ["req-1"]


def test_application_code_never_parses_provider_job_id():
    import re
    src = Path("workers/cpu/stage_transcript.py").read_text()
    assert "provider_job_id" in src  # passed through / stored only
    # no method call, indexing, slicing or conversion applied to the VALUE of an id
    assert not re.search(r"provider_job_id(\.\w+\(|\[|\s*\+)", src.replace("handle.provider_job_id", "ID"))
    assert not re.search(r"(int|uuid\.UUID|re\.\w+)\([^)]*provider_job_id", src)


def test_no_diarization_speaker_features_use_null_with_reason():
    from shorts_config import speaker_dependent_feature_v1
    assert speaker_dependent_feature_v1(0.4, diarization_available=False) == {"v": None, "m": "not_available_in_stage"}


def test_unused_backends_dataclass_default_is_all_none():
    assert Backends() == Backends(None, None, None)


# ---------------- 2026-10-02 #13: PTS-based CFR predicate ------------------------------------------
from fractions import Fraction

from workers.cpu.cfr import classify_cfr_v1


@pytest.mark.parametrize("fps,tb,delta", [
    (24, Fraction(1, 12288), 512), (25, Fraction(1, 12800), 512), (30, Fraction(1, 90000), 3000),
    (50, Fraction(1, 12800), 256), (60, Fraction(1, 90000), 1500)])
def test_cfr_eligible_rates_preserved(fps, tb, delta):
    d = classify_cfr_v1([i * delta for i in range(120)], tb)
    assert d.is_cfr and d.reason == "cfr_eligible" and d.selected_fps == fps and d.derived_fps == f"{fps}/1"


def test_cfr_ntsc_2997_is_not_eligible_normalizes_to_30():
    d = classify_cfr_v1([i * 1001 for i in range(100)], Fraction(1, 30000))
    assert not d.is_cfr and d.reason == "fps_not_eligible" and d.selected_fps == 30 and d.derived_fps == "30000/1001"


def test_cfr_variable_and_degenerate_cases():
    assert classify_cfr_v1([0, 33, 67, 100, 133], Fraction(1, 1000)).reason == "variable_deltas"  # ms-rounded 30 fps
    assert classify_cfr_v1([0, 3000, 3000, 6000], Fraction(1, 90000)).reason == "non_positive_delta"
    assert classify_cfr_v1([0, None, 6000], Fraction(1, 90000)).reason == "missing_pts"
    assert classify_cfr_v1([0], Fraction(1, 90000)).reason == "insufficient_frames"
    assert classify_cfr_v1([0, 1], None).reason == "insufficient_frames"
    assert classify_cfr_v1([0, 3000, 6000], Fraction(1, 90000)).selected_fps == 30


def test_cfr_is_in_presentation_order_not_decode_order():
    pts = [0, 6000, 3000, 12000, 9000]  # B-frame decode order, constant 3000 in presentation order
    assert classify_cfr_v1(pts, Fraction(1, 90000)).is_cfr


def test_cfr_never_uses_r_frame_rate():
    src = Path("workers/cpu/cfr.py").read_text()
    assert "r_frame_rate" not in src.replace("Not inferred from r_frame_rate", "")


def test_media_manifest_schema_requires_cfr_audio_presence_and_config_identity():
    schema = json.loads(Path("packages/schemas/json/media_manifest_v1.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    for f in ("cfr", "audio_presence", "config_sha256", "source", "normalized_video", "analysis_audio", "provenance",
              "orientation", "probe", "source_video_id", "stage_version", "schema_version"):
        assert f in schema["required"]
    from packages.schemas.python.media_manifest_v1 import MediaManifestV1  # generated
    assert MediaManifestV1


def test_transport_keys_are_not_artifact_keys():
    from workers.shared.artifact_keys import artifact_storage_key, transport_storage_key
    k = transport_storage_key(source_video_id=SV, stage="asr", sha256=SHA)
    assert k.startswith("transport/") and not k.startswith("artifacts/")
    assert artifact_storage_key(source_video_id=SV, artifact_type="media_manifest_v1",
                                artifact_id=SV, sha256=SHA).endswith(".json")


def test_gpu_worker_has_no_db_write_and_does_not_catch_unexpected_crashes():
    src = Path("workers/gpu/execute.py").read_text()
    assert "session.add" not in src and "session.execute" not in src and "Artifact(" not in src  # #7
    assert "except Exception" not in src and "PERMANENT_MODEL" not in src.split("except StageFailure")[1][:300]  # #5
    py = Path("workers/cpu/stage_transcript.py").read_text()
    assert "PERMANENT_MODEL" in py  # only for explicit 'no word received alignment'


def test_envelope_is_not_an_artifact_type_anywhere():
    for f in ("workers/cpu/stage_transcript.py",):
        src = Path(f).read_text()
        assert "NewArtifact(STAGE_OUTPUT_TYPE" not in src and 'artifact_type="phase3_stage_output' not in src
