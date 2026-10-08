"""Phase 3 preflight (owner decisions C1, C2, C4, G4, G6, G7; 2026-10-02 #1,#5-#9).

The job STAYS in NORMALIZED while these stage_runs execute (no ASR/alignment/diarization job
state): asr -> language_gate -> forced_alignment -> diarization -> sentence_segmentation.
NORMALIZED -> ANALYZING only after the language gate passed AND (alignment succeeded OR ASR
produced zero words / there is no audio stream). Anything else -> FAILED.

Only `transcript_v1` is a canonical artifact. ASR / alignment / diarization results are internal
transport envelopes (#6): objects under `transport/`, described by descriptors recorded in
stage_runs.execution_metadata together with the EFFECTIVE polling / timeout / attempt values (#8).
The GPU worker never writes DB rows (#7); this control plane does.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

import jsonschema
from app.models import Artifact
from app.storage import StorageAdapter
from shorts_config import AlignmentUnavailable, Config, canonical_json, sha256_bytes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from workers.cpu.language_gate import LanguageIDBackend, language_gate_v1
from workers.cpu.transcript_builder import STAGE_VERSION as TRANSCRIPT_STAGE_VERSION
from workers.cpu.transcript_builder import build_transcript_v1
from workers.gpu.execute import STAGE_OUTPUT_TYPE, STAGE_OUTPUT_VERSION
from workers.shared import dispatch_intents, transport_retention
from workers.shared.artifact_keys import artifact_storage_key
from workers.shared.failures import FailureKind, StageFailure
from workers.shared.gpu_provider import (
    ConfigIdentity as GPUConfigIdentity,
)
from workers.shared.gpu_provider import GPUExecutionProvider, GPUJobState, GPUOutput
from workers.shared.job_state import transition_job_state
from workers.shared.stage_runner import (
    ConfigIdentity,
    NewArtifact,
    StageOutcome,
    compute_stage_input_sha256,
    deterministic_task_id,
    run_stage_ex,
)

ASR, LANG, ALIGN, DIAR, SEG = "asr", "language_gate", "forced_alignment", "diarization", "sentence_segmentation"
TRANSCRIPT_TYPE = "transcript_v1"
# Owner 2026-10-04 #3 (v5.0 2.25 amended): a `stage` is an orchestrated product-processing stage;
# asr / language_gate / forced_alignment / sentence_segmentation / diarization are SUB-STEPS of the
# ANALYZING stage. They keep their own stage_runs (status, failure reason, version, provenance,
# retry/idempotency) but only the stage's output, transcript_v1, is a canonical artifact.
PARENT_STAGE = "ANALYZING"
_ENVELOPE_SCHEMA = json.loads(
    (Path(__file__).resolve().parents[2] / "packages/schemas/json/internal/phase3_stage_output_v1.schema.json").read_text())


class Phase3Failed(Exception):
    def __init__(self, reason: str, kind: FailureKind):
        self.reason, self.kind = reason, kind
        super().__init__(f"{kind}:{reason}")


class _GPUStageFailure(StageFailure):
    """A StageFailure that carries the effective execution metadata of the failed run (#8)."""

    def __init__(self, kind, reason, detail="", execution_metadata=None):
        super().__init__(kind, reason, detail)
        self.execution_metadata = execution_metadata


@dataclass
class Phase3Deps:
    session: AsyncSession
    cfg: Config
    artifact_storage: StorageAdapter
    gpu: GPUExecutionProvider
    language_backend_factory: Callable[[], LanguageIDBackend]
    # Operational parameters (owner #8: NOT config@1; recorded in stage-run execution metadata).
    poll_interval_s: float = 1.0
    poll_timeout_s: float = 6 * 3600
    heartbeat: Callable[[], Awaitable[None]] | None = None  # lease heartbeat of the dispatch intent


async def _run_gpu(
    d: Phase3Deps, *, job_id: str, stage: str, input_ids: list[str], transport_inputs: dict | None = None,
    upstream: dict | None = None,
) -> tuple[GPUOutput, dict]:
    """Submit one GPU task and wait. Bounded attempts for TRANSIENT/TIMEOUT only (§3.4)."""
    cfgid = GPUConfigIdentity(d.cfg.config_version, d.cfg.config_sha256)
    meta = {"provider": getattr(d.gpu, "name", type(d.gpu).__name__), "poll_interval_s": d.poll_interval_s,
            "poll_timeout_s": d.poll_timeout_s, "max_attempts": d.cfg["STAGE_MAX_ATTEMPTS"],
            "attempts": 0, "provider_job_ids": []}
    last: StageFailure | None = None
    for attempt in range(1, d.cfg["STAGE_MAX_ATTEMPTS"] + 1):
        meta["attempts"] = attempt
        request_id = deterministic_task_id(
            job_id=job_id, stage_name=f"{stage}#gpu{attempt}",
            stage_input_sha256=compute_stage_input_sha256(input_ids, extra=upstream))
        handle = await d.gpu.submit(
            task_name=stage, input_artifact_ids=tuple(sorted(input_ids)), model_manifest={},
            config_identity=cfgid, request_id=request_id, transport_inputs=transport_inputs)
        meta["provider_job_ids"].append(handle.provider_job_id)  # opaque; stored, never parsed
        waited = 0.0
        while True:
            st = await d.gpu.get_status(provider_job_id=handle.provider_job_id)
            if st.state is GPUJobState.SUCCEEDED:
                return st.outputs[0], meta
            if st.state in (GPUJobState.FAILED, GPUJobState.CANCELLED):
                kind = FailureKind(st.failure_kind) if st.failure_kind else FailureKind.TRANSIENT
                last = _GPUStageFailure(kind, st.error or "gpu_failed", execution_metadata={"execution": meta})
                if kind in (FailureKind.TRANSIENT, FailureKind.TIMEOUT) and attempt < d.cfg["STAGE_MAX_ATTEMPTS"]:
                    break  # bounded retry
                raise last
            if waited >= d.poll_timeout_s:
                await d.gpu.cancel(provider_job_id=handle.provider_job_id)
                raise _GPUStageFailure(FailureKind.TIMEOUT, "gpu_poll_timeout", execution_metadata={"execution": meta})
            if d.heartbeat is not None:
                await d.heartbeat()
            await asyncio.sleep(d.poll_interval_s)
            waited += d.poll_interval_s
    assert last is not None
    raise last


def _descriptor(o: GPUOutput) -> dict:
    return {"kind": o.kind, "stage": o.stage, "schema_version": o.schema_version,
            "storage_location": o.storage_location, "checksum": o.checksum, "provenance": o.provenance}


async def _stage(session: AsyncSession, **kw):
    """run_stage_ex + commit. The commit is REQUIRED: the GPU worker reads input artifacts in its
    own DB session, and a stage's StageRun must be durable before the next stage builds on it."""
    res = await run_stage_ex(session, **kw)
    await session.commit()
    return res


def _read_envelope(d: Phase3Deps, meta: dict, *, expected_stage: str, source_video_id: str) -> dict:
    """Control-plane VALIDATION of a stage output (owner 2026-10-04 #5): inline (cheap CPU stages /
    no-audio) or a transport envelope whose descriptor, location, checksum, schema, stage and config
    identity are all verified before any of its data is trusted."""
    if "inline" in meta:
        return meta["inline"]
    desc = meta["output"]
    prefix = f"transport/{source_video_id}/{expected_stage}/"
    if desc.get("kind") != STAGE_OUTPUT_TYPE or desc.get("stage") != expected_stage \
            or not desc["storage_location"].startswith(prefix):
        raise StageFailure(FailureKind.PERMANENT_VALIDATION, "transport_output_descriptor_invalid", expected_stage)
    raw = d.artifact_storage.read_bytes(desc["storage_location"])
    if sha256_bytes(raw) != desc["checksum"] or not desc["storage_location"].endswith(f"/{desc['checksum']}.json"):
        raise StageFailure(FailureKind.PERMANENT_INPUT, "transport_envelope_checksum_mismatch", expected_stage)
    doc = json.loads(raw)
    try:
        jsonschema.Draft202012Validator(_ENVELOPE_SCHEMA).validate(doc)
    except jsonschema.ValidationError as exc:
        raise StageFailure(FailureKind.PERMANENT_VALIDATION, "transport_envelope_schema_invalid", exc.message[:200]) from exc
    if doc["stage"] != expected_stage or doc["status"] != "completed" or doc["config_sha256"] != d.cfg.config_sha256:
        raise StageFailure(FailureKind.PERMANENT_VALIDATION, "transport_envelope_identity_mismatch", expected_stage)
    return doc


async def _accept_output(d: Phase3Deps, *, job_id: str, source_video_id: str, stage: str, out: GPUOutput) -> dict:
    """Validate a provider output, then register it for retention (same transaction as the stage)."""
    meta = {"output": _descriptor(out)}
    _read_envelope(d, meta, expected_stage=stage, source_video_id=source_video_id)
    await transport_retention.register_transport_object(
        d.session, job_id=job_id, source_video_id=source_video_id, stage=stage,
        storage_location=out.storage_location, checksum=out.checksum)
    return meta["output"]


def _inline_doc(cfg: Config, **fields) -> dict:
    base = {"schema_version": 1, "stage_version": STAGE_OUTPUT_VERSION, "config_version": cfg.config_version,
            "config_sha256": cfg.config_sha256, "runtime_id": None, "runtime_sha256": None, "model_id": None,
            "model_revision": None, "model_sha256": None, "models": {}, "error_category": None, "segments": None, "words": None, "turns": None,
            "language": None}
    base.update(fields)
    return base


async def run_transcript_preflight(
    d: Phase3Deps, *, job_id: str, source_video_id: str, normalized_audio_artifact_id: str | None,
    normalization_artifact_ids: list[str],
) -> str:
    """Returns the transcript artifact id. Raises Phase3Failed on a terminal Phase-3 failure."""
    cfg, session = d.cfg, d.session
    # Idempotent re-entry (also after transport objects were retention-deleted): the canonical
    # artifact is the only thing a re-run needs.
    done = await session.scalar(select(Artifact).where(
        Artifact.job_id == job_id, Artifact.artifact_type == TRANSCRIPT_TYPE))
    if done is not None:
        return str(done.id)
    config = ConfigIdentity(cfg.config_version, cfg.config_sha256)
    in_ids = sorted(normalization_artifact_ids)
    audio_present = normalized_audio_artifact_id is not None
    audio_ids = [normalized_audio_artifact_id] if audio_present else in_ids
    manifest: dict = {}

    # ---- asr -----------------------------------------------------------------------------
    if not audio_present:  # G6: no audio stream -> no GPU call, zero-word result, inline
        async def exec_asr() -> StageOutcome:
            return StageOutcome([], {"inline": _inline_doc(cfg, stage="asr", status="not_applicable", segments=[]),
                                     "parent_stage": PARENT_STAGE})
        stage_ver = "asr_none@1"
    else:
        async def exec_asr() -> StageOutcome:
            out, meta = await _run_gpu(d, job_id=job_id, stage="asr", input_ids=audio_ids)
            desc = await _accept_output(d, job_id=job_id, source_video_id=source_video_id, stage="asr", out=out)
            return StageOutcome([], {"output": desc, "execution": meta, "parent_stage": PARENT_STAGE})
        stage_ver = "asr@1"
    try:
        asr_res = await _stage(session, job_id=job_id, stage_name=ASR, stage_version=stage_ver,
                               input_artifact_ids=audio_ids, config=config, execute=exec_asr)
    except StageFailure as exc:  # ASR is a prerequisite: no transcript -> job FAILED
        raise Phase3Failed(exc.reason, exc.kind) from exc
    asr_doc = _read_envelope(d, asr_res.metadata, expected_stage="asr", source_video_id=source_video_id)
    asr_sha = (asr_res.metadata.get("output") or {}).get("checksum") or sha256_bytes(canonical_json(asr_doc))
    segments = asr_doc["segments"] or []
    manifest.update(asr_doc.get("models") or {})  # asr (+ vad) pinned identities
    asr_word_count = sum(len(s["text"].split()) for s in segments)
    upstream = {"asr_sha256": asr_sha}

    # ---- language_gate (cheap CPU; result inline) -------------------------------------------
    async def exec_lang() -> StageOutcome:
        backend = d.language_backend_factory()  # constructed once (loads + verifies the model)
        res = language_gate_v1(segments, backend, cfg)
        lang = {"gate_status": res.gate_status, "code": res.code, "confidence": res.confidence,
                "model_id": res.model_id, "model_sha256": res.model_sha256, "sample_word_count": res.sample_word_count}
        return StageOutcome([], {"inline": _inline_doc(cfg, stage="language_gate", status="completed", language=lang),
                                 "parent_stage": PARENT_STAGE,
                                 "execution": {"language_id_adapter": getattr(backend, "adapter_version", None)}})
    try:
        lang_res = await _stage(session, job_id=job_id, stage_name=LANG, stage_version="language_gate@1",
                                input_artifact_ids=audio_ids, config=config, execute=exec_lang, extra=upstream)
    except StageFailure as exc:
        raise Phase3Failed(exc.reason, exc.kind) from exc
    language = lang_res.metadata["inline"]["language"]
    manifest["language_id"] = {"model_id": language["model_id"], "revision": None, "sha256": language["model_sha256"]}

    # ---- forced_alignment ----------------------------------------------------------------
    aligned_words: list[dict] | None = None
    align_prov: dict = {"runtime_id": None, "runtime_sha256": None}
    align_sha = None
    if asr_word_count > 0:
        async def exec_align() -> StageOutcome:
            out, meta = await _run_gpu(d, job_id=job_id, stage="forced_alignment", input_ids=audio_ids,
                                       transport_inputs={"asr": asr_res.metadata["output"]}, upstream=upstream)
            desc = await _accept_output(d, job_id=job_id, source_video_id=source_video_id, stage="forced_alignment", out=out)
            return StageOutcome([], {"output": desc, "execution": meta, "parent_stage": PARENT_STAGE})
        try:
            al_res = await _stage(session, job_id=job_id, stage_name=ALIGN, stage_version="forced_alignment@1",
                                  input_artifact_ids=audio_ids, config=config, execute=exec_align, extra=upstream)
        except StageFailure as exc:
            raise Phase3Failed("alignment_unavailable", exc.kind) from exc  # mandatory alignment unobtainable
        al = _read_envelope(d, al_res.metadata, expected_stage="forced_alignment", source_video_id=source_video_id)
        aligned_words = al["words"] or []
        if not aligned_words:
            raise Phase3Failed("alignment_unavailable", FailureKind.PERMANENT_MODEL)
        align_sha = al_res.metadata["output"]["checksum"]
        align_prov = {"runtime_id": al["runtime_id"], "runtime_sha256": al["runtime_sha256"]}
        manifest.update(al.get("models") or {})
        manifest.setdefault("alignment", {"model_id": al["model_id"] or "", "revision": al["model_revision"],
                                          "sha256": al.get("model_sha256")})

    # ---- diarization (attempted for every speech-bearing source; non-fatal: C1/C4) ------------
    diar: dict = {"attempted": False, "status": "not_applicable_no_speech", "missing_reason": None,
                  "provider": None, "model_id": None, "error_category": None, "turns": []}
    diar_sha = None
    if asr_word_count > 0:
        diar.update(attempted=True, provider="gpu_dispatch")
        try:
            async def exec_diar() -> StageOutcome:
                out, meta = await _run_gpu(d, job_id=job_id, stage="diarization", input_ids=audio_ids)
                desc = await _accept_output(d, job_id=job_id, source_video_id=source_video_id, stage="diarization", out=out)
                return StageOutcome([], {"output": desc, "execution": meta, "parent_stage": PARENT_STAGE})
            dz_res = await _stage(session, job_id=job_id, stage_name=DIAR, stage_version="diarization@1",
                                  input_artifact_ids=audio_ids, config=config, execute=exec_diar)
            dz = _read_envelope(d, dz_res.metadata, expected_stage="diarization", source_video_id=source_video_id)
            diar_sha = dz_res.metadata["output"]["checksum"]
            diar.update(status="succeeded", model_id=dz["model_id"], turns=dz["turns"] or [])
            manifest.update(dz.get("models") or {})
            manifest.setdefault("diarization", {"model_id": dz["model_id"] or "", "revision": dz["model_revision"],
                                                "sha256": dz.get("model_sha256")})
        except StageFailure as exc:
            if exc.kind is FailureKind.BLOCKED_BY_DEPENDENCY and "backend_unavailable" in exc.reason:
                diar.update(status="unavailable", missing_reason="not_available_in_stage",
                            attempted=False, error_category=exc.reason)
            else:  # attempted and the extractor/provider failed
                diar.update(status="failed", missing_reason="extraction_failed", error_category=str(exc.kind))

    # ---- sentence_segmentation + transcript_v1 (the only canonical Phase-3 artifact) ----------
    seg_extra = {**upstream, "language": language, "align_sha256": align_sha, "diar_sha256": diar_sha,
                 "diar_status": diar["status"]}
    input_sha = compute_stage_input_sha256(in_ids, extra=seg_extra)

    async def exec_seg() -> StageOutcome:
        doc = build_transcript_v1(
            cfg=cfg, source_video_id=source_video_id, input_sha256=input_sha, language=language,
            audio_availability="present" if audio_present else "not_applicable",
            asr={"status": "completed" if audio_present else "not_applicable_no_audio",
                 "runtime_id": asr_doc["runtime_id"], "runtime_sha256": asr_doc["runtime_sha256"],
                 "segment_count": len(segments), "word_count": asr_word_count},
            alignment_words=aligned_words, alignment=align_prov, diarization=diar, model_manifest=manifest)
        data = canonical_json(doc)
        sha = sha256_bytes(data)
        key = artifact_storage_key(source_video_id=source_video_id, artifact_type=TRANSCRIPT_TYPE,
                                   artifact_id=uuid.uuid4(), sha256=sha)
        d.artifact_storage.write_bytes(key, data)
        return StageOutcome([NewArtifact(TRANSCRIPT_TYPE, PARENT_STAGE, TRANSCRIPT_STAGE_VERSION, 1, key, sha, manifest)],
                            {"parent_stage": PARENT_STAGE})
    try:
        seg_res = await _stage(session, job_id=job_id, stage_name=SEG, stage_version="sentence_segmentation@1",
                               input_artifact_ids=in_ids, config=config, execute=exec_seg, extra=seg_extra)
    except AlignmentUnavailable as exc:
        raise Phase3Failed("alignment_unavailable", FailureKind.PERMANENT_MODEL) from exc
    canonical_id = seg_res.artifact_ids[0]
    await _link_substeps_to_canonical(session, job_id=job_id, canonical_artifact_id=canonical_id)
    return canonical_id


async def _link_substeps_to_canonical(session: AsyncSession, *, job_id: str, canonical_artifact_id: str) -> None:
    """Sub-step stage_runs reference the canonical artifact they contributed to (owner 2026-10-04 #3).
    Written into execution_metadata so output_artifact_ids keeps its single meaning (reuse key)."""
    from app.models import StageRun
    rows = (await session.scalars(select(StageRun).where(
        StageRun.job_id == job_id, StageRun.status == "SUCCEEDED",
        StageRun.stage_name.in_((ASR, LANG, ALIGN, DIAR, SEG))))).all()
    for r in rows:
        md = dict(r.execution_metadata or {})
        if md.get("canonical_artifact_id") != canonical_artifact_id:
            md["canonical_artifact_id"] = canonical_artifact_id
            r.execution_metadata = md
    await session.flush()
    await session.commit()


async def run_phase3(d: Phase3Deps, *, job_id: str, source_video_id: str) -> str | None:
    """Entry used by the Celery task. Claims the dispatch intent, runs the preflight, applies the
    NORMALIZED -> ANALYZING | FAILED transition and completes the intent. Idempotent."""
    await dispatch_intents.claim_running(d.session, job_id=job_id)
    await d.session.commit()
    rows = (await d.session.scalars(select(Artifact).where(
        Artifact.job_id == job_id, Artifact.stage == "NORMALIZING"))).all()
    audio = next((a for a in rows if a.artifact_type == "analysis_audio"), None)
    try:
        tid = await run_transcript_preflight(
            d, job_id=job_id, source_video_id=source_video_id,
            normalized_audio_artifact_id=str(audio.id) if audio else None,
            normalization_artifact_ids=[str(a.id) for a in rows])
    except Phase3Failed as exc:
        await transition_job_state(d.session, job_id=job_id, from_state="NORMALIZED", to_state="FAILED",
                                   error=f"{exc.reason} ({exc.kind})")
        await dispatch_intents.complete(d.session, job_id=job_id)
        await d.session.commit()
        return None
    await transition_job_state(d.session, job_id=job_id, from_state="NORMALIZED", to_state="ANALYZING")
    await dispatch_intents.complete(d.session, job_id=job_id)
    await d.session.commit()
    return tid
