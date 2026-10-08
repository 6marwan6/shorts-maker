"""language_gate_v1 (v5.0 2.14; impl plan 3.3; owner decision G8).

Runs AFTER ASR and BEFORE forced alignment. Input = coarse ASR segments (used only to window the
language sample -- never as cut timing). Model = the vendored fastText `lid.176.ftz`, verified
against its SHA-256 sidecar; there is no runtime download and no substitute model.

Result mapping (owner decision 2026-10-02 #3, exact):
  * fewer than LANGUAGE_MIN_WORDS words                      -> not_applicable
  * language_code != "en" (any confidence)                   -> unsupported_language
  * language_code == "en" and confidence < LANGUAGE_CONF_MIN -> language_uncertain
  * language_code == "en" and confidence >= LANGUAGE_CONF_MIN -> passed
No other failure reason exists.

Sample (owner #2): the ASR evidence whose timestamps fall in [first detected ASR speech onset,
onset + LANGUAGE_SAMPLE_S). Runs after ASR, never waits for forced alignment.
"""
from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from shorts_config import Config

from workers.shared.failures import FailureKind, StageFailure

DEFAULT_MODEL_DIR = Path(__file__).resolve().parents[2] / "models" / "fasttext"
MODEL_FILENAME = "lid.176.ftz"


class LanguageIDBackend(Protocol):
    model_id: str
    model_sha256: str | None

    def predict(self, text: str) -> tuple[str, float]:
        """Return (language_code, confidence) for the top label, e.g. ("en", 0.98)."""
        ...


@dataclass(frozen=True)
class LanguageGateResult:
    gate_status: str  # "passed" | "not_applicable"
    code: str | None
    confidence: float | None
    model_id: str
    model_sha256: str | None
    sample_word_count: int


FASTTEXT_ADAPTER_VERSION = "fasttext_predict_v1"
CONTRACT_CHECK_TEXT = "The quick brown fox jumps over the lazy dog while the sun sets over the quiet river."
CONTRACT_CHECK_EXPECTED_CODE = "en"


def fasttext_predict_v1(model, text: str) -> tuple[str, float]:
    """Versioned compatibility adapter (owner decision 2026-10-04 #1). INFRASTRUCTURE ONLY.

    The official `fasttext` wrapper's `FastText.predict()` ends with `np.array(probs, copy=False)`,
    which raises under numpy >= 2 (required by pyannote-audio 4.x and the pinned whisperx stack).
    The wrapper's own first step is `self.f.predict(text, k, threshold, on_unicode_error)` on the
    pybind model; this adapter performs exactly that call and converts the returned
    (probability, label) pair itself. It never calls `model.predict()`.

    Deliberately narrow: top-1 only (k=1, threshold 0.0, strict unicode), no training, no batch
    API -- NOT a general replacement for the fastText Python API.
    Returns (language_code, confidence) as plain Python scalars.
    """
    if "\n" in text:  # same precondition the wrapper enforces
        raise ValueError("fasttext_predict_v1: predict processes one line at a time (remove '\\n')")
    pairs = model.f.predict(text, 1, 0.0, "strict")
    if not pairs:
        raise StageFailure(FailureKind.PERMANENT_MODEL, "language_id_empty_prediction")
    prob, label = pairs[0]
    conf = float(prob)
    if not math.isfinite(conf):
        raise StageFailure(FailureKind.PERMANENT_MODEL, "language_id_non_finite_confidence", repr(prob))
    return str(label).removeprefix("__label__"), min(1.0, max(0.0, conf))


class FastTextLanguageID:
    """Loads the provisioned artifact; never touches the network. Prediction goes ONLY through
    `fasttext_predict_v1` (never `model.predict()`)."""

    adapter_version = FASTTEXT_ADAPTER_VERSION

    def __init__(self, model_id: str, model_sha256: str, model, *, sha256_verified: bool = False):
        self.model_id, self.model_sha256, self._model = model_id, model_sha256, model
        self.sha256_verified = sha256_verified  # True only if THIS loader hashed the file before loading it
        self.adapter_calls = 0

    @classmethod
    def from_provisioned_artifact(cls, model_id: str, model_dir: Path | str = DEFAULT_MODEL_DIR):
        model_dir = Path(model_dir)
        model_path, sidecar = model_dir / MODEL_FILENAME, model_dir / f"{MODEL_FILENAME}.sha256"
        if not model_path.is_file() or not sidecar.is_file():
            raise StageFailure(
                FailureKind.BLOCKED_BY_DEPENDENCY, "language_id_model_not_provisioned",
                f"{model_path} and {sidecar} must both exist (owner decision G8)")
        expected = sidecar.read_text().split()[0].strip().lower()
        h = hashlib.sha256()
        with open(model_path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        if h.hexdigest() != expected:  # verified BEFORE the model is loaded
            raise StageFailure(
                FailureKind.BLOCKED_BY_DEPENDENCY, "language_id_model_checksum_mismatch",
                f"expected {expected}, got {h.hexdigest()}")
        try:
            import fasttext  # type: ignore[import-not-found]
        except ImportError as exc:
            raise StageFailure(FailureKind.BLOCKED_BY_DEPENDENCY, "fasttext_not_installed", str(exc)) from exc
        backend = cls(model_id, expected, fasttext.load_model(str(model_path)), sha256_verified=True)
        backend.contract_check()  # mandatory startup check (owner 2026-10-04 #1): fail closed
        return backend

    def predict(self, text: str) -> tuple[str, float]:
        self.adapter_calls += 1
        return fasttext_predict_v1(self._model, text.replace("\n", " "))

    def contract_check(self) -> tuple[str, float]:
        """One deterministic prediction: shape, finite confidence, checksum verified, adapter used."""
        before = self.adapter_calls
        code, conf = self.predict(CONTRACT_CHECK_TEXT)
        problems = []
        if not self.sha256_verified:
            problems.append("sha256_not_verified")
        if self.adapter_calls != before + 1:
            problems.append("adapter_not_used")
        if not (isinstance(code, str) and code and isinstance(conf, float) and math.isfinite(conf) and 0.0 <= conf <= 1.0):
            problems.append("bad_result_shape")
        if code != CONTRACT_CHECK_EXPECTED_CODE:
            problems.append(f"unexpected_language:{code}")
        if problems:
            raise StageFailure(FailureKind.BLOCKED_BY_DEPENDENCY, "language_id_contract_check_failed", ",".join(problems))
        return code, conf


def select_language_sample(segments: Sequence[dict], *, sample_s: int) -> tuple[list[str], str]:
    """Words of the ASR segments whose start lies in [onset, onset + sample_s), onset = the first
    segment's start. Coarse ASR timing bounds the sample only; it is never a cut anchor."""
    if not segments:
        return [], ""
    ordered = sorted(segments, key=lambda s: (s["start_ms"], s["end_ms"]))
    origin = ordered[0]["start_ms"]
    words: list[str] = []
    for seg in ordered:
        if seg["start_ms"] - origin >= sample_s * 1000:
            break
        words.extend(seg["text"].split())
    return words, " ".join(words)


def language_gate_v1(segments: Sequence[dict], backend: LanguageIDBackend, cfg: Config) -> LanguageGateResult:
    words, text = select_language_sample(segments, sample_s=cfg["LANGUAGE_SAMPLE_S"])
    model_id = cfg["LANGUAGE_ID_MODEL_ID"]
    if len(words) < cfg["LANGUAGE_MIN_WORDS"]:
        return LanguageGateResult("not_applicable", None, None, model_id, backend.model_sha256, len(words))
    code, conf = backend.predict(text)
    if code != "en":
        raise StageFailure(FailureKind.PERMANENT_INPUT, "unsupported_language", f"{code} ({conf:.3f})")
    if conf < cfg["LANGUAGE_CONF_MIN"]:
        raise StageFailure(FailureKind.PERMANENT_INPUT, "language_uncertain", f"{code} ({conf:.3f})")
    return LanguageGateResult("passed", code, conf, model_id, backend.model_sha256, len(words))
