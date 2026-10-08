"""IT-3-4 (impl plan Phase 3; refactored per owner decision C3): the Phase-3 -> Phase-4 ARTIFACT
BOUNDARY, plus the Phase 3 preflight state machine (owner decisions C1, C2, C4, G4, G6, G7).

Real normalization (ffmpeg) produces the real analysis_audio artifact; ASR / alignment /
diarization / fastText are deterministic fakes behind the production Protocols (no GPU, no model
files, no network in the sandbox). The GPU boundary is exercised through a GPUExecutionProvider
test double that calls the REAL worker-side `run_gpu_task` against the REAL DB + storage.
IT-3-4 does NOT assert embedding determinism -- that belongs to Phase 4 (owner C3).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from pathlib import Path

import jsonschema
import pytest
from sqlalchemy import select

from tests.unit.test_phase3_core import FakeLID

pytestmark = pytest.mark.asyncio
SCHEMA = json.loads(Path("packages/schemas/json/transcript_v1.schema.json").read_text())
SPEECH = Path("packages/fixtures/media/fixture_speech_45s.mp4")
EVENT = Path("packages/fixtures/media/fixture_event_6_8s.mp4")

TEXT = ("Hello everyone. " + "This is a short test sentence with enough words to pass the gate. " * 3).split()


class FakeASR:
    runtime_id, model_id, model_revision = "fake-asr@0", "fake/asr", None
    calls = 0

    def transcribe(self, audio_path):
        FakeASR.calls += 1
        assert Path(audio_path).read_bytes()[:4] == b"RIFF"  # real WAV from real normalization
        return [{"start_ms": 0, "end_ms": 20000, "text": " ".join(TEXT)}]


class FakeAlign:
    runtime_id, model_id, model_revision = "fake-align@0", "fake/align", None

    def __init__(self, fail_kind=None, unaligned_edge=False):
        self.calls, self.fail_kind, self.unaligned_edge = 0, fail_kind, unaligned_edge

    def align(self, audio_path, segments):
        self.calls += 1
        if self.fail_kind:
            from workers.shared.failures import StageFailure
            raise StageFailure(self.fail_kind, "boom")
        words, t = [], 0
        for i, w in enumerate(" ".join(s["text"] for s in segments).split()):
            words.append({"text": w, "start_ms": t, "end_ms": t + 200, "confidence": 0.9})
            t += 260 if not w.endswith(".") else 1200  # long gap after a terminal '.'
        if self.unaligned_edge:
            words[2] = {"text": words[2]["text"], "start_ms": None, "end_ms": None, "confidence": None}
        return words


class CrashingAlign(FakeAlign):
    def align(self, audio_path, segments):
        self.calls += 1
        raise RuntimeError("worker process crashed")


class FakeDiar:
    runtime_id, model_id, model_revision = "fake-diar@0", "pyannote/speaker-diarization-community-1", None

    def __init__(self, boom=False):
        self.boom = boom

    def diarize(self, audio_path):
        if self.boom:
            raise RuntimeError("diarizer exploded")
        return [{"start_ms": 0, "end_ms": 60000, "raw_label": "SPEAKER_03"}]


class InProcessGPU:
    """GPUExecutionProvider test double: runs the real worker-side body, synchronously."""

    def __init__(self, backends, artifact_storage, cfg):
        self.backends, self.storage, self.cfg, self.submitted, self.jobs = backends, artifact_storage, cfg, [], {}
        self.transport_inputs_seen = []

    name = "in_process_test_double"

    async def submit(self, *, task_name, input_artifact_ids, model_manifest, config_identity, request_id,
                     transport_inputs=None):
        from app.db import session_scope

        from workers.gpu.execute import run_gpu_task
        from workers.shared.gpu_provider import GPUJobHandle
        self.submitted.append(task_name)
        self.transport_inputs_seen.append(transport_inputs)
        try:
            async with session_scope() as session:  # SEPARATE session, like the real GPU worker
                self.jobs[request_id] = await run_gpu_task(
                    session, task_name=task_name, input_artifact_ids=list(input_artifact_ids), cfg=self.cfg,
                    backends=self.backends, artifact_storage=self.storage, transport_inputs=transport_inputs)
        except Exception as exc:  # noqa: BLE001  an unexpected crash -> Celery FAILURE -> provider reports TRANSIENT (#5)
            self.jobs[request_id] = {"status": "error", "kind": "TRANSIENT", "reason": f"crash:{type(exc).__name__}"}
        return GPUJobHandle(request_id)

    async def get_status(self, *, provider_job_id):
        from workers.shared.gpu_provider import GPUJobState, GPUJobStatus, GPUOutput
        p = self.jobs[provider_job_id]
        if p["status"] == "ok":
            return GPUJobStatus(provider_job_id, GPUJobState.SUCCEEDED, outputs=tuple(GPUOutput(**o) for o in p["outputs"]))
        return GPUJobStatus(provider_job_id, GPUJobState.FAILED, error=p["reason"], failure_kind=p["kind"])

    async def cancel(self, *, provider_job_id):
        raise AssertionError("not expected")


class ReadRecorder:
    """Wraps a storage adapter and records every key read (proves 'artifacts only')."""

    def __init__(self, inner):
        self.inner, self.reads = inner, []

    def read_bytes(self, key):
        self.reads.append(key)
        return self.inner.read_bytes(key)

    def __getattr__(self, n):
        return getattr(self.inner, n)


async def _normalized_job(client, auth_headers, settings, fixture: Path, *, strip_audio: bool, tmp_path):
    """Upload -> job (NORMALIZING) -> real normalization -> job NORMALIZED. Returns ids."""
    from app.db import session_scope
    from app.models import Artifact, SourceVideo
    from app.storage import build_storage_adapter
    from shorts_config import load_config

    from workers.cpu.stage_normalize import run_normalization_stage
    from workers.shared.job_state import transition_job_state
    from workers.shared.stage_runner import ConfigIdentity

    src = fixture
    if strip_audio:
        src = tmp_path / "silent.mp4"
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-i", str(fixture), "-an", "-c:v", "copy", str(src)],  # noqa: ASYNC221
                       check=True, capture_output=True)
    ru = await client.post("/v1/uploads", json={"filename": src.name, "content_type": "video/mp4"}, headers=auth_headers)
    up = ru.json()
    build_storage_adapter(settings, bucket_kind="source").write_bytes(up["storage_key"], src.read_bytes())
    rc = await client.post(f"/v1/uploads/{up['upload_id']}/complete",
                           json={"checksum_sha256": hashlib.sha256(src.read_bytes()).hexdigest()}, headers=auth_headers)
    svid = rc.json()["source_video_id"]
    rj = await client.post("/v1/jobs", json={"source_video_id": svid, "export_profile_id": "youtube_shorts"},
                           headers=auth_headers)
    job_id = rj.json()["job_id"]
    cfg = load_config()
    async with session_scope() as session:
        sv = await session.get(SourceVideo, uuid.UUID(svid))
        raw = (await session.execute(select(Artifact).where(
            Artifact.source_video_id == uuid.UUID(svid), Artifact.artifact_type == "raw_source"))).scalar_one()
        await run_normalization_stage(
            session, job_id=job_id, source_video_id=svid, source_storage_key=sv.raw_storage_key,
            source_artifact_id=str(raw.id), source_storage=build_storage_adapter(settings, bucket_kind="source"),
            artifact_storage=build_storage_adapter(settings, bucket_kind="artifacts"),
            config=ConfigIdentity(cfg.config_version, cfg.config_sha256), max_duration_s=cfg["MAX_SOURCE_DURATION_S"])
        assert await transition_job_state(session, job_id=job_id, from_state="NORMALIZING", to_state="NORMALIZED")
        await session.commit()
    return job_id, svid, cfg


def _deps(session, cfg, settings, backends, lid=None):
    from app.storage import build_storage_adapter

    from workers.cpu.stage_transcript import Phase3Deps
    storage = ReadRecorder(build_storage_adapter(settings, bucket_kind="artifacts"))
    gpu = InProcessGPU(backends, storage, cfg)
    return Phase3Deps(session=session, cfg=cfg, artifact_storage=storage, gpu=gpu,
                      language_backend_factory=lambda: lid or FakeLID("en", 0.99), poll_interval_s=0.0), gpu, storage


async def _state(job_id):
    from app.db import session_scope
    from app.models import ProcessingJob
    async with session_scope() as s:
        j = await s.get(ProcessingJob, uuid.UUID(job_id))
        return j.state, j.error


async def _stage_runs(job_id):
    from app.db import session_scope
    from app.models import StageRun
    async with session_scope() as s:
        rows = (await s.scalars(select(StageRun).where(StageRun.job_id == uuid.UUID(job_id)))).all()
        return {(r.stage_name, r.status) for r in rows}


async def test_happy_path_stays_normalized_then_analyzing_and_phase4_handoff(
    client, auth_headers, settings, tmp_path,
):
    from app.db import session_scope
    from app.models import Artifact

    from workers.cpu.stage_transcript import run_phase3
    from workers.gpu.backends import Backends

    job_id, svid, cfg = await _normalized_job(client, auth_headers, settings, SPEECH, strip_audio=False, tmp_path=tmp_path)
    assert (await _state(job_id))[0] == "NORMALIZED"
    align = FakeAlign()
    async with session_scope() as session:
        d, gpu, storage = _deps(session, cfg, settings, Backends(FakeASR(), align, FakeDiar()))
        tid = await run_phase3(d, job_id=job_id, source_video_id=svid)
        await session.commit()
    assert tid and (await _state(job_id)) == ("ANALYZING", None)
    assert {("asr", "SUCCEEDED"), ("language_gate", "SUCCEEDED"), ("forced_alignment", "SUCCEEDED"),
            ("diarization", "SUCCEEDED"), ("sentence_segmentation", "SUCCEEDED")} <= await _stage_runs(job_id)
    assert gpu.submitted == ["asr", "forced_alignment", "diarization"]

    # ---- IT-3-4 proper: a Phase-4 consumer sees ONLY the transcript artifact ----------------
    async with session_scope() as session:
        art = await session.get(Artifact, uuid.UUID(tid))
        assert art.artifact_type == "transcript_v1" and art.job_id == uuid.UUID(job_id)
        normalized_keys = {a.storage_location for a in (await session.scalars(select(Artifact).where(
            Artifact.job_id == uuid.UUID(job_id), Artifact.artifact_type == "normalized_media"))).all()}
    from app.storage import build_storage_adapter
    phase4_view = ReadRecorder(build_storage_adapter(settings, bucket_kind="artifacts"))
    doc = json.loads(phase4_view.read_bytes(art.storage_location))
    assert phase4_view.reads == [art.storage_location]      # nothing else read
    assert not (set(phase4_view.reads) & normalized_keys)   # raw/normalized MP4 never reopened
    assert not any(k in "".join(storage.reads) for k in normalized_keys)  # ...nor by Phase 3 itself
    jsonschema.Draft202012Validator(SCHEMA).validate(doc)
    ids = [s["sentence_id"] for s in doc["sentences"]]
    assert ids == [f"S{i:06d}" for i in range(1, len(ids) + 1)] and len(ids) >= 2
    assert all(s["end_ms"] >= s["start_ms"] for s in doc["sentences"])
    assert [s["start_ms"] for s in doc["sentences"]] == sorted(s["start_ms"] for s in doc["sentences"])
    assert doc["provenance"]["diarization"]["status"] == "succeeded" and doc["words"][0]["speaker_id"] == "SPK_0"
    assert doc["language"]["gate_status"] == "passed" and doc["source_video_id"] == svid
    assert doc["config_sha256"] == cfg.config_sha256

    # idempotency (impl plan 3.2): re-running reuses every SUCCEEDED stage_run -> no new GPU/ASR work
    before = (len(gpu.submitted), FakeASR.calls, align.calls)
    async with session_scope() as session:
        d2, gpu2, _ = _deps(session, cfg, settings, Backends(FakeASR(), align, FakeDiar()))
        tid2 = await run_phase3(d2, job_id=job_id, source_video_id=svid)
        await session.commit()
    assert gpu2.submitted == [] and (FakeASR.calls, align.calls) == (before[1], before[2]) and tid2 == tid


async def test_no_audio_stream_skips_gpu_entirely_g6(client, auth_headers, settings, tmp_path):
    from app.db import session_scope
    from app.models import Artifact

    from workers.cpu.stage_transcript import run_phase3
    from workers.gpu.backends import Backends

    job_id, svid, cfg = await _normalized_job(client, auth_headers, settings, EVENT, strip_audio=True, tmp_path=tmp_path)
    async with session_scope() as s:
        types = {a.artifact_type for a in (await s.scalars(select(Artifact).where(Artifact.job_id == uuid.UUID(job_id)))).all()}
    assert "analysis_audio" not in types  # no synthesized silence
    async with session_scope() as session:
        d, gpu, storage = _deps(session, cfg, settings, Backends(FakeASR(), FakeAlign(), FakeDiar()))
        tid = await run_phase3(d, job_id=job_id, source_video_id=svid)
        await session.commit()
    assert gpu.submitted == [] and (await _state(job_id))[0] == "ANALYZING"
    async with session_scope() as s:
        art = await s.get(Artifact, uuid.UUID(tid))
    doc = json.loads(storage.inner.read_bytes(art.storage_location))
    jsonschema.Draft202012Validator(SCHEMA).validate(doc)
    assert doc["words"] == [] and doc["provenance"]["audio"]["availability"] == "not_applicable"
    assert doc["provenance"]["alignment"]["status"] == "not_applicable"
    assert doc["provenance"]["diarization"]["attempted"] is False


@pytest.mark.parametrize("lid,reason", [(("fr", 0.99), "unsupported_language"), (("en", 0.5), "language_uncertain")])
async def test_language_gate_failure_fails_job_and_never_aligns(client, auth_headers, settings, tmp_path, lid, reason):
    from app.db import session_scope

    from workers.cpu.stage_transcript import run_phase3
    from workers.gpu.backends import Backends

    job_id, svid, cfg = await _normalized_job(client, auth_headers, settings, SPEECH, strip_audio=False, tmp_path=tmp_path)
    async with session_scope() as session:
        d, gpu, _ = _deps(session, cfg, settings, Backends(FakeASR(), FakeAlign(), FakeDiar()), lid=FakeLID(*lid))
        assert await run_phase3(d, job_id=job_id, source_video_id=svid) is None
        await session.commit()
    state, err = await _state(job_id)
    assert state == "FAILED" and reason in err and gpu.submitted == ["asr"]  # never entered ANALYZING


async def test_alignment_unavailable_fails_job_after_bounded_transient_retries(client, auth_headers, settings, tmp_path):
    from app.db import session_scope

    from workers.cpu.stage_transcript import run_phase3
    from workers.gpu.backends import Backends
    from workers.shared.failures import FailureKind

    job_id, svid, cfg = await _normalized_job(client, auth_headers, settings, SPEECH, strip_audio=False, tmp_path=tmp_path)
    # InProcessGPU's run_gpu_task converts StageFailure to {"status":"error","kind":...}
    align = FakeAlign(fail_kind=FailureKind.TRANSIENT)
    async with session_scope() as session:
        d, gpu, _ = _deps(session, cfg, settings, Backends(FakeASR(), align, FakeDiar()))
        assert await run_phase3(d, job_id=job_id, source_video_id=svid) is None
        await session.commit()
    state, err = await _state(job_id)
    assert state == "FAILED" and "alignment_unavailable" in err
    assert gpu.submitted.count("forced_alignment") == cfg["STAGE_MAX_ATTEMPTS"]  # bounded: 3
    assert "diarization" not in gpu.submitted


async def test_permanent_alignment_failure_is_not_retried(client, auth_headers, settings, tmp_path):
    from app.db import session_scope

    from workers.cpu.stage_transcript import run_phase3
    from workers.gpu.backends import Backends
    from workers.shared.failures import FailureKind

    job_id, svid, cfg = await _normalized_job(client, auth_headers, settings, SPEECH, strip_audio=False, tmp_path=tmp_path)
    async with session_scope() as session:
        d, gpu, _ = _deps(session, cfg, settings, Backends(FakeASR(), FakeAlign(fail_kind=FailureKind.PERMANENT_MODEL), FakeDiar()))
        await run_phase3(d, job_id=job_id, source_video_id=svid)
        await session.commit()
    assert gpu.submitted.count("forced_alignment") == 1 and (await _state(job_id))[0] == "FAILED"


async def test_unaligned_sentence_edge_does_not_fail_the_job_but_is_marked_unusable(
    client, auth_headers, settings, tmp_path,
):
    from app.db import session_scope
    from app.models import Artifact

    from workers.cpu.stage_transcript import run_phase3
    from workers.gpu.backends import Backends

    job_id, svid, cfg = await _normalized_job(client, auth_headers, settings, SPEECH, strip_audio=False, tmp_path=tmp_path)
    async with session_scope() as session:
        d, _, storage = _deps(session, cfg, settings, Backends(FakeASR(), FakeAlign(unaligned_edge=True), FakeDiar()))
        tid = await run_phase3(d, job_id=job_id, source_video_id=svid)
        await session.commit()
    assert tid and (await _state(job_id)) == ("ANALYZING", None)  # owner 2026-10-02 #1
    async with session_scope() as s:
        art = await s.get(Artifact, uuid.UUID(tid))
    doc = json.loads(storage.inner.read_bytes(art.storage_location))
    jsonschema.Draft202012Validator(SCHEMA).validate(doc)
    unusable = [x for x in doc["sentences"] if not (x["start_timing_usable"] and x["end_timing_usable"])]
    assert unusable and all(x["start_ms"] is None or x["end_ms"] is None for x in unusable)
    assert all(x["text"] for x in doc["sentences"])  # sentence + transcript data preserved


async def test_unexpected_gpu_crash_is_retried_not_classified_permanent(client, auth_headers, settings, tmp_path):
    from app.db import session_scope

    from workers.cpu.stage_transcript import run_phase3
    from workers.gpu.backends import Backends

    job_id, svid, cfg = await _normalized_job(client, auth_headers, settings, SPEECH, strip_audio=False, tmp_path=tmp_path)
    async with session_scope() as session:
        d, gpu, _ = _deps(session, cfg, settings, Backends(FakeASR(), CrashingAlign(), FakeDiar()))
        await run_phase3(d, job_id=job_id, source_video_id=svid)
        await session.commit()
    assert gpu.submitted.count("forced_alignment") == cfg["STAGE_MAX_ATTEMPTS"]  # recovered by bounded retry, not PERMANENT
    assert (await _state(job_id))[0] == "FAILED"


async def test_envelopes_are_not_artifacts_and_execution_metadata_is_recorded(
    client, auth_headers, settings, tmp_path,
):
    from app.db import session_scope
    from app.models import Artifact, StageRun

    from workers.cpu.stage_transcript import run_phase3
    from workers.gpu.backends import Backends

    job_id, svid, cfg = await _normalized_job(client, auth_headers, settings, SPEECH, strip_audio=False, tmp_path=tmp_path)
    async with session_scope() as session:
        d, gpu, _ = _deps(session, cfg, settings, Backends(FakeASR(), FakeAlign(), FakeDiar()))
        d.poll_interval_s, d.poll_timeout_s = 0.0, 123.0
        await run_phase3(d, job_id=job_id, source_video_id=svid)
        await session.commit()
    async with session_scope() as s:
        types = {a.artifact_type for a in (await s.scalars(select(Artifact).where(Artifact.job_id == uuid.UUID(job_id)))).all()}
        runs = {r.stage_name: r for r in (await s.scalars(select(StageRun).where(StageRun.job_id == uuid.UUID(job_id)))).all()}
    assert "phase3_stage_output_v1" not in types  # #6: no new persistent artifact lineage type
    assert {"transcript_v1", "media_manifest_v1", "normalized_media", "analysis_audio"} <= types
    for stage in ("asr", "forced_alignment", "diarization"):
        m = runs[stage].execution_metadata
        assert runs[stage].output_artifact_ids == []
        assert m["output"]["storage_location"].startswith("transport/") and len(m["output"]["checksum"]) == 64
        ex = m["execution"]  # #8: effective operational values recorded
        assert (ex["poll_interval_s"], ex["poll_timeout_s"], ex["attempts"]) == (0.0, 123.0, 1)
        assert ex["max_attempts"] == cfg["STAGE_MAX_ATTEMPTS"] and ex["provider"] == "in_process_test_double"
        assert len(ex["provider_job_ids"]) == 1
    assert runs["language_gate"].execution_metadata["inline"]["language"]["gate_status"] == "passed"
    # alignment received the ASR envelope as a transport descriptor, not an artifact id
    assert gpu.transport_inputs_seen[1]["asr"]["storage_location"].startswith("transport/")


@pytest.mark.parametrize("diar,status,reason", [
    (FakeDiar(boom=True), "failed", "extraction_failed"),
    (None, "unavailable", "not_available_in_stage"),
])
async def test_diarization_failure_is_non_fatal_c4(client, auth_headers, settings, tmp_path, diar, status, reason):
    from app.db import session_scope
    from app.models import Artifact

    from workers.cpu.stage_transcript import run_phase3
    from workers.gpu.backends import Backends

    job_id, svid, cfg = await _normalized_job(client, auth_headers, settings, SPEECH, strip_audio=False, tmp_path=tmp_path)
    async with session_scope() as session:
        d, _, storage = _deps(session, cfg, settings, Backends(FakeASR(), FakeAlign(), diar))
        tid = await run_phase3(d, job_id=job_id, source_video_id=svid)
        await session.commit()
    assert tid and (await _state(job_id))[0] == "ANALYZING"
    async with session_scope() as s:
        art = await s.get(Artifact, uuid.UUID(tid))
    doc = json.loads(storage.inner.read_bytes(art.storage_location))
    jsonschema.Draft202012Validator(SCHEMA).validate(doc)
    p = doc["provenance"]["diarization"]
    assert (p["status"], p["missing_reason"]) == (status, reason)
    assert all(w["speaker_id"] is None for w in doc["words"]) and doc["speaker_turns"] == []
    assert doc["sentences"]  # everything not requiring speaker evidence still produced


async def _task_job(client, auth_headers, settings):
    import hashlib as h

    from app.db import session_scope
    from app.models import Artifact, SourceVideo
    from app.storage import build_storage_adapter

    ru = await client.post("/v1/uploads", json={"filename": "s.mp4", "content_type": "video/mp4"}, headers=auth_headers)
    up = ru.json()
    build_storage_adapter(settings, bucket_kind="source").write_bytes(up["storage_key"], SPEECH.read_bytes())
    rc = await client.post(f"/v1/uploads/{up['upload_id']}/complete",
                           json={"checksum_sha256": h.sha256(SPEECH.read_bytes()).hexdigest()}, headers=auth_headers)
    svid = rc.json()["source_video_id"]
    job_id = (await client.post("/v1/jobs", json={"source_video_id": svid, "export_profile_id": "youtube_shorts"},
                                headers=auth_headers)).json()["job_id"]
    async with session_scope() as s:
        sv = await s.get(SourceVideo, uuid.UUID(svid))
        raw = (await s.execute(select(Artifact).where(Artifact.source_video_id == uuid.UUID(svid),
                                                       Artifact.artifact_type == "raw_source"))).scalar_one()
    return job_id, svid, sv.raw_storage_key, str(raw.id)


async def _run_normalize_task(app, kwargs):
    import asyncio

    from app.db import dispose_engine

    from workers.cpu import tasks as cpu_tasks
    normalize, *_ = cpu_tasks.bind(app)
    await dispose_engine()  # the task runs its own asyncio.run() loop (in a thread) with a fresh engine
    return await asyncio.to_thread(normalize.apply, kwargs=kwargs)


async def _intent(job_id):
    from app.db import session_scope
    from app.models import Phase3DispatchIntent
    async with session_scope() as s:
        return await s.scalar(select(Phase3DispatchIntent).where(Phase3DispatchIntent.job_id == uuid.UUID(job_id)))


async def test_normalize_task_is_atomic_and_dispatches_through_a_durable_intent(
    client, auth_headers, settings, monkeypatch,
):
    from shorts_config import load_config

    from workers.shared.celery_app import make_celery_app

    job_id, svid, key, raw_id = await _task_job(client, auth_headers, settings)
    app = make_celery_app(settings.redis_url)
    sent = []
    monkeypatch.setattr(app, "send_task", lambda name, **kw: sent.append((name, kw)))
    cfg = load_config()
    out = await _run_normalize_task(app, {"job_id": job_id, "source_video_id": svid, "source_storage_key": key,
                                          "source_artifact_id": raw_id, "max_duration_s": cfg["MAX_SOURCE_DURATION_S"]})
    assert out.successful(), out.traceback
    assert (await _state(job_id))[0] == "NORMALIZED"
    it = await _intent(job_id)
    assert it.state == "DISPATCHED" and it.dispatch_count == 1 and it.lease_expires_at is not None
    assert [n for n, _ in sent] == ["workers.cpu.run_transcript_preflight"]
    assert sent[0][1]["queue"] == "cpu" and sent[0][1]["task_id"] == it.task_id
    assert sent[0][1]["kwargs"] == {"job_id": job_id, "source_video_id": svid}


async def test_crash_between_commit_and_dispatch_leaves_pending_intent_and_reconciler_resubmits(
    client, auth_headers, settings, monkeypatch,
):
    """The old crash window: job NORMALIZED, broker enqueue never happened."""
    from app.db import session_scope
    from shorts_config import load_config

    from workers.shared import dispatch_intents
    from workers.shared.celery_app import make_celery_app

    job_id, svid, key, raw_id = await _task_job(client, auth_headers, settings)
    app = make_celery_app(settings.redis_url)

    def boom(name, **kw):
        raise ConnectionError("broker down")
    monkeypatch.setattr(app, "send_task", boom)
    cfg = load_config()
    out = await _run_normalize_task(app, {"job_id": job_id, "source_video_id": svid, "source_storage_key": key,
                                          "source_artifact_id": raw_id, "max_duration_s": cfg["MAX_SOURCE_DURATION_S"]})
    assert not out.successful()  # the task failed AFTER the atomic commit ...
    assert (await _state(job_id))[0] == "NORMALIZED"       # ... normalization is durable ...
    it = await _intent(job_id)
    assert it.state == "PENDING" and it.dispatch_count == 0  # ... and so is the intent
    sent = []
    async with session_scope() as s:
        rep = await dispatch_intents.reconcile(s, lambda n, k, tid, q: sent.append((n, k, tid, q)))
        await s.commit()
    assert rep.resubmitted_pending == 1 and sent[0][2] == it.task_id and sent[0][3] == "cpu"
    assert (await _intent(job_id)).state == "DISPATCHED"


async def test_normalization_failure_inside_the_atomic_txn_leaves_no_partial_state(
    client, auth_headers, settings, monkeypatch,
):
    from app.db import session_scope
    from app.models import Artifact
    from shorts_config import load_config

    from workers.shared import dispatch_intents
    from workers.shared.celery_app import make_celery_app

    job_id, svid, key, raw_id = await _task_job(client, auth_headers, settings)
    app = make_celery_app(settings.redis_url)

    async def boom(*a, **k):
        raise RuntimeError("db write failed")
    monkeypatch.setattr(dispatch_intents, "create_intent", boom)
    cfg = load_config()
    out = await _run_normalize_task(app, {"job_id": job_id, "source_video_id": svid, "source_storage_key": key,
                                          "source_artifact_id": raw_id, "max_duration_s": cfg["MAX_SOURCE_DURATION_S"]})
    assert not out.successful()
    assert (await _state(job_id))[0] == "NORMALIZING" and await _intent(job_id) is None
    async with session_scope() as s:
        n = len((await s.scalars(select(Artifact).where(Artifact.job_id == uuid.UUID(job_id)))).all())
    assert n == 0  # normalized artifacts + manifest rolled back with the state change


async def test_reconciler_lease_expiry_orphans_closure_and_no_double_dispatch(client, auth_headers, settings, tmp_path):
    from datetime import UTC, datetime, timedelta

    from app.db import session_scope
    from app.models import Phase3DispatchIntent

    from workers.shared import dispatch_intents

    job_id, _svid, _cfg = await _normalized_job(client, auth_headers, settings, SPEECH, strip_audio=False,
                                              tmp_path=tmp_path)
    sent = []
    send = lambda n, k, tid, q: sent.append(tid)
    now = datetime.now(UTC)
    # (1) NORMALIZED job with NO intent (e.g. pre-fix / lost row) -> intent created and dispatched
    async with session_scope() as s:
        rep = await dispatch_intents.reconcile(s, send, now=now)
        await s.commit()
    assert (rep.created, rep.resubmitted_pending) == (1, 1) and len(sent) == 1
    # (2) fresh lease -> NOT resubmitted (a live Phase-3 task is never raced)
    async with session_scope() as s:
        rep = await dispatch_intents.reconcile(s, send, now=now + timedelta(seconds=30))
        await s.commit()
    assert (rep.resubmitted_pending, rep.resubmitted_expired) == (0, 0) and len(sent) == 1
    # (3) heartbeat extends the lease; RUNNING + expired lease -> resubmitted
    async with session_scope() as s:
        await dispatch_intents.claim_running(s, job_id=job_id, now=now)
        await dispatch_intents.heartbeat(s, job_id=job_id, now=now + timedelta(seconds=50))
        await s.commit()
    async with session_scope() as s:
        rep = await dispatch_intents.reconcile(s, send, now=now + timedelta(seconds=100))
        await s.commit()
    assert rep.resubmitted_expired == 0  # lease runs to now+110
    async with session_scope() as s:
        rep = await dispatch_intents.reconcile(s, send, now=now + timedelta(seconds=111))
        await s.commit()
    assert rep.resubmitted_expired == 1 and len(sent) == 2 and sent[0] == sent[1]  # same deterministic task id
    # (4) job left NORMALIZED -> intent closed, never resubmitted
    from workers.shared.job_state import transition_job_state
    async with session_scope() as s:
        await transition_job_state(s, job_id=job_id, from_state="NORMALIZED", to_state="ANALYZING")
        await s.commit()
    async with session_scope() as s:
        rep = await dispatch_intents.reconcile(s, send, now=now + timedelta(hours=1))
        await s.commit()
    assert rep.closed == 1 and len(sent) == 2
    async with session_scope() as s:
        assert (await s.scalar(select(Phase3DispatchIntent))).state == "COMPLETED"


async def test_phase3_completion_closes_the_intent(client, auth_headers, settings, tmp_path):
    from app.db import session_scope

    from workers.cpu.stage_transcript import run_phase3
    from workers.gpu.backends import Backends
    from workers.shared import dispatch_intents

    job_id, svid, cfg = await _normalized_job(client, auth_headers, settings, SPEECH, strip_audio=False, tmp_path=tmp_path)
    async with session_scope() as s:
        await dispatch_intents.create_intent(s, job_id=job_id, source_video_id=svid, task_id="t" * 64)
        await s.commit()
    async with session_scope() as session:
        d, _, _ = _deps(session, cfg, settings, Backends(FakeASR(), FakeAlign(), FakeDiar()))
        await run_phase3(d, job_id=job_id, source_video_id=svid)
        await session.commit()
    assert (await _intent(job_id)).state == "COMPLETED"


async def test_media_manifest_is_written_and_valid_with_real_cfr_decision(client, auth_headers, settings, tmp_path):
    from app.db import session_scope
    from app.models import Artifact
    from app.storage import build_storage_adapter

    job_id, svid, cfg = await _normalized_job(client, auth_headers, settings, SPEECH, strip_audio=False, tmp_path=tmp_path)
    schema = json.loads(Path("packages/schemas/json/media_manifest_v1.schema.json").read_text())
    async with session_scope() as s:
        rows = (await s.scalars(select(Artifact).where(Artifact.job_id == uuid.UUID(job_id)))).all()
        raw = (await s.execute(select(Artifact).where(Artifact.source_video_id == uuid.UUID(svid)))).scalar_one()
    by = {a.artifact_type: a for a in rows}
    man = json.loads(build_storage_adapter(settings, bucket_kind="artifacts").read_bytes(by["media_manifest_v1"].storage_location))
    jsonschema.Draft202012Validator(schema).validate(man)
    assert man["source"] == {"artifact_id": str(raw.id), "sha256": raw.checksum}
    assert man["audio_presence"] == "present" and man["analysis_audio"]["status"] == "created"
    assert man["normalized_video"]["object"]["artifact_id"] == str(by["normalized_media"].id)  # deterministic ids line up
    assert man["analysis_audio"]["object"]["sha256"] == by["analysis_audio"].checksum
    assert man["cfr"]["frame_count"] > 0 and man["cfr"]["selected_normalized_fps"] in (24, 25, 30, 50, 60)
    assert man["cfr"]["reason"] in {"cfr_eligible", "variable_deltas", "fps_not_eligible", "non_positive_delta"}
    assert man["config_sha256"] == cfg.config_sha256
    assert "-r" in man["provenance"]["ffmpeg_argv"]["normalize"]


async def test_manifest_for_silent_source_records_not_applicable(client, auth_headers, settings, tmp_path):
    from app.db import session_scope
    from app.models import Artifact
    from app.storage import build_storage_adapter

    job_id, _svid, _cfg = await _normalized_job(client, auth_headers, settings, EVENT, strip_audio=True, tmp_path=tmp_path)
    schema = json.loads(Path("packages/schemas/json/media_manifest_v1.schema.json").read_text())
    async with session_scope() as s:
        a = (await s.scalars(select(Artifact).where(Artifact.job_id == uuid.UUID(job_id),
                                                    Artifact.artifact_type == "media_manifest_v1"))).one()
    man = json.loads(build_storage_adapter(settings, bucket_kind="artifacts").read_bytes(a.storage_location))
    jsonschema.Draft202012Validator(schema).validate(man)
    assert man["audio_presence"] == "no_audio_stream"
    assert man["analysis_audio"] == {"status": "not_applicable", "object": None, "probe": None}


# ======================= 2026-10-04 decisions =====================================================

async def _full_run(client, auth_headers, settings, tmp_path, backends=None, strip_audio=False):
    from app.db import session_scope

    from workers.cpu.stage_transcript import run_phase3
    from workers.gpu.backends import Backends

    job_id, svid, cfg = await _normalized_job(
        client, auth_headers, settings, EVENT if strip_audio else SPEECH, strip_audio=strip_audio, tmp_path=tmp_path)
    async with session_scope() as session:
        d, gpu, storage = _deps(session, cfg, settings, backends or Backends(FakeASR(), FakeAlign(), FakeDiar()))
        tid = await run_phase3(d, job_id=job_id, source_video_id=svid)
        await session.commit()
    return job_id, svid, cfg, tid, gpu, storage


async def test_substeps_are_linked_to_the_one_canonical_artifact_and_stage_is_analyzing(
    client, auth_headers, settings, tmp_path,
):
    from app.db import session_scope
    from app.models import Artifact, StageRun

    job_id, _svid, _cfg, tid, _gpu, _st = await _full_run(client, auth_headers, settings, tmp_path)
    async with session_scope() as s:
        art = await s.get(Artifact, uuid.UUID(tid))
        runs = (await s.scalars(select(StageRun).where(StageRun.job_id == uuid.UUID(job_id)))).all()
    assert art.stage == "ANALYZING"  # amended v5.0 2.25: the orchestrated stage, not a sub-step
    subs = {r.stage_name: r for r in runs if r.stage_name in
            {"asr", "language_gate", "forced_alignment", "diarization", "sentence_segmentation"}}
    assert set(subs) == {"asr", "language_gate", "forced_alignment", "diarization", "sentence_segmentation"}
    for r in subs.values():
        assert r.status == "SUCCEEDED" and r.stage_version and r.config_sha256
        assert r.execution_metadata["canonical_artifact_id"] == tid and r.execution_metadata["parent_stage"] == "ANALYZING"
    assert subs["language_gate"].execution_metadata["execution"]["language_id_adapter"] is None  # fake backend has none
    assert subs["sentence_segmentation"].output_artifact_ids == [tid]


async def test_control_plane_rejects_tampered_or_foreign_transport_output(client, auth_headers, settings, tmp_path):
    from app.db import session_scope

    from workers.cpu.stage_transcript import _read_envelope
    from workers.shared.failures import StageFailure

    job_id, svid, cfg, _tid, _gpu, storage = await _full_run(client, auth_headers, settings, tmp_path)
    async with session_scope() as s:
        d, _, _ = _deps(s, cfg, settings, None)
        from app.models import StageRun
        asr = (await s.scalars(select(StageRun).where(StageRun.job_id == uuid.UUID(job_id),
                                                      StageRun.stage_name == "asr"))).one()
        meta = asr.execution_metadata
        _read_envelope(d, meta, expected_stage="asr", source_video_id=svid)  # control: valid
        with pytest.raises(StageFailure, match="descriptor_invalid"):  # wrong stage
            _read_envelope(d, meta, expected_stage="diarization", source_video_id=svid)
        with pytest.raises(StageFailure, match="descriptor_invalid"):  # another video's envelope
            _read_envelope(d, meta, expected_stage="asr", source_video_id=str(uuid.uuid4()))
        evil = {"output": {**meta["output"], "kind": "transcript_v1"}}
        with pytest.raises(StageFailure, match="descriptor_invalid"):
            _read_envelope(d, evil, expected_stage="asr", source_video_id=svid)
        key = meta["output"]["storage_location"]
        storage.inner.write_bytes(key, b'{"tampered": true}')
        with pytest.raises(StageFailure, match="checksum_mismatch"):
            _read_envelope(d, meta, expected_stage="asr", source_video_id=svid)


async def test_gpu_worker_rejects_unauthorized_inputs_and_foreign_transport_inputs(
    client, auth_headers, settings, tmp_path,
):
    from app.db import session_scope
    from app.models import Artifact

    from workers.gpu.backends import Backends
    from workers.gpu.execute import run_gpu_task

    job_id, svid, cfg, _tid, _gpu, storage = await _full_run(client, auth_headers, settings, tmp_path)
    async with session_scope() as s:
        rows = {a.artifact_type: a for a in (await s.scalars(select(Artifact).where(Artifact.job_id == uuid.UUID(job_id)))).all()}
        be = Backends(FakeASR(), FakeAlign(), FakeDiar())
        # two inputs -> not the approved shape
        r = await run_gpu_task(s, task_name="asr", input_artifact_ids=[str(rows["analysis_audio"].id), str(rows["media_manifest_v1"].id)],
                               cfg=cfg, backends=be, artifact_storage=storage)
        assert r["status"] == "error" and r["reason"] == "unauthorized_input_artifact"
        # a non-audio artifact alone -> not an approved input type
        r = await run_gpu_task(s, task_name="asr", input_artifact_ids=[str(rows["media_manifest_v1"].id)],
                               cfg=cfg, backends=be, artifact_storage=storage)
        assert r["status"] == "error" and r["reason"] == "analysis_audio_missing"
        # alignment fed another video's ASR envelope
        r = await run_gpu_task(
            s, task_name="forced_alignment", input_artifact_ids=[str(rows["analysis_audio"].id)], cfg=cfg, backends=be,
            artifact_storage=storage,
            transport_inputs={"asr": {"storage_location": f"transport/{uuid.uuid4()}/asr/{'a' * 64}.json", "checksum": "a" * 64}})
        assert r["status"] == "error" and r["reason"] == "unauthorized_transport_input"
    assert svid  # silence unused


async def test_dispatch_effective_lease_and_interval_are_persisted(client, auth_headers, settings, monkeypatch):
    from shorts_config import load_config

    from workers.shared.celery_app import make_celery_app

    job_id, svid, key, raw_id = await _task_job(client, auth_headers, settings)
    app = make_celery_app(settings.redis_url)
    monkeypatch.setattr(app, "send_task", lambda name, **kw: None)
    cfg = load_config()
    out = await _run_normalize_task(app, {"job_id": job_id, "source_video_id": svid, "source_storage_key": key,
                                          "source_artifact_id": raw_id, "max_duration_s": cfg["MAX_SOURCE_DURATION_S"]})
    assert out.successful(), out.traceback
    it = await _intent(job_id)
    assert (it.lease_s, it.reconcile_interval_s) == (60, 15)
    assert (it.lease_expires_at - it.last_heartbeat_at).total_seconds() == 60


async def test_transport_objects_are_registered_and_never_listed_as_artifacts(client, auth_headers, settings, tmp_path):
    from app.db import session_scope
    from app.models import Artifact, TransportObject

    job_id, _svid, _cfg, _tid, _gpu, storage = await _full_run(client, auth_headers, settings, tmp_path)
    async with session_scope() as s:
        objs = (await s.scalars(select(TransportObject).where(TransportObject.job_id == uuid.UUID(job_id)))).all()
        arts = (await s.scalars(select(Artifact).where(Artifact.job_id == uuid.UUID(job_id)))).all()
    assert {o.stage for o in objs} == {"asr", "forced_alignment", "diarization"}
    assert all(o.storage_location.startswith("transport/") and o.cleanup_result == "pending" for o in objs)
    assert not any(a.storage_location.startswith("transport/") or "phase3_stage_output" in a.artifact_type for a in arts)
    assert all(storage.inner.object_exists(o.storage_location) for o in objs)


async def test_retention_success_path_24h_after_materialization_and_canonical_untouched(
    client, auth_headers, settings, tmp_path,
):
    from datetime import UTC, datetime, timedelta

    from app.db import session_scope
    from app.models import Artifact, TransportObject

    from workers.shared import transport_retention

    job_id, _svid, _cfg, tid, _gpu, storage = await _full_run(client, auth_headers, settings, tmp_path)
    async with session_scope() as s:
        t = await s.get(Artifact, uuid.UUID(tid))
        sha_before, loc = t.checksum, t.storage_location
        created = t.created_at
    bytes_before = storage.inner.read_bytes(loc)
    # not yet due (23 h after materialization): deadline set, nothing deleted
    async with session_scope() as s:
        rep = await transport_retention.sweep(s, storage.inner, now=created + timedelta(hours=23))
        await s.commit()
    assert (rep.deadlines_set, rep.deleted, rep.not_due) == (3, 0, 3)
    async with session_scope() as s:
        objs = (await s.scalars(select(TransportObject).where(TransportObject.job_id == uuid.UUID(job_id)))).all()
    assert all(abs((o.retain_until - (created + timedelta(hours=24))).total_seconds()) < 1 for o in objs)
    assert all(o.retention_policy["basis"] == "success" and o.retention_policy["success_h"] == 24 for o in objs)
    assert all(storage.inner.object_exists(o.storage_location) for o in objs)
    # due: deleted, attempts / result recorded, idempotent on repeat
    async with session_scope() as s:
        rep = await transport_retention.sweep(s, storage.inner, now=created + timedelta(hours=24, seconds=5))
        await s.commit()
    assert rep.deleted == 3
    async with session_scope() as s:
        objs = (await s.scalars(select(TransportObject).where(TransportObject.job_id == uuid.UUID(job_id)))).all()
        rep2 = await transport_retention.sweep(s, storage.inner, now=created + timedelta(days=30))
        await s.commit()
    assert rep2.deleted == 0 and all(o.cleanup_result == "deleted" and o.cleanup_attempts == 1 and o.deleted_at for o in objs)
    assert not any(storage.inner.object_exists(o.storage_location) for o in objs)
    # canonical artifacts and hashes untouched
    async with session_scope() as s:
        t = await s.get(Artifact, uuid.UUID(tid))
    assert t.checksum == sha_before and storage.inner.read_bytes(loc) == bytes_before
    _ = datetime.now(UTC)


async def test_phase3_rerun_after_transport_deletion_is_idempotent(client, auth_headers, settings, tmp_path):
    from datetime import timedelta

    from app.db import session_scope
    from app.models import Artifact

    from workers.cpu.stage_transcript import run_phase3
    from workers.gpu.backends import Backends
    from workers.shared import transport_retention

    job_id, svid, cfg, tid, _gpu, storage = await _full_run(client, auth_headers, settings, tmp_path)
    async with session_scope() as s:
        created = (await s.get(Artifact, uuid.UUID(tid))).created_at
        await transport_retention.sweep(s, storage.inner, now=created + timedelta(days=2))
        await s.commit()
    async with session_scope() as session:
        d, gpu2, _ = _deps(session, cfg, settings, Backends(FakeASR(), FakeAlign(), FakeDiar()))
        again = await run_phase3(d, job_id=job_id, source_video_id=svid)
        await session.commit()
    assert again == tid and gpu2.submitted == []


async def test_retention_failed_job_7_days_and_active_jobs_never_deleted(client, auth_headers, settings, tmp_path):
    from datetime import timedelta

    from app.db import session_scope
    from app.models import ProcessingJob, TransportObject

    from workers.gpu.backends import Backends
    from workers.shared import transport_retention
    from workers.shared.failures import FailureKind

    # alignment succeeds but the job later fails? -> use a job whose diarization/ASR ran then alignment failed
    job_id, _svid, _cfg, tid, _gpu, storage = await _full_run(
        client, auth_headers, settings, tmp_path, Backends(FakeASR(), FakeAlign(fail_kind=FailureKind.PERMANENT_MODEL), FakeDiar()))
    assert tid is None
    async with session_scope() as s:
        job = await s.get(ProcessingJob, uuid.UUID(job_id))
        assert job.state == "FAILED"
        failed_at = job.updated_at
        objs = (await s.scalars(select(TransportObject).where(TransportObject.job_id == uuid.UUID(job_id)))).all()
    assert {o.stage for o in objs} == {"asr"}  # only the successful envelope exists
    async with session_scope() as s:
        rep = await transport_retention.sweep(s, storage.inner, now=failed_at + timedelta(days=6, hours=23))
        await s.commit()
    assert rep.deleted == 0 and rep.not_due == 1
    async with session_scope() as s:
        rep = await transport_retention.sweep(s, storage.inner, now=failed_at + timedelta(days=7, minutes=1))
        await s.commit()
    assert rep.deleted == 1
    # an ACTIVE job (still NORMALIZED, no transcript): never deleted, no deadline set
    from app.models import TransportObject as TO
    job2, svid2, cfg2 = await _normalized_job(client, auth_headers, settings, SPEECH, strip_audio=False, tmp_path=tmp_path / "b")
    async with session_scope() as s:
        s.add(TO(job_id=job2, source_video_id=svid2, stage="asr", storage_location=f"transport/{svid2}/asr/{'b' * 64}.json",
                 checksum="b" * 64))
        await s.commit()
    storage.inner.write_bytes(f"transport/{svid2}/asr/{'b' * 64}.json", b"x")
    async with session_scope() as s:
        rep = await transport_retention.sweep(s, storage.inner, now=failed_at + timedelta(days=365))
        await s.commit()
    assert (rep.deleted, rep.skipped_active) == (0, 1) and storage.inner.object_exists(f"transport/{svid2}/asr/{'b' * 64}.json")
    assert cfg2


async def test_retention_cancelled_7d_running_stage_blocks_and_cleanup_failure_is_recorded(
    client, auth_headers, settings, tmp_path,
):
    from datetime import timedelta

    from app.db import session_scope
    from app.models import ProcessingJob, StageRun, TransportObject

    from workers.shared import transport_retention

    job_id, svid, cfg = await _normalized_job(client, auth_headers, settings, SPEECH, strip_audio=False, tmp_path=tmp_path)
    loc = f"transport/{svid}/asr/{'c' * 64}.json"
    async with session_scope() as s:
        s.add(TransportObject(job_id=uuid.UUID(job_id), source_video_id=uuid.UUID(svid), stage="asr", storage_location=loc, checksum="c" * 64))
        await s.commit()
    from app.storage import build_storage_adapter
    storage = build_storage_adapter(settings, bucket_kind="artifacts")
    storage.write_bytes(loc, b"x")
    async with session_scope() as s:  # cancel the job
        job = await s.get(ProcessingJob, uuid.UUID(job_id))
        job.state = "CANCELLED"
        await s.commit()
    async with session_scope() as s:
        cancelled_at = (await s.get(ProcessingJob, uuid.UUID(job_id))).updated_at
    # a RUNNING stage run blocks deletion even past the deadline
    async with session_scope() as s:
        s.add(StageRun(job_id=uuid.UUID(job_id), stage_name="asr", stage_version="x", stage_input_sha256="d" * 64,
                       config_sha256="e" * 64, attempt=1, status="RUNNING", output_artifact_ids=[]))
        await s.commit()
    async with session_scope() as s:
        rep = await transport_retention.sweep(s, storage, now=cancelled_at + timedelta(days=8))
        await s.commit()
    assert rep.deleted == 0 and rep.skipped_active == 1 and storage.object_exists(loc)
    async with session_scope() as s:
        for r in (await s.scalars(select(StageRun).where(StageRun.job_id == uuid.UUID(job_id)))).all():
            r.status = "SUCCEEDED"
        await s.commit()

    class Exploding:
        def object_exists(self, k): return True
        def delete_object(self, k): raise OSError("storage unavailable")
    async with session_scope() as s:
        rep = await transport_retention.sweep(s, Exploding(), now=cancelled_at + timedelta(days=7, minutes=1))
        await s.commit()
    assert rep.failed == 1
    async with session_scope() as s:
        o = (await s.scalars(select(TransportObject).where(TransportObject.storage_location == loc))).one()
    assert (o.cleanup_result, o.cleanup_attempts) == ("failed", 1) and "storage unavailable" in o.cleanup_failure_reason
    assert o.retention_policy["basis"] == "cancelled" and o.retention_policy["cancelled_d"] == 7
    assert storage.object_exists(loc)  # failure never corrupts anything
    async with session_scope() as s:  # retried on the next sweep, then succeeds
        rep = await transport_retention.sweep(s, storage, now=cancelled_at + timedelta(days=7, minutes=2))
        await s.commit()
    assert rep.deleted == 1 and not storage.object_exists(loc)
    assert cfg


async def test_retention_never_deletes_non_transport_keys(client, auth_headers, settings, tmp_path):
    from datetime import timedelta

    from app.db import session_scope
    from app.models import Artifact, TransportObject

    from workers.shared import transport_retention

    job_id, svid, _cfg, tid, _gpu, storage = await _full_run(client, auth_headers, settings, tmp_path)
    async with session_scope() as s:
        t = await s.get(Artifact, uuid.UUID(tid))
        created, canonical_key = t.created_at, t.storage_location
        s.add(TransportObject(job_id=uuid.UUID(job_id), source_video_id=uuid.UUID(svid), stage="asr",
                              storage_location=canonical_key, checksum="f" * 64))  # a corrupted registry row
        await s.commit()
    async with session_scope() as s:
        rep = await transport_retention.sweep(s, storage.inner, now=created + timedelta(days=3))
        await s.commit()
    assert rep.failed == 1 and storage.inner.object_exists(canonical_key)  # refused, canonical artifact intact
    with pytest.raises(ValueError):
        async with session_scope() as s:
            await transport_retention.register_transport_object(
                s, job_id=job_id, source_video_id=svid, stage="asr", storage_location=canonical_key, checksum="f" * 64)


# ======================= 2026-10-06 G3 freeze: identities flow into transcript_v1 ===================

async def test_pinned_model_identities_reach_the_transcript_provenance(client, auth_headers, settings, tmp_path):
    from app.db import session_scope
    from app.models import Artifact

    from workers.cpu.stage_transcript import run_phase3
    from workers.gpu.backends import Backends

    class IdASR(FakeASR):
        runtime_sha256 = "1" * 64
        model_sha256 = "2" * 64
        models = {"asr": {"model_id": "mobiuslabsgmbh/faster-whisper-large-v3-turbo", "revision": "0c94664" + "0" * 33, "sha256": "2" * 64},  # noqa: RUF012
                  "vad": {"model_id": "silero_vad_v6.onnx", "revision": None, "sha256": "3" * 64}}

    class IdAlign(FakeAlign):
        runtime_sha256 = "4" * 64
        model_sha256 = "5" * 64
        models = {"alignment": {"model_id": "facebook/wav2vec2-base-960h", "revision": "22aad52d" + "0" * 32, "sha256": "5" * 64}}  # noqa: RUF012

    class IdDiar(FakeDiar):
        runtime_sha256 = "6" * 64
        model_sha256 = None
        models = {"diarization": {"model_id": "pyannote/speaker-diarization-community-1", "revision": "3533c8cf" + "0" * 32, "sha256": None}}  # noqa: RUF012

    job_id, svid, cfg = await _normalized_job(client, auth_headers, settings, SPEECH, strip_audio=False, tmp_path=tmp_path)
    async with session_scope() as session:
        d, _, storage = _deps(session, cfg, settings, Backends(IdASR(), IdAlign(), IdDiar()))
        tid = await run_phase3(d, job_id=job_id, source_video_id=svid)
        await session.commit()
    async with session_scope() as s:
        art = await s.get(Artifact, uuid.UUID(tid))
    doc = json.loads(storage.inner.read_bytes(art.storage_location))
    jsonschema.Draft202012Validator(SCHEMA).validate(doc)
    mm_ = doc["provenance"]["model_manifest"]
    assert set(mm_) >= {"asr", "vad", "alignment", "diarization", "language_id"}
    assert mm_["vad"]["sha256"] == "3" * 64 and mm_["asr"]["revision"].startswith("0c94664")
    assert doc["provenance"]["asr"]["runtime_sha256"] == "1" * 64
    assert doc["provenance"]["alignment"]["runtime_sha256"] == "4" * 64
