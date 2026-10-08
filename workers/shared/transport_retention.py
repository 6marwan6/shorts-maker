"""Transport-object retention (owner decision 2026-10-04 #7). Operational, not config@1.

Defaults (Settings): successful terminal stage -> delete 24 h after the canonical artifact
(transcript_v1) was materialized; failed -> retain 7 days; cancelled -> retain 7 days;
pending/running -> never delete.

The sweep derives the state from the DB, so it needs no cooperation from the orchestrator beyond
the registry row written when a GPU output is accepted:
  * transcript_v1 exists for the job             -> success; deadline = materialized_at + 24 h
  * job.state == FAILED                          -> deadline = job.updated_at + 7 d
  * job.state == CANCELLED                       -> deadline = job.updated_at + 7 d
  * anything else                                -> active, never deleted
Before deleting, it re-checks that no stage run is RUNNING and no dispatch intent is
DISPATCHED/RUNNING for the job, that (success case) the canonical artifact really is materialized,
and that the deadline has passed. Deletion is idempotent and can never touch anything outside the
`transport/` prefix; a cleanup failure is recorded and never modifies canonical artifacts.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.models import Artifact, Phase3DispatchIntent, ProcessingJob, StageRun, TransportObject
from app.storage import StorageAdapter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

TRANSPORT_PREFIX = "transport/"
CANONICAL_TRANSCRIPT_TYPE = "transcript_v1"


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class RetentionPolicy:
    success_h: int
    failed_d: int
    cancelled_d: int

    @classmethod
    def from_settings(cls) -> RetentionPolicy:
        from app.config import get_settings
        st = get_settings()
        return cls(st.transport_retention_success_h, st.transport_retention_failed_d, st.transport_retention_cancelled_d)

    def as_dict(self) -> dict:
        return {"success_h": self.success_h, "failed_d": self.failed_d, "cancelled_d": self.cancelled_d}


async def register_transport_object(
    session: AsyncSession, *, job_id: str, source_video_id: str, stage: str, storage_location: str, checksum: str,
) -> None:
    """Idempotent (unique storage_location): a retried / re-validated output registers once."""
    if not storage_location.startswith(TRANSPORT_PREFIX):
        raise ValueError(f"not a transport key: {storage_location!r}")
    existing = await session.scalar(select(TransportObject).where(TransportObject.storage_location == storage_location))
    if existing is None:
        session.add(TransportObject(job_id=job_id, source_video_id=source_video_id, stage=stage,
                                    storage_location=storage_location, checksum=checksum))
        await session.flush()


@dataclass
class SweepReport:
    deadlines_set: int = 0
    deleted: int = 0
    failed: int = 0
    skipped_active: int = 0
    skipped_not_materialized: int = 0
    not_due: int = 0


async def _basis(session: AsyncSession, job: ProcessingJob, policy: RetentionPolicy):
    """(basis, base_time, delta) or (None, None, None) when the job is still active."""
    transcript = await session.scalar(select(Artifact).where(
        Artifact.job_id == job.id, Artifact.artifact_type == CANONICAL_TRANSCRIPT_TYPE))
    if transcript is not None:
        return "success", transcript.created_at, timedelta(hours=policy.success_h)
    if job.state == "FAILED":
        return "failed", job.updated_at, timedelta(days=policy.failed_d)
    if job.state == "CANCELLED":
        return "cancelled", job.updated_at, timedelta(days=policy.cancelled_d)
    return None, None, None


async def _active(session: AsyncSession, job_id) -> bool:
    running = await session.scalar(select(StageRun.id).where(StageRun.job_id == job_id, StageRun.status == "RUNNING").limit(1))
    intent = await session.scalar(select(Phase3DispatchIntent.id).where(
        Phase3DispatchIntent.job_id == job_id, Phase3DispatchIntent.state.in_(("DISPATCHED", "RUNNING"))).limit(1))
    return running is not None or intent is not None


async def sweep(
    session: AsyncSession, storage: StorageAdapter, *, now: datetime | None = None,
    policy: RetentionPolicy | None = None,
) -> SweepReport:
    now = now or _now()
    policy = policy or RetentionPolicy.from_settings()
    rep = SweepReport()
    rows = (await session.scalars(select(TransportObject).where(
        TransportObject.cleanup_result.in_(("pending", "failed"))))).all()
    for obj in rows:
        job = await session.get(ProcessingJob, obj.job_id)
        basis, base, delta = await _basis(session, job, policy) if job is not None else (None, None, None)
        if basis is None:
            rep.skipped_active += 1  # pending/running: never delete while the stage is active
            continue
        if obj.retain_until is None:  # retention timestamp, set once the terminal basis is known
            obj.retain_until = base + delta
            obj.retention_policy = {**policy.as_dict(), "basis": basis}
            rep.deadlines_set += 1
        if await _active(session, obj.job_id):
            rep.skipped_active += 1
            continue
        if basis == "success":
            # canonical artifact must be materialized AND readable before the transport copy may go
            t = await session.scalar(select(Artifact).where(
                Artifact.job_id == obj.job_id, Artifact.artifact_type == CANONICAL_TRANSCRIPT_TYPE))
            if t is None or not storage.object_exists(t.storage_location):
                rep.skipped_not_materialized += 1
                continue
        if obj.retain_until > now:
            rep.not_due += 1
            continue
        obj.cleanup_attempts += 1
        obj.last_cleanup_attempt_at = now
        try:
            if not obj.storage_location.startswith(TRANSPORT_PREFIX):
                raise ValueError("refusing to delete a non-transport key")
            storage.delete_object(obj.storage_location)  # idempotent: a missing object is success
            obj.cleanup_result, obj.cleanup_failure_reason, obj.deleted_at = "deleted", None, now
            rep.deleted += 1
        except Exception as exc:  # noqa: BLE001 -- a cleanup failure is recorded, never propagated
            obj.cleanup_result, obj.cleanup_failure_reason = "failed", f"{type(exc).__name__}: {exc}"[:500]
            rep.failed += 1
    await session.flush()
    return rep
