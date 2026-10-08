"""Local immutable model directory + hash verification (owner decision 2026-10-06, G3 sections 1-5).

`runtime_downloads: false` in every runtime contract: nothing here, and nothing in the adapters,
touches the network. Artifacts are provisioned ahead of time by `scripts/materialize_models.py`
(a provisioning tool run by a person with network access) into

    <models_root>/
      silero/silero_vad_v6.onnx(+.sha256)                       vendored in git
      whisper/faster-whisper-large-v3-turbo/ (+ materialization.json)
      alignment/wav2vec2-base-960h/          (+ materialization.json)
      diarization/speaker-diarization-community-1/ (+ materialization.json)
      nltk_data/tokenizers/punkt_tab/english/...                 (alignment sentence splitter)

and are RE-VERIFIED here before any adapter loads them. A missing or mismatching artifact is
BLOCKED_BY_DEPENDENCY -- never a silent replacement or a download. `materialization.json` records
the repository, the requested revision, the RESOLVED 40-hex commit and the SHA-256 of every file.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from shorts_config import Config

from workers.shared.failures import FailureKind, StageFailure

MANIFEST = "materialization.json"
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
REPO_ROOT = Path(__file__).resolve().parents[2]

ASR_DIR = "whisper/faster-whisper-large-v3-turbo"
ALIGN_DIR = "alignment/wav2vec2-base-960h"
DIAR_DIR = "diarization/speaker-diarization-community-1"
EMBED_DIR = "embedding/bge-small-en-v1.5"  # Phase 4, embedding_runtime@1 (owner decision 2026-10-07 s2)
VAD_FILE = "silero/silero_vad_v6.onnx"
NLTK_DIR = "nltk_data"


def models_root(override: str | Path | None = None) -> Path:
    if override:
        return Path(override)
    from app.config import get_settings
    configured = get_settings().models_root
    return Path(configured) if configured else REPO_ROOT / "models"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _blocked(reason: str, detail: str = "") -> StageFailure:
    return StageFailure(FailureKind.BLOCKED_BY_DEPENDENCY, reason, detail)


@dataclass(frozen=True)
class MaterializedModel:
    component: str
    path: Path
    repository: str
    requested_revision: str
    resolved_revision: str
    files_sha256: dict[str, str] = field(default_factory=dict)

    def manifest_entry(self, weights_sha256: str | None) -> dict:
        return {"model_id": self.repository, "revision": self.resolved_revision, "sha256": weights_sha256}


def _read_manifest(directory: Path, component: str) -> dict:
    mf = directory / MANIFEST
    if not directory.is_dir() or not mf.is_file():
        raise _blocked(f"{component}_not_materialized", f"{mf} missing (run scripts/materialize_models.py)")
    return json.loads(mf.read_text())


def _verify_files(directory: Path, component: str, recorded: dict[str, str], pinned: dict[str, str]) -> None:
    """Every pinned file must be present, hash to its pinned value and agree with the recorded one;
    every other recorded file must still hash to what was recorded at materialization."""
    for rel, expected in pinned.items():
        f = directory / rel
        if not f.is_file():
            raise _blocked(f"{component}_file_missing", rel)
        actual = sha256_file(f)
        if actual != expected:
            raise _blocked(f"{component}_checksum_mismatch", f"{rel}: expected {expected}, got {actual}")
    for rel, expected in recorded.items():
        if rel in pinned:
            continue
        f = directory / rel
        if not f.is_file() or sha256_file(f) != expected:
            raise _blocked(f"{component}_recorded_file_mismatch", rel)


def verify_vad(cfg: Config, root: Path) -> Path:
    c = cfg.runtime_contract("asr_runtime@1")["vad"]
    f = root / "silero" / c["model_file"]
    if not f.is_file():
        raise _blocked("vad_model_missing", str(f))
    actual = sha256_file(f)
    if actual != c["model_sha256"]:
        raise _blocked("vad_checksum_mismatch", f"expected {c['model_sha256']}, got {actual}")
    return f


def verify_asr(cfg: Config, root: Path) -> MaterializedModel:
    m = cfg.runtime_contract("asr_runtime@1")["model"]
    d = root / ASR_DIR
    mf = _read_manifest(d, "asr_model")
    resolved = mf.get("resolved_revision", "")
    if not _HEX40.match(resolved) or not resolved.startswith(m["model_revision"]):
        raise _blocked("asr_model_revision_unresolved",
                       f"resolved {resolved!r} must be a 40-hex commit starting with {m['model_revision']!r}")
    _verify_files(d, "asr_model", mf["files"], {m["model_weights_file"]: m["model_weights_sha256"]})
    return MaterializedModel("asr", d, mf.get("repository", m["model_id"]), m["model_revision"], resolved, mf["files"])


def verify_alignment(cfg: Config, root: Path) -> MaterializedModel:
    m = cfg.runtime_contract("alignment_runtime@1")["model"]
    d = root / ALIGN_DIR
    mf = _read_manifest(d, "alignment_model")
    if mf.get("resolved_revision") != m["revision"]:
        raise _blocked("alignment_model_revision_mismatch", f"{mf.get('resolved_revision')!r} != {m['revision']!r}")
    _verify_files(d, "alignment_model", mf["files"], {m["weights_file"]: m["weights_sha256"]})
    return MaterializedModel("alignment", d, m["model_id"], m["revision"], m["revision"], mf["files"])


def verify_diarization(cfg: Config, root: Path) -> MaterializedModel:
    c = cfg.runtime_contract("diarization_runtime@1")
    d = root / DIAR_DIR
    mf = _read_manifest(d, "diarization_model")
    if mf.get("resolved_revision") != c["model"]["revision"]:
        raise _blocked("diarization_model_revision_mismatch", f"{mf.get('resolved_revision')!r}")
    _verify_files(d, "diarization_model", mf["files"], dict(c["model_files"]))
    return MaterializedModel("diarization", d, c["model"]["model_id"], c["model"]["revision"],
                             c["model"]["revision"], mf["files"])


def verify_punkt(root: Path) -> dict[str, str]:
    """NLTK punkt_tab data that whisperx.align() needs. alignment_runtime@1 pins NO identity for it
    (gap flagged to the owner): here it must exist and its file hashes are RECORDED in provenance,
    not compared to an expected value. Without it nltk would download it at runtime."""
    d = root / NLTK_DIR / "tokenizers" / "punkt_tab" / "english"
    files = sorted(p for p in d.rglob("*") if p.is_file()) if d.is_dir() else []
    if not files:
        raise _blocked("nltk_punkt_tab_not_provisioned", f"{d} (whisperx.align would download it at runtime)")
    return {str(p.relative_to(d)): sha256_file(p) for p in files}


def verify_embedding(cfg: Config, root: Path) -> MaterializedModel:
    """embedding_runtime@1: complete snapshot at the pinned 40-hex revision; model.safetensors hash
    pinned. No download, ever (runtime_downloads: false)."""
    c = cfg.runtime_contract("embedding_runtime@1")
    m = c["model"]
    d = root / EMBED_DIR
    mf = _read_manifest(d, "embedding_model")
    if mf.get("resolved_revision") != m["revision"]:
        raise _blocked("embedding_model_revision_mismatch", f"{mf.get('resolved_revision')!r} != {m['revision']!r}")
    _verify_files(d, "embedding_model", mf["files"], {m["model_file"]: m["model_sha256"]})
    return MaterializedModel("embedding", d, m["model_id"], m["revision"], m["revision"], mf["files"])
