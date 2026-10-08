"""Tests for the 2026-10-04 owner decisions (fastText adapter, operational values, v5.0 2.25
amendment, transport validation/retention, real-model gate scaffold)."""
from __future__ import annotations

import math
from pathlib import Path

import pytest

from workers.cpu.language_gate import (
    CONTRACT_CHECK_TEXT,
    FASTTEXT_ADAPTER_VERSION,
    FastTextLanguageID,
    fasttext_predict_v1,
)
from workers.shared.failures import FailureKind, StageFailure


class _F:
    """Stands in for the pybind model: f.predict(text, k, threshold, on_unicode_error) -> [(prob, label)]."""

    def __init__(self, pairs):
        self.pairs, self.calls = pairs, []

    def predict(self, text, k, threshold, on_unicode_error):
        self.calls.append((text, k, threshold, on_unicode_error))
        return self.pairs


class _Model:
    def __init__(self, pairs):
        self.f = _F(pairs)

    def predict(self, *a, **k):  # the numpy-2-broken wrapper
        raise AssertionError("model.predict() (the broken wrapper) must never be called")


def test_adapter_calls_pybind_f_predict_only_and_returns_plain_scalars():
    m = _Model([(0.9731, "__label__en")])
    code, conf = fasttext_predict_v1(m, "hello world")
    assert (code, type(conf)) == ("en", float) and conf == pytest.approx(0.9731)
    assert m.f.calls == [("hello world", 1, 0.0, "strict")]  # top-1, no threshold, strict unicode


def test_adapter_rejects_newlines_empty_and_non_finite():
    with pytest.raises(ValueError):
        fasttext_predict_v1(_Model([(1.0, "__label__en")]), "a\nb")
    with pytest.raises(StageFailure) as e:
        fasttext_predict_v1(_Model([]), "x")
    assert e.value.reason == "language_id_empty_prediction"
    with pytest.raises(StageFailure) as e:
        fasttext_predict_v1(_Model([(float("nan"), "__label__en")]), "x")
    assert e.value.reason == "language_id_non_finite_confidence"
    code, conf = fasttext_predict_v1(_Model([(1.0000002, "__label__fr")]), "x")
    assert (code, conf) == ("fr", 1.0)  # clamped to [0, 1]


def test_adapter_is_narrow_not_a_general_fasttext_replacement():
    src = Path("workers/cpu/language_gate.py").read_text()
    for forbidden in ("train_supervised", "train_unsupervised", "multilinePredict", "import numpy", "get_input_matrix"):
        assert forbidden not in src
    code_lines = [ln for ln in src.splitlines() if not ln.strip().startswith(("#", '"""')) and "`" not in ln]
    assert sum("model.f.predict(" in ln for ln in code_lines) == 1  # the single pybind call
    assert not any("model.predict(" in ln or "self._model.predict(" in ln for ln in code_lines)


def test_contract_check_enforces_sha_adapter_and_shape():
    ok = FastTextLanguageID("m", "a" * 64, _Model([(0.99, "__label__en")]), sha256_verified=True)
    code, conf = ok.contract_check()
    assert code == "en" and math.isfinite(conf) and ok.adapter_calls == 1
    assert ok._model.f.calls[0][0] == CONTRACT_CHECK_TEXT
    unverified = FastTextLanguageID("m", "a" * 64, _Model([(0.99, "__label__en")]), sha256_verified=False)
    with pytest.raises(StageFailure, match="language_id_contract_check_failed") as e:
        unverified.contract_check()
    assert "sha256_not_verified" in e.value.detail
    wrong = FastTextLanguageID("m", "a" * 64, _Model([(0.99, "__label__fr")]), sha256_verified=True)
    with pytest.raises(StageFailure) as e:
        wrong.contract_check()
    assert "unexpected_language:fr" in e.value.detail


def test_loader_hashes_before_loading_and_runs_the_contract_check(tmp_path, monkeypatch):
    import hashlib
    import sys
    import types

    blob = b"fake ftz bytes"
    (tmp_path / "lid.176.ftz").write_bytes(blob)
    (tmp_path / "lid.176.ftz.sha256").write_text(hashlib.sha256(blob).hexdigest() + "  lid.176.ftz\n")
    order: list[str] = []
    fake = types.ModuleType("fasttext")
    fake.load_model = lambda path: (order.append("load"), _Model([(0.97, "__label__en")]))[1]
    monkeypatch.setitem(sys.modules, "fasttext", fake)
    real_sha = hashlib.sha256

    def spy(*a, **k):
        order.append("hash")
        return real_sha(*a, **k)
    monkeypatch.setattr("workers.cpu.language_gate.hashlib.sha256", spy)
    lid = FastTextLanguageID.from_provisioned_artifact("fasttext/lid.176.ftz", tmp_path)
    assert order.index("hash") < order.index("load")  # checksum verified BEFORE loading
    assert lid.sha256_verified and lid.adapter_calls == 1 and lid.adapter_version == FASTTEXT_ADAPTER_VERSION
    (tmp_path / "lid.176.ftz.sha256").write_text("0" * 64)
    with pytest.raises(StageFailure) as e:
        FastTextLanguageID.from_provisioned_artifact("m", tmp_path)
    assert e.value.reason == "language_id_model_checksum_mismatch" and e.value.kind is FailureKind.BLOCKED_BY_DEPENDENCY


def test_no_numpy_pin_and_numpy2_stays_locked():
    py, lock = Path("pyproject.toml").read_text(), Path("uv.lock").read_text()
    assert "numpy==1.26.4" not in py
    assert 'name = "numpy"\nversion = "2.' in lock


def test_operational_defaults_are_not_config_at_1():
    from app.config import Settings
    s = Settings()
    assert (s.dispatch_lease_s, s.reconcile_interval_s) == (60, 15)
    assert (s.transport_retention_success_h, s.transport_retention_failed_d, s.transport_retention_cancelled_d) == (24, 7, 7)
    raw = Path("packages/config/config@1.json").read_text()
    for name in ("dispatch_lease", "reconcile_interval", "transport_retention", "poll_interval"):
        assert name not in raw


def test_cpu_worker_consumes_both_queues_and_beat_schedules_both_maintenance_jobs():
    from workers.cpu.worker import WORKER_COMMAND, WORKER_QUEUES, app
    assert WORKER_QUEUES == ("cpu", "maintenance") and "-Q cpu,maintenance --beat" in WORKER_COMMAND
    sched = app.conf.beat_schedule
    assert sched["reconcile-phase3-dispatch"]["schedule"] == 15.0
    assert sched["reconcile-phase3-dispatch"]["options"]["queue"] == "maintenance"
    assert sched["sweep-transport-objects"]["options"]["queue"] == "maintenance"
    assert "-Q cpu,maintenance --beat" in Path("apps/api/README.md").read_text()
    assert not Path("docker-compose.yml").exists() or "worker-beat" not in Path("docker-compose.yml").read_text()


def test_v5_0_section_2_25_carries_the_owner_amendment():
    spec = Path("docs/spec/virality_shorts_plan_v5_0.md").read_text()
    assert "OWNER AMENDMENT 2026-10-04" in spec and "stage sub-steps" in spec
    assert spec.index("OWNER AMENDMENT 2026-10-04") > spec.index("Each stage must:")


def test_transport_envelope_schema_is_internal_only():
    assert Path("packages/schemas/json/internal/phase3_stage_output_v1.schema.json").is_file()
    assert not Path("packages/schemas/json/phase3_stage_output_v1.schema.json").exists()
    assert not list(Path("packages/schemas").rglob("phase3_stage_output_v1.py"))
    assert not list(Path("packages/schemas").rglob("phase3_stage_output_v1.ts"))


def test_real_model_exit_gate_scaffold_blocks_loudly(monkeypatch):
    src = Path("tests/real_models/test_phase3_real_smoke.py").read_text()
    for needle in ("REQUIRE_REAL_MODELS", "BLOCKED_BY_SPEC", "BLOCKED_BY_DEPENDENCY", "real_models",
                   "transcribe", "align(", "diarize(", "contract_check"):
        assert needle in src
    assert "smoke-real" in Path("Makefile").read_text()
