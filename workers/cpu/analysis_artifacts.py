"""Attach the common Phase-4 artifact identity to computed content and validate against the JSON
Schema (impl plan 4.3: schemas are the one canonical definition; nothing is hand-modelled)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
from shorts_config import Config

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "packages/schemas/json"
STAGE_VERSIONS = {
    "audio_features_v1": "audio_features@1", "visual_features_v1": "visual_features@1",
    "shot_map_v1": "shot_map@1", "sentence_embeddings_v1": "sentence_embeddings@1",
    "texttiling_depth_v1": "texttiling_depth@1", "frame_manifest_v1": "frame_manifest@1",
}


def build_analysis_artifact(artifact_type: str, content: dict[str, Any], *, cfg: Config, job_id: str,
                            source_video_id: str, input_artifact_ids: list[str], input_sha256s: list[str],
                            input_sha256: str) -> dict[str, Any]:
    doc = {
        "schema_version": 1, "stage_version": STAGE_VERSIONS[artifact_type],
        "config_version": cfg.config_version, "config_sha256": cfg.config_sha256,
        "job_id": job_id, "source_video_id": source_video_id, "stage": "ANALYZING",
        "input_artifact_ids": input_artifact_ids, "input_sha256s": input_sha256s, "input_sha256": input_sha256,
        **content,
    }
    schema = json.loads((SCHEMA_DIR / f"{artifact_type}.schema.json").read_text())
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(doc)
    return doc
