"""Immutable config@1 registry (implementation plan 0.5 / 2.1).

All behavior-producing constants are read from one snapshot. Missing names raise, they are never defaulted.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .canonical import canonical_json, sha256_bytes

DEFAULT_SNAPSHOT = Path(__file__).resolve().parents[2] / "config@1.json"


def _freeze(v: Any) -> Any:
    if isinstance(v, dict):
        return MappingProxyType({k: _freeze(x) for k, x in v.items()})
    if isinstance(v, list):
        return tuple(_freeze(x) for x in v)
    return v


class ConfigSpecGap(KeyError):
    """A constant is not defined by the two source-of-truth documents (implementation plan 13.4)."""


class ConfigNotYetCalibrated(KeyError):
    """v5.0 states this constant has no initial value, only a calibration procedure.

    Raised instead of returning a guessed/placeholder number, so calling code cannot
    accidentally treat "not yet calibrated" as zero, None-as-falsy, or any other silent
    default. See config@1.json's calibrated_no_initial_value block.
    """


class Config:
    def __init__(self, raw: dict[str, Any]):
        self._raw = raw
        self.config_version: str = raw["config_version"]
        self.config_sha256: str = sha256_bytes(canonical_json(raw))
        self._constants = _freeze(raw["constants"])
        self._supplement = _freeze({k: v for k, v in raw["v5_supplement"].items() if k != "_note"})
        self._uncalibrated = _freeze(
            {k: v for k, v in raw.get("calibrated_no_initial_value", {}).items() if k != "_note"}
        )
        self._runtime_model_slots = _freeze(
            {k: v for k, v in raw.get("runtime_model_slots", {}).items() if k != "_note"}
        )
        self._runtime_contracts = _freeze(
            {k: v for k, v in raw.get("runtime_contracts", {}).items() if k != "_note"}
        )
        self.export_profiles = _freeze(raw["export_profiles"])
        self._validate()

    def __getitem__(self, name: str) -> Any:
        if name in self._constants:
            return self._constants[name]
        if name in self._supplement:
            return self._supplement[name]
        if name in self._uncalibrated:
            entry = self._uncalibrated[name]
            raise ConfigNotYetCalibrated(
                f"{name}: no initial value -- {entry['status']} "
                f"(procedure: {entry['procedure']}, source: {entry['source']})"
            )
        raise ConfigSpecGap(f"{name}: not defined in config@1 (spec gap; do not invent a value)")

    def __contains__(self, name: str) -> bool:
        return name in self._constants or name in self._supplement or name in self._uncalibrated

    def runtime_model(self, slot: str) -> str:
        """JUDGE_MODEL / STYLE_MODEL / HOOK_MODEL -- see config@1.json runtime_model_slots note."""
        return self._runtime_model_slots[slot]["value"]

    def runtime_contract(self, name: str) -> Any:
        """asr_runtime@1 / alignment_runtime@1 / diarization_runtime@1 (owner decision 2026-09-30 G3).

        Returns the frozen `values` mapping only when status == FROZEN and every required field is
        present and non-null. Otherwise raises ConfigSpecGap (BLOCKED_BY_SPEC) -- never a default.
        """
        entry = self._runtime_contracts.get(name)
        if entry is None:
            raise ConfigSpecGap(f"{name}: no such runtime contract in config@1")
        if entry["status"] != "FROZEN" or entry["values"] is None:
            raise ConfigSpecGap(
                f"{name}: BLOCKED_BY_SPEC -- runtime not frozen ({entry['source']}); "
                f"required fields: {list(entry['required_fields'])}"
            )
        missing = [f for f in entry["required_fields"]
                   if f not in entry["values"] or entry["values"][f] is None]
        if missing:
            raise ConfigSpecGap(f"{name}: FROZEN but missing required fields {missing}")
        return entry["values"]

    def runtime_contract_sha256(self, name: str) -> str:
        """Content identity persisted in transcript_v1 provenance (runtime_sha256)."""
        self.runtime_contract(name)  # raises if blocked/incomplete
        return sha256_bytes(canonical_json(self._raw["runtime_contracts"][name]["values"]))

    @property
    def identity(self) -> tuple[str, str]:
        return self.config_version, self.config_sha256

    @property
    def effective_max_compression_ratio(self) -> float:
        """v5.0 2.36.0: STUDY_MAX_RATIO if STUDY_MODE else MAX_COMPRESSION_RATIO."""
        return self["STUDY_MAX_RATIO"] if self["STUDY_MODE"] else self["MAX_COMPRESSION_RATIO"]

    def profile(self, profile_id: str):
        p = self.export_profiles.get(profile_id)
        if p is None or not p["enabled"]:
            raise ValueError(f"unknown or disabled export profile: {profile_id}")
        return p

    def _validate(self) -> None:
        c = self._constants
        derived = min(c["SINGLE_IDEA_EXTENSION"] * c["MAX_REGION_S"], c["ABSOLUTE_REGION_CEILING"])
        assert c["MAX_SINGLE_IDEA_REGION_S"] == derived, "MAX_SINGLE_IDEA_REGION_S must equal min(1.25*240, 360)"
        for name in ("T1_WEIGHTS", "T2_WEIGHTS"):
            assert abs(sum(c[name].values()) - 1.0) < 1e-9, f"{name} must sum to 1.00"
        assert c["MAX_JUDGE_CALLS_PER_REGION"] >= c["MAX_PLANS_PER_REGION"] * c["MAX_JUDGE_CALLS_PER_PLAN"]
        assert c["STYLE_HEAD_TOKENS"] + c["STYLE_TAIL_TOKENS"] + 1 <= c["STYLE_MAX_INPUT_TOKENS"] + 1
        # v5.0 2.36.7 table: floor <= rate-derived value's plausible range <= cap, for each budget stage
        for stage in ("R_DISC", "R_T1", "R_EDIT"):
            assert c[f"{stage}_FLOOR"] <= c[f"{stage}_CAP"], f"{stage} floor must not exceed cap"


def load_config(path: Path | str = DEFAULT_SNAPSHOT) -> Config:
    with open(path, encoding="utf-8") as f:
        return Config(json.load(f))


def config_identity(config: Config) -> tuple[str, str]:
    return config.identity
