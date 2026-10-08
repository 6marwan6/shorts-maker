"""G3 freeze (owner 2026-10-06): pure logic + adapter wiring against stub libraries. These tests prove the
adapters pass EXACTLY the frozen contract values to the (stubbed) libraries and never download; they do not
prove real-model behavior -- that is `make smoke-real`."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import types
from pathlib import Path

import pytest
from shorts_config import load_config

from workers.gpu import model_materialization as mm
from workers.gpu import real_backends as rb
from workers.shared.failures import FailureKind, StageFailure

CFG = load_config()
DICT = {c: i for i, c in enumerate(["<pad>", "<s>", "</s>", "<unk>", "|", "e", "t", "a", "o", "n", "i", "h", "s", "r", "d", "l", "u", "m", "w", "c", "f", "g", "y", "p", "b", "v", "k", "'", "x", "j", "q", "z"])}
DICT.update({ch: 100 + i for i, ch in enumerate("abcdefghijklmnopqrstuvwxyz'")})


# ---------------------------------------------------------------- pure logic
def test_asr_options_map_contract_names_to_whisperx_keys():
    o = rb.asr_options_from_contract(CFG.runtime_contract("asr_runtime@1")["transcription"])
    assert o["temperatures"] == [0.0] and "temperature" not in o and "temperature_increment_on_fallback" not in o
    assert (o["beam_size"], o["patience"], o["length_penalty"], o["condition_on_previous_text"]) == (5, 1.0, 1.0, False)
    assert (o["compression_ratio_threshold"], o["log_prob_threshold"], o["no_speech_threshold"]) == (2.4, -1.0, 0.6)
    assert o["initial_prompt"] is None and o["hotwords"] is None and "word_timestamps" not in o


@pytest.mark.parametrize("word,expected", [
    ("Here", False), ("price", False), ("2nd", False),  # has dictionary chars
    ("2026", True), ("$50", True), ("$", True), ("(!!!)", True), ("...", True), ("50%", True), ("U.S.", False)])
def test_wildcard_only_classification(word, expected):
    assert rb.is_wildcard_only(word, DICT) is expected


def _aw(text, s=None, e=None, score=None):
    d = {"word": text}
    if s is not None:
        d.update(start=s, end=e)
    if score is not None:
        d["score"] = score
    return d


def test_reconcile_nulls_missing_and_wildcard_timing_and_never_interpolates():
    asr = ["Buy", "it", "for", "$50", "in", "2026", "today."]
    aligned = [_aw("Buy", 0.0, 0.3, 0.9), _aw("it", 0.3, 0.4, 0.8), _aw("for"), _aw("$50", 1.0, 1.4, 0.7),
               _aw("in", 1.4, 1.5, 0.9), _aw("2026", 1.5, 2.0, 0.5), _aw("today.", 2.0, 2.6, 0.95)]
    w = rb.reconcile_words_v1(asr, aligned, DICT)
    assert [x["text"] for x in w] == asr
    t = {x["text"]: (x["start_ms"], x["end_ms"]) for x in w}
    assert t["Buy"] == (0, 300) and t["today."] == (2000, 2600)
    assert t["for"] == (None, None)       # no start/end (interpolate_method='ignore')
    assert t["$50"] == (None, None)       # wildcard-only: has a timestamp from whisperx but is NOT trusted
    assert t["2026"] == (None, None)
    assert [x["confidence"] for x in w if x["start_ms"] is None] == [None] * 3


def test_reconcile_reinserts_tokens_whisperx_dropped_without_timing():
    asr = ["alpha", "beta", "gamma", "delta"]
    aligned = [_aw("alpha", 0.0, 0.2, 1.0), _aw("delta", 5.0, 5.3, 1.0)]  # a whole segment failed to align
    w = rb.reconcile_words_v1(asr, aligned, DICT)
    assert [x["text"] for x in w] == asr
    assert [x["start_ms"] for x in w] == [0, None, None, 5000]  # text never lost; nothing borrowed or interpolated


def test_reconcile_one_sided_timing_is_unaligned():
    w = rb.reconcile_words_v1(["hi"], [{"word": "hi", "start": 0.1, "score": 0.9}], DICT)
    assert w[0]["start_ms"] is None and w[0]["end_ms"] is None


def test_turns_are_raw_and_overlaps_preserved():
    class Seg:
        def __init__(self, s, e): self.start, self.end = s, e

    class Ann:
        def itertracks(self, yield_label=False):
            yield Seg(0.0, 1.5), "t0", "SPEAKER_01"
            yield Seg(1.0, 2.0), "t1", "SPEAKER_00"
    assert rb.turns_from_annotation(Ann()) == [
        {"start_ms": 0, "end_ms": 1500, "raw_label": "SPEAKER_01"},
        {"start_ms": 1000, "end_ms": 2000, "raw_label": "SPEAKER_00"}]


# ---------------------------------------------------------------- materialization
def test_vendored_silero_is_the_owner_hash_and_is_verified():
    c = CFG.runtime_contract("asr_runtime@1")["vad"]
    f = Path("models/silero") / c["model_file"]
    assert hashlib.sha256(f.read_bytes()).hexdigest() == c["model_sha256"]
    assert mm.verify_vad(CFG, Path("models")) == f


def test_vad_checksum_mismatch_is_blocked_not_replaced(tmp_path):
    (tmp_path / "silero").mkdir()
    (tmp_path / "silero" / "silero_vad_v6.onnx").write_bytes(b"tampered")
    with pytest.raises(StageFailure) as e:
        mm.verify_vad(CFG, tmp_path)
    assert e.value.reason == "vad_checksum_mismatch" and e.value.kind is FailureKind.BLOCKED_BY_DEPENDENCY
    assert (tmp_path / "silero" / "silero_vad_v6.onnx").read_bytes() == b"tampered"  # never overwritten


def _materialize(tmp_path, cfg_raw, component, files: dict[str, bytes], resolved: str, extra=None):
    import copy as cp

    from shorts_config import Config
    raw = cp.deepcopy(cfg_raw)
    d = tmp_path / {"asr": mm.ASR_DIR, "alignment": mm.ALIGN_DIR, "diarization": mm.DIAR_DIR}[component]
    d.mkdir(parents=True)
    hashes = {}
    for rel, data in files.items():
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_bytes(data)
        hashes[rel] = hashlib.sha256(data).hexdigest()
    (d / mm.MANIFEST).write_text(json.dumps({"repository": "r", "requested_revision": "x", "resolved_revision": resolved, "files": hashes}))
    return raw, Config, hashes, d


def test_asr_materialization_requires_resolved_40hex_commit_and_weights_hash(tmp_path):
    raw, Config, hashes, d = _materialize(tmp_path, CFG._raw, "asr", {"model.bin": b"w", "config.json": b"{}"},
                                          resolved="0c94664" + "0" * 33)
    raw["runtime_contracts"]["asr_runtime@1"]["values"]["model"]["model_weights_sha256"] = hashes["model.bin"]
    cfg = Config(raw)
    m = mm.verify_asr(cfg, tmp_path)
    assert m.resolved_revision == "0c94664" + "0" * 33 and m.requested_revision == "0c94664"
    (d / mm.MANIFEST).write_text(json.dumps({"resolved_revision": "0c94664", "files": hashes}))  # short, not resolved
    with pytest.raises(StageFailure, match="asr_model_revision_unresolved"):
        mm.verify_asr(cfg, tmp_path)
    (d / mm.MANIFEST).write_text(json.dumps({"resolved_revision": "ffffffff" + "0" * 32, "files": hashes}))  # wrong commit
    with pytest.raises(StageFailure, match="asr_model_revision_unresolved"):
        mm.verify_asr(cfg, tmp_path)
    (d / mm.MANIFEST).write_text(json.dumps({"resolved_revision": "0c94664" + "0" * 33, "files": hashes}))
    (d / "model.bin").write_bytes(b"corrupt")
    with pytest.raises(StageFailure, match="asr_model_checksum_mismatch"):
        mm.verify_asr(cfg, tmp_path)


def test_alignment_and_diarization_check_revision_and_every_pinned_file(tmp_path):
    ali = CFG.runtime_contract("alignment_runtime@1")["model"]
    raw, Config, hashes, d = _materialize(tmp_path, CFG._raw, "alignment", {"model.safetensors": b"s", "vocab.json": b"{}"},
                                          resolved=ali["revision"])
    raw["runtime_contracts"]["alignment_runtime@1"]["values"]["model"]["weights_sha256"] = hashes["model.safetensors"]
    assert mm.verify_alignment(Config(raw), tmp_path).resolved_revision == ali["revision"]
    (d / "vocab.json").write_bytes(b"changed")  # an UNPINNED recorded file must still match its recorded hash
    with pytest.raises(StageFailure, match="alignment_model_recorded_file_mismatch"):
        mm.verify_alignment(Config(raw), tmp_path)
    dia = CFG.runtime_contract("diarization_runtime@1")
    files = {rel: rel.encode() for rel in dia["model_files"]}
    raw2, Config, hashes2, _ = _materialize(tmp_path, CFG._raw, "diarization", files, resolved=dia["model"]["revision"])
    raw2["runtime_contracts"]["diarization_runtime@1"]["values"]["model_files"] = hashes2
    assert mm.verify_diarization(Config(raw2), tmp_path)
    with pytest.raises(StageFailure, match="diarization_model_checksum_mismatch"):
        mm.verify_diarization(CFG, tmp_path)  # real contract hashes != the fake bytes


def test_punkt_tab_must_be_provisioned_never_downloaded(tmp_path):
    with pytest.raises(StageFailure, match="nltk_punkt_tab_not_provisioned"):
        mm.verify_punkt(tmp_path)
    d = tmp_path / "nltk_data/tokenizers/punkt_tab/english"
    d.mkdir(parents=True)
    (d / "collocations.tab").write_text("x")
    assert list(mm.verify_punkt(tmp_path)) == ["collocations.tab"]


def test_enforce_offline_sets_env_and_blocks_nltk_download(monkeypatch):
    nltk = types.ModuleType("nltk")
    nltk.download = lambda *a, **k: "downloaded"
    monkeypatch.setitem(sys.modules, "nltk", nltk)
    for k in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE"):
        monkeypatch.delenv(k, raising=False)
    rb.enforce_offline()
    assert all(os.environ[k] == "1" for k in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE"))
    with pytest.raises(StageFailure, match="runtime_download_forbidden"):
        nltk.download("punkt_tab")


# ---------------------------------------------------------------- adapter wiring against stub libraries
def _stub(monkeypatch, **mods):
    for name, mod in mods.items():
        monkeypatch.setitem(sys.modules, name, mod)


def _fake_models(monkeypatch, tmp_path):
    def mat(component, repo, rev):
        return mm.MaterializedModel(component, tmp_path / component, repo, rev, rev, {})
    monkeypatch.setattr(mm, "verify_vad", lambda cfg, root: Path("models/silero/silero_vad_v6.onnx"))
    monkeypatch.setattr(mm, "verify_asr", lambda cfg, root: mat("asr", "mobiuslabsgmbh/faster-whisper-large-v3-turbo", "0c94664" + "1" * 33))
    monkeypatch.setattr(mm, "verify_alignment", lambda cfg, root: mat("alignment", "facebook/wav2vec2-base-960h", "22aad52d435eb6dbaf354bdad9b0da84ce7d6156"))
    monkeypatch.setattr(mm, "verify_diarization", lambda cfg, root: mat("diarization", "pyannote/speaker-diarization-community-1", "3533c8cf8e369892e6b79ff1bf80f7b0286a54ee"))
    monkeypatch.setattr(mm, "verify_punkt", lambda root: {"x": "y"})
    monkeypatch.setattr(rb, "enforce_offline", lambda: None)


def test_whisperx_asr_receives_exactly_the_frozen_contract(monkeypatch, tmp_path):
    _fake_models(monkeypatch, tmp_path)
    seen = {}

    class Pipe:
        def transcribe(self, audio, **kw):
            seen["transcribe"] = kw
            return {"language": "fr", "segments": [{"start": 0.0, "end": 1.0, "text": " bonjour tout le monde "}]}
    wx = types.ModuleType("whisperx")
    wx.load_model = lambda *a, **kw: (seen.update(args=a, load=kw), Pipe())[1]
    wx.load_audio = lambda p: [0.0]
    monkeypatch.setattr(rb, "VendoredSileroV6Vad", lambda path, opts: ("VAD", str(path), opts["threshold"]))
    _stub(monkeypatch, whisperx=wx)
    asr = rb.WhisperXASR(CFG, tmp_path)
    segs = asr.transcribe(Path("x.wav"))
    assert segs == [{"start_ms": 0, "end_ms": 1000, "text": "bonjour tout le monde"}] and asr.last_language == "fr"
    assert seen["args"] == (str(tmp_path / "asr"), "cpu")
    kw = seen["load"]
    assert (kw["compute_type"], kw["threads"], kw["language"], kw["task"], kw["local_files_only"]) == ("int8", 8, None, "transcribe", True)
    assert kw["asr_options"]["temperatures"] == [0.0] and kw["vad_model"][0] == "VAD"
    assert seen["transcribe"] == {"batch_size": 1, "language": None, "task": "transcribe", "chunk_size": 30}
    assert asr.models["vad"]["sha256"] == CFG.runtime_contract("asr_runtime@1")["vad"]["model_sha256"]
    assert asr.models["asr"]["revision"] == "0c94664" + "1" * 33 and len(asr.runtime_sha256) == 64


def test_aligner_uses_local_model_ignore_interpolation_and_reconciles(monkeypatch, tmp_path):
    _fake_models(monkeypatch, tmp_path)
    seen = {}
    wx = types.ModuleType("whisperx")
    wx.load_align_model = lambda lang, dev, **kw: (seen.update(load=(lang, dev, kw)), ("MODEL", {"dictionary": DICT}))[1]
    wx.load_audio = lambda p: [0.0]
    wx.align = lambda tr, model, meta, audio, dev, **kw: (seen.update(align=(tr, dev, kw)), {
        "word_segments": [_aw("hello", 0.0, 0.4, 0.9), _aw("2026", 0.5, 0.9, 0.2)]})[1]
    _stub(monkeypatch, whisperx=wx)
    al = rb.WhisperXAligner(CFG, tmp_path)
    out = al.align(Path("x.wav"), [{"start_ms": 0, "end_ms": 1000, "text": "hello 2026"}])
    assert seen["load"] == ("en", "cuda:0", {"model_name": str(tmp_path / "alignment"), "model_dir": None, "model_cache_only": True})
    tr, dev, kw = seen["align"]
    assert kw == {"interpolate_method": "ignore", "return_char_alignments": False} and dev == "cuda:0"
    assert tr == [{"text": "hello 2026", "start": 0.0, "end": 1.0}]
    assert [(w["text"], w["start_ms"]) for w in out] == [("hello", 0), ("2026", None)]


def test_diarizer_loads_offline_config_and_uses_the_non_exclusive_annotation(monkeypatch, tmp_path):
    _fake_models(monkeypatch, tmp_path)
    seen = {}

    class Ann:
        def itertracks(self, yield_label=False):
            class S:
                start, end = 0.0, 2.0
            yield S(), "t", "SPEAKER_00"

    class Out:
        speaker_diarization = Ann()
        exclusive_speaker_diarization = None  # must NOT be used (exclusive_diarization: false)

    class Pipeline:
        @classmethod
        def from_pretrained(cls, p):
            seen["path"] = p
            return cls()

        def to(self, dev):
            seen["device"] = str(dev)
            return self

        def __call__(self, f, **kw):
            seen["kw"] = kw
            return Out()
    torch = types.ModuleType("torch")
    torch.device = lambda d: d
    torch.from_numpy = lambda a: types.SimpleNamespace(unsqueeze=lambda i: "WAVE")
    pyannote = types.ModuleType("pyannote")
    audio = types.ModuleType("pyannote.audio")
    audio.Pipeline = Pipeline
    wx = types.ModuleType("whisperx")
    wx.load_audio = lambda p: [0.0]
    _stub(monkeypatch, torch=torch, pyannote=pyannote, **{"pyannote.audio": audio}, whisperx=wx)
    d = rb.PyannoteDiarizer(CFG, tmp_path)
    assert d.diarize(Path("x.wav")) == [{"start_ms": 0, "end_ms": 2000, "raw_label": "SPEAKER_00"}]
    assert seen["path"] == str(tmp_path / "diarization" / "config.yaml") and seen["device"] == "cuda:0"
    assert seen["kw"] == {"num_speakers": None, "min_speakers": None, "max_speakers": None}


def test_real_backends_module_imports_without_torch_and_never_uses_hub_vad():
    src = Path("workers/gpu/real_backends.py").read_text()
    for forbidden in ("torch.hub", "snakers4", "snapshot_download", "hf_hub_download", "urlopen", "requests."):
        assert forbidden not in src
    assert "interpolate_method=self._c[\"interpolation\"][\"method\"]" in src
    assert "from_pretrained(str(self.model.path / \"config.yaml\"))" in src
