#!/usr/bin/env python
"""PROVISIONING TOOL (not part of the runtime path). Run by a person with network access (and, for the
gated pyannote model, an accepted-conditions HF token in HF_TOKEN) to materialize the model artifacts
named in config@1 `runtime_contracts` into the local immutable models directory, VERIFY every pinned
SHA-256, resolve revisions to 40-hex commits, and write `materialization.json`. The workers
re-verify everything at load time and never download (runtime_downloads: false).

    uv run --group ml python scripts/materialize_models.py [--root models] [asr|alignment|diarization|all]

Owner decision 2026-10-06 (G3). NOT executed by the implementer (no network in the dev sandbox).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages/config/src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shorts_config import load_config

from workers.gpu import model_materialization as mm


def _snapshot(repo: str, revision: str, target: Path, token: str | None):
    from huggingface_hub import HfApi, snapshot_download
    resolved = HfApi().model_info(repo, revision=revision, token=token).sha  # short rev -> 40-hex commit
    target.mkdir(parents=True, exist_ok=True)
    snapshot_download(repo_id=repo, revision=resolved, local_dir=str(target), token=token)
    files = {str(p.relative_to(target)): mm.sha256_file(p) for p in sorted(target.rglob("*"))
             if p.is_file() and not p.name.startswith(".") and ".cache" not in p.parts and p.name != mm.MANIFEST}
    return resolved, files


def _write(target: Path, repo: str, requested: str, resolved: str, files: dict) -> None:
    (target / mm.MANIFEST).write_text(json.dumps(
        {"repository": repo, "requested_revision": requested, "resolved_revision": resolved, "files": files},
        indent=2, sort_keys=True) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", nargs="?", default="all", choices=["asr", "alignment", "diarization", "embedding", "all"])
    ap.add_argument("--root", default=None)
    ap.add_argument("--hf-token", default=None)
    a = ap.parse_args()
    import os
    token = a.hf_token or os.environ.get("HF_TOKEN")
    cfg, root = load_config(), mm.models_root(a.root)
    if a.what in ("asr", "all"):
        m = cfg.runtime_contract("asr_runtime@1")["model"]
        t = root / mm.ASR_DIR
        resolved, files = _snapshot(m["model_id"], m["model_revision"], t, token)
        _write(t, m["model_id"], m["model_revision"], resolved, files)
        mm.verify_asr(cfg, root)
        print("asr ok", resolved)
    if a.what in ("alignment", "all"):
        m = cfg.runtime_contract("alignment_runtime@1")["model"]
        t = root / mm.ALIGN_DIR
        resolved, files = _snapshot(m["model_id"], m["revision"], t, token)
        _write(t, m["model_id"], m["revision"], resolved, files)
        mm.verify_alignment(cfg, root)
        print("alignment ok", resolved)
    if a.what in ("diarization", "all"):
        c = cfg.runtime_contract("diarization_runtime@1")
        t = root / mm.DIAR_DIR
        resolved, files = _snapshot(c["model"]["model_id"], c["model"]["revision"], t, token)
        _write(t, c["model"]["model_id"], c["model"]["revision"], resolved, files)
        mm.verify_diarization(cfg, root)
        print("diarization ok", resolved)
    if a.what in ("embedding", "all"):
        m = cfg.runtime_contract("embedding_runtime@1")["model"]
        t = root / mm.EMBED_DIR
        resolved, files = _snapshot(m["model_id"], m["revision"], t, token)
        _write(t, m["model_id"], m["revision"], resolved, files)
        mm.verify_embedding(cfg, root)
        print("embedding ok", resolved)
    print("NOTE: nltk punkt_tab (english) must also be provisioned under", root / mm.NLTK_DIR,
          "-- alignment_runtime@1 pins no identity for it (owner decision pending).")
    print("NOTE: models/fasttext/lid.176.ftz and models/silero/silero_vad_v6.onnx are provisioned separately.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
