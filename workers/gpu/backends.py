"""Model-backend boundary for worker-gpu (impl plan Phase 3 3.1/3.2/3.4/3.6).

Protocols and the default factory live here; the concrete WhisperX / pyannote adapters are in
workers/gpu/real_backends.py (owner G3 freeze 2026-10-06). `default_backends()` is BLOCKED_BY_SPEC
while a runtime contract is not FROZEN and BLOCKED_BY_DEPENDENCY while a model artifact is missing
or fails its SHA-256 check -- it never guesses and never downloads. Tests inject fakes."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from shorts_config import Config, ConfigSpecGap

from workers.shared.failures import BlockedBySpec


class ASRBackend(Protocol):
    runtime_id: str
    runtime_sha256: str | None
    model_id: str
    model_revision: str | None
    model_sha256: str | None
    models: dict

    def transcribe(self, audio_path: Path) -> list[dict]:
        """-> [{start_ms, end_ms, text}] coarse segments (alignment input only)."""
        ...


class AlignmentBackend(Protocol):
    runtime_id: str
    runtime_sha256: str | None
    model_id: str
    model_revision: str | None
    model_sha256: str | None
    models: dict

    def align(self, audio_path: Path, segments: Sequence[dict]) -> list[dict]:
        """-> [{text, start_ms|None, end_ms|None, confidence|None}]; unaligned words keep text, null timing."""
        ...


class DiarizationBackend(Protocol):
    runtime_id: str
    runtime_sha256: str | None
    model_id: str
    model_revision: str | None
    model_sha256: str | None
    models: dict

    def diarize(self, audio_path: Path) -> list[dict]:
        """-> raw turns [{start_ms, end_ms, raw_label}] exactly as the provider returned them."""
        ...


@dataclass(frozen=True)
class Backends:
    asr: ASRBackend | None = None
    alignment: AlignmentBackend | None = None
    diarization: DiarizationBackend | None = None


def default_backends(cfg: Config, root=None) -> Backends:
    """Real backends (owner 2026-10-06 G3 freeze). BLOCKED_BY_SPEC while a runtime contract is not
    FROZEN; BLOCKED_BY_DEPENDENCY (raised by the adapters) while any model artifact is missing or
    fails its SHA-256 check. Never a guess, never a download."""
    blocked: list[str] = []
    for name in ("asr_runtime@1", "alignment_runtime@1", "diarization_runtime@1"):
        try:
            cfg.runtime_contract(name)
        except ConfigSpecGap as exc:
            blocked.append(str(exc))
    if blocked:
        raise BlockedBySpec("; ".join(blocked))
    from workers.gpu import model_materialization as mm
    from workers.gpu.real_backends import PyannoteDiarizer, WhisperXAligner, WhisperXASR
    r = mm.models_root(root)
    return Backends(asr=WhisperXASR(cfg, r), alignment=WhisperXAligner(cfg, r), diarization=PyannoteDiarizer(cfg, r))
