"""Guarded job-state transitions (v5.0 2.25 states). Compare-and-set so at-least-once task
delivery can never move a job backwards or skip a state."""
from __future__ import annotations

from app.models import ProcessingJob
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession


async def transition_job_state(
    session: AsyncSession, *, job_id: str, from_state: str, to_state: str, error: str | None = None,
) -> bool:
    """True iff the row was in `from_state` and is now in `to_state`."""
    values: dict = {"state": to_state}
    if error is not None:
        values["error"] = error[:2000]
    res = await session.execute(
        update(ProcessingJob).where(ProcessingJob.id == job_id, ProcessingJob.state == from_state).values(**values))
    return res.rowcount == 1
