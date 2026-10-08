"""Durable Phase-3 dispatch (owner decision 2026-10-02 #9) -- a minimal outbox-like mechanism.

Contract
  * create_intent() runs in the SAME transaction as the normalization artifacts + the
    NORMALIZING->NORMALIZED transition; the caller commits once.
  * dispatch_intent() sends the Celery task THEN marks the intent DISPATCHED with a lease
    (send-then-mark = at-least-once; duplicates are safe: deterministic task id, idempotent stage
    runs, compare-and-set job transitions).
  * The Phase-3 task claims (RUNNING) and heartbeats the lease while it works, and marks the
    intent COMPLETED when Phase 3 reaches a terminal outcome (ANALYZING or FAILED).
  * reconcile() (periodic, `maintenance` queue) resubmits: PENDING intents; DISPATCHED/RUNNING
    intents whose lease expired while the job is still NORMALIZED; and NORMALIZED jobs with no
    intent at all. It closes intents whose job already left NORMALIZED.

Operational parameters (owner decision 2026-10-04 #2; NOT config@1): dispatch lease 60 s and
reconcile interval 15 s are `Settings.dispatch_lease_s` / `Settings.reconcile_interval_s`
(env SHORTS_MAKER_*). The effective values are persisted on the intent row at every dispatch and
returned by the reconciler. Phase 18 may revise them or replace this mechanism with the final
transactional outbox.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.models import Phase3DispatchIntent, ProcessingJob
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from workers.shared.stage_runner import compute_stage_input_sha256, deterministic_task_id

PHASE3_TASK_NAME = "workers.cpu.run_transcript_preflight"
HEARTBEAT_MIN_INTERVAL_S = 15  # lease-heartbeat throttle (operational; kept at the earlier 15 s)


def _settings():
    from app.config import get_settings
    return get_settings()


def effective_lease_s() -> int:
    return _settings().dispatch_lease_s


def effective_reconcile_interval_s() -> int:
    return _settings().reconcile_interval_s

SendFn = Callable[[str, dict, str, str], None]  # (task_name, kwargs, task_id, queue)


def phase3_task_id(job_id: str, normalization_artifact_ids: list[str]) -> str:
    return deterministic_task_id(
        job_id=job_id, stage_name="TRANSCRIPT_PREFLIGHT",
        stage_input_sha256=compute_stage_input_sha256(normalization_artifact_ids))


def _now() -> datetime:
    return datetime.now(UTC)


async def create_intent(session: AsyncSession, *, job_id: str, source_video_id: str, task_id: str) -> None:
    session.add(Phase3DispatchIntent(job_id=job_id, source_video_id=source_video_id, task_id=task_id, state="PENDING"))
    await session.flush()


async def dispatch_intent(
    session: AsyncSession, send: SendFn, intent: Phase3DispatchIntent, *, now: datetime | None = None,
    lease_s: int | None = None,
) -> None:
    now = now or _now()
    lease_s = effective_lease_s() if lease_s is None else lease_s
    send(PHASE3_TASK_NAME,
         {"job_id": str(intent.job_id), "source_video_id": str(intent.source_video_id)},
         intent.task_id, "cpu")
    intent.state = "DISPATCHED"
    intent.dispatch_count += 1
    intent.lease_s = lease_s
    intent.reconcile_interval_s = effective_reconcile_interval_s()
    intent.lease_expires_at = now + timedelta(seconds=lease_s)
    intent.last_heartbeat_at = now
    await session.flush()


async def claim_running(
    session: AsyncSession, *, job_id: str, now: datetime | None = None, lease_s: int | None = None,
) -> None:
    now = now or _now()
    lease_s = effective_lease_s() if lease_s is None else lease_s
    await session.execute(
        update(Phase3DispatchIntent)
        .where(Phase3DispatchIntent.job_id == job_id, Phase3DispatchIntent.state != "COMPLETED")
        .values(state="RUNNING", lease_expires_at=now + timedelta(seconds=lease_s), last_heartbeat_at=now))


async def heartbeat(
    session: AsyncSession, *, job_id: str, now: datetime | None = None, lease_s: int | None = None,
) -> None:
    """Short, independent transaction (own session) so it never waits on the stage transaction."""
    now = now or _now()
    lease_s = effective_lease_s() if lease_s is None else lease_s
    await session.execute(
        update(Phase3DispatchIntent)
        .where(Phase3DispatchIntent.job_id == job_id, Phase3DispatchIntent.state == "RUNNING")
        .values(lease_expires_at=now + timedelta(seconds=lease_s), last_heartbeat_at=now))


async def complete(session: AsyncSession, *, job_id: str) -> None:
    await session.execute(
        update(Phase3DispatchIntent).where(Phase3DispatchIntent.job_id == job_id).values(state="COMPLETED"))


@dataclass
class ReconcileReport:
    effective_lease_s: int = 0
    effective_reconcile_interval_s: int = 0
    created: int = 0
    resubmitted_pending: int = 0
    resubmitted_expired: int = 0
    closed: int = 0


async def reconcile(
    session: AsyncSession, send: SendFn, *, now: datetime | None = None, lease_s: int | None = None,
) -> ReconcileReport:
    """Safe to run concurrently with itself and with live Phase-3 tasks (leases + idempotency)."""
    from app.models import Artifact  # local import keeps module import light

    now = now or _now()
    lease_s = effective_lease_s() if lease_s is None else lease_s
    rep = ReconcileReport(effective_lease_s=lease_s, effective_reconcile_interval_s=effective_reconcile_interval_s())

    # 1. NORMALIZED jobs with no dispatch record at all -> create the missing intent.
    orphan_jobs = (await session.execute(
        select(ProcessingJob).where(
            ProcessingJob.state == "NORMALIZED",
            ~select(Phase3DispatchIntent.id).where(Phase3DispatchIntent.job_id == ProcessingJob.id).exists(),
        ))).scalars().all()
    for job in orphan_jobs:
        ids = [str(a.id) for a in (await session.scalars(select(Artifact).where(
            Artifact.job_id == job.id, Artifact.stage == "NORMALIZING"))).all()]
        await create_intent(session, job_id=str(job.id), source_video_id=str(job.source_video_id),
                            task_id=phase3_task_id(str(job.id), ids))
        rep.created += 1

    # 2. Pending / lease-expired intents of still-NORMALIZED jobs -> resubmit; others -> close.
    intents = (await session.scalars(
        select(Phase3DispatchIntent).where(Phase3DispatchIntent.state != "COMPLETED"))).all()
    for it in intents:
        job = await session.get(ProcessingJob, it.job_id)
        if job is None or job.state != "NORMALIZED":
            it.state = "COMPLETED"
            rep.closed += 1
            continue
        if it.state == "PENDING":
            await dispatch_intent(session, send, it, now=now, lease_s=lease_s)
            rep.resubmitted_pending += 1
        elif it.lease_expires_at is not None and it.lease_expires_at < now:
            await dispatch_intent(session, send, it, now=now, lease_s=lease_s)
            rep.resubmitted_expired += 1
    await session.flush()
    return rep
