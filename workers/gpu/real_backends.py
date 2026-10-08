"""Real WhisperX / pyannote adapters (owner decision 2026-10-06, G3 freeze).

STATUS: written against the frozen asr_runtime@1 / alignment_runtime@1 / diarization_runtime@1 and
the pinned library sources (whisperx 3.8.6, faster-whisper 1.2.1, pyannote-audio 4.0.7) but NOT yet
run against real models in the dev sandbox (no GPU, no model files, no network). The Phase 3 exit
gate is `make smoke-real`. Libraries are imported lazily so this module imports without torch.

Rules enforced here: nothing is downloaded (offline env + nltk.download blocked); every artifact is
re-verified by workers.gpu.model_materialization before it is loaded; no word timing is ever
interpolated or kept when it came from the wildcard path (owner G4 + 2026-10-06 section 2).
"""
from __future__ import annotations

import difflib
import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from shorts_config import Config

from workers.gpu import model_materialization as mm
from workers.shared.failures import FailureKind, StageFailure

SAMPLE_RATE = 16000


def enforce_offline() -> None:
    """runtime_downloads: false. Hugging Face / transformers / datasets offline; nltk cannot download."""
    for k in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE"):
        os.environ[k] = "1"
    try:
        import nltk
    except ImportError:
        return

    def _no_download(*a, **k):
        raise StageFailure(FailureKind.BLOCKED_BY_DEPENDENCY, "runtime_download_forbidden", "nltk.download blocked")
    nltk.download = _no_download  # type: ignore[assignment]


# ------------------------------------------------------------------------------------ pure logic
def asr_options_from_contract(t: dict) -> dict:
    """Contract field names -> whisperx `asr_options` keys. Only keys the owner froze are passed;
    everything else is whisperx 3.8.6's default (listed in config@1 as observed, unconfirmed)."""
    return {
        "beam_size": t["beam_size"], "temperatures": list(t["temperatures"]),
        "condition_on_previous_text": t["condition_on_previous_text"], "patience": t["patience"],
        "length_penalty": t["length_penalty"], "compression_ratio_threshold": t["compression_ratio_threshold"],
        "log_prob_threshold": t["log_prob_threshold"], "no_speech_threshold": t["no_speech_threshold"],
        "initial_prompt": t["initial_prompt"], "hotwords": t["hotwords"],
    }


def is_wildcard_only(word: str, dictionary: dict) -> bool:
    """True when EVERY non-space character of the word is outside the alignment model's dictionary
    (digits, currency, punctuation...). whisperx 3.8.6 gives such characters a wildcard emission
    (max non-blank score per frame), so their timing is not character-level alignment evidence."""
    chars = [c.lower() for c in word if not c.isspace()]
    return bool(chars) and all(c not in dictionary and c != "|" for c in chars)


def _clean(tok: str) -> str:
    return tok.strip()


def reconcile_words_v1(asr_tokens: Sequence[str], aligned: Sequence[dict], dictionary: dict) -> list[dict]:
    """Authoritative words for transcript_v1 (owner G4):
      * word with real start AND end, not wildcard-only -> keeps its timing;
      * word lacking start/end (interpolate_method='ignore') or wildcard-only -> text kept, timing None;
      * ASR tokens that whisperx dropped entirely (e.g. a segment that failed to align) are re-inserted
        with null timing, so transcript text is never lost. Matching is by token sequence.
    Never interpolates and never borrows coarse ASR segment timing."""
    a_tokens = [_clean(w["word"]) for w in aligned]
    sm = difflib.SequenceMatcher(a=list(asr_tokens), b=a_tokens, autojunk=False)
    out: list[dict] = []

    def emit_aligned(w: dict) -> None:
        text = _clean(w["word"])
        s, e = w.get("start"), w.get("end")
        usable = s is not None and e is not None and not is_wildcard_only(text, dictionary)
        out.append({
            "text": text,
            "start_ms": round(float(s) * 1000) if usable else None,
            "end_ms": round(float(e) * 1000) if usable else None,
            "confidence": float(w["score"]) if usable and w.get("score") is not None else None,
        })

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("equal", "replace"):
            for w in aligned[j1:j2]:
                emit_aligned(w)
            if tag == "replace" and (i2 - i1) > (j2 - j1):  # fewer aligned tokens than ASR tokens
                for tok in asr_tokens[i1 + (j2 - j1): i2]:
                    out.append({"text": _clean(tok), "start_ms": None, "end_ms": None, "confidence": None})
        elif tag == "delete":  # ASR token with no aligned counterpart -> untimed
            for tok in asr_tokens[i1:i2]:
                out.append({"text": _clean(tok), "start_ms": None, "end_ms": None, "confidence": None})
        elif tag == "insert":  # aligned token ASR text did not have (should not happen) -> keep, as aligned
            for w in aligned[j1:j2]:
                emit_aligned(w)
    return [w for w in out if w["text"]]


def turns_from_annotation(annotation) -> list[dict]:
    """Raw pyannote turns exactly as returned (owner G5): no merging, no minimum duration."""
    turns = []
    for segment, _track, label in annotation.itertracks(yield_label=True):
        turns.append({"start_ms": round(segment.start * 1000), "end_ms": round(segment.end * 1000),
                      "raw_label": str(label)})
    return turns


# ------------------------------------------------------------------------------------ VAD
class VendoredSileroV6Vad:
    """whisperx `Vad`-compatible wrapper around the vendored, hash-verified silero_vad_v6.onnx.
    Uses faster-whisper's own get_speech_timestamps with its VadOptions (frozen values from
    asr_runtime@1) and swaps in a SileroVADModel built from the VERIFIED file -- never the hub."""

    def __init__(self, model_path: Path, options: dict):
        from faster_whisper import vad as fw_vad
        from whisperx.vads.vad import Vad
        self._fw_vad, self._Vad = fw_vad, Vad
        self._model = fw_vad.SileroVADModel(str(model_path))
        self.options = fw_vad.VadOptions(
            threshold=options["threshold"], min_speech_duration_ms=options["min_speech_duration_ms"],
            max_speech_duration_s=options["max_speech_duration_s"],
            min_silence_duration_ms=options["min_silence_duration_ms"], speech_pad_ms=options["speech_pad_ms"])
        Vad.__init__(self, options["threshold"])

    # whisperx calls these on the instance
    @staticmethod
    def preprocess_audio(audio):
        return audio

    @staticmethod
    def merge_chunks(segments, chunk_size, onset, offset):
        from whisperx.vads.vad import Vad
        if not segments:
            return []
        return Vad.merge_chunks(segments, chunk_size, onset, offset)

    def __call__(self, audio_in):
        import numpy as np
        from pyannote.core import Segment
        wave = audio_in["waveform"]
        audio = np.asarray(wave, dtype=np.float32).reshape(-1)
        original = self._fw_vad.get_vad_model
        self._fw_vad.get_vad_model = lambda: self._model  # the verified file, not the packaged asset
        try:
            stamps = self._fw_vad.get_speech_timestamps(audio, self.options, sampling_rate=SAMPLE_RATE)
        finally:
            self._fw_vad.get_vad_model = original
        segs = []
        for s in stamps:
            seg = Segment(s["start"] / SAMPLE_RATE, s["end"] / SAMPLE_RATE)
            segs.append(_SegmentX(seg.start, seg.end))
        return segs


@dataclass
class _SegmentX:
    start: float
    end: float
    speaker: str | None = None


# ------------------------------------------------------------------------------------ backends
class WhisperXASR:
    """asr_runtime@1: CPU / CTranslate2 int8, VAD vendored Silero v6, language auto-detected."""

    def __init__(self, cfg: Config, root: Path):
        enforce_offline()
        c = cfg.runtime_contract("asr_runtime@1")
        self.runtime_id = c["runtime_version"]
        self.runtime_sha256 = cfg.runtime_contract_sha256("asr_runtime@1")
        vad_path = mm.verify_vad(cfg, root)
        self.model = mm.verify_asr(cfg, root)
        self.model_id, self.model_revision = self.model.repository, self.model.resolved_revision
        self.model_sha256 = c["model"]["model_weights_sha256"]
        self.models = {"asr": self.model.manifest_entry(self.model_sha256),
                       "vad": {"model_id": "silero_vad_v6.onnx", "revision": None, "sha256": c["vad"]["model_sha256"]}}
        self._c, self._pipeline, self._vad_path = c, None, vad_path
        self.last_language: str | None = None  # language whisper detected for the last audio (not forced)

    def _load(self):
        if self._pipeline is None:
            import whisperx
            c = self._c
            vad = VendoredSileroV6Vad(self._vad_path, c["vad"])
            self._pipeline = whisperx.load_model(
                str(self.model.path), c["execution"]["device"], compute_type=c["execution"]["compute_type"],
                asr_options=asr_options_from_contract(c["transcription"]),
                language=c["transcription"]["language"], vad_model=vad, task=c["transcription"]["task"],
                local_files_only=True, threads=c["execution"]["cpu_threads"])
        return self._pipeline

    def transcribe(self, audio_path: Path) -> list[dict]:
        import whisperx
        c = self._c
        audio = whisperx.load_audio(str(audio_path))
        out = self._load().transcribe(
            audio, batch_size=c["execution"]["batch_size"], language=c["transcription"]["language"],
            task=c["transcription"]["task"], chunk_size=c["vad"]["max_speech_duration_s"])
        self.last_language = out.get("language")
        return [{"start_ms": round(s["start"] * 1000), "end_ms": round(s["end"] * 1000),
                 "text": s["text"].strip()} for s in out["segments"] if s["text"].strip()]


class WhisperXAligner:
    """alignment_runtime@1: facebook/wav2vec2-base-960h (HF CTC), interpolate_method='ignore'."""

    def __init__(self, cfg: Config, root: Path):
        enforce_offline()
        c = cfg.runtime_contract("alignment_runtime@1")
        self.runtime_id = c["runtime_version"]
        self.runtime_sha256 = cfg.runtime_contract_sha256("alignment_runtime@1")
        self.model = mm.verify_alignment(cfg, root)
        self.punkt_sha256 = mm.verify_punkt(root)  # recorded, not pinned (gap flagged)
        os.environ["NLTK_DATA"] = str(root / mm.NLTK_DIR)
        self.model_id, self.model_revision = self.model.repository, self.model.resolved_revision
        self.model_sha256 = c["model"]["weights_sha256"]
        self.models = {"alignment": self.model.manifest_entry(self.model_sha256)}
        self._c, self._loaded = c, None

    def _load(self):
        if self._loaded is None:
            import whisperx
            self._loaded = whisperx.load_align_model(
                self._c["language"], self._c["execution"]["device"], model_name=str(self.model.path),
                model_dir=None, model_cache_only=True)
        return self._loaded

    def align(self, audio_path: Path, segments: Sequence[dict]) -> list[dict]:
        import whisperx
        model, metadata = self._load()
        audio = whisperx.load_audio(str(audio_path))
        transcript = [{"text": s["text"], "start": s["start_ms"] / 1000.0, "end": s["end_ms"] / 1000.0} for s in segments]
        result = whisperx.align(
            transcript, model, metadata, audio, self._c["execution"]["device"],
            interpolate_method=self._c["interpolation"]["method"], return_char_alignments=False)
        aligned = result["word_segments"]
        asr_tokens = [t for s in segments for t in s["text"].split()]
        return reconcile_words_v1(asr_tokens, aligned, metadata["dictionary"])


class PyannoteDiarizer:
    """diarization_runtime@1: official community-1 bundle, offline, non-exclusive diarization."""

    def __init__(self, cfg: Config, root: Path):
        enforce_offline()
        c = cfg.runtime_contract("diarization_runtime@1")
        self.runtime_id = c["runtime_version"]
        self.runtime_sha256 = cfg.runtime_contract_sha256("diarization_runtime@1")
        self.model = mm.verify_diarization(cfg, root)
        self.model_id, self.model_revision = c["model"]["model_id"], c["model"]["revision"]
        self.model_sha256 = c["model_files"]["config.yaml"]
        self.models = {"diarization": {"model_id": self.model_id, "revision": self.model_revision, "sha256": None}}
        self._c, self._pipeline = c, None

    def _load(self):
        if self._pipeline is None:
            import torch
            from pyannote.audio import Pipeline
            p = Pipeline.from_pretrained(str(self.model.path / "config.yaml"))
            self._pipeline = p.to(torch.device(self._c["execution"]["device"]))
        return self._pipeline

    def diarize(self, audio_path: Path) -> list[dict]:
        import torch
        import whisperx
        pipe, p = self._load(), self._c["pipeline"]
        wave = torch.from_numpy(whisperx.load_audio(str(audio_path))).unsqueeze(0)
        output = pipe({"waveform": wave, "sample_rate": SAMPLE_RATE},
                      num_speakers=p["num_speakers"], min_speakers=p["min_speakers"], max_speakers=p["max_speakers"])
        # exclusive_diarization: false -> the NON-exclusive annotation (overlapping speech preserved)
        return turns_from_annotation(output.speaker_diarization)
