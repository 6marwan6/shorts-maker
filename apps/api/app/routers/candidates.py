from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings, get_settings
from ..db import get_session
from ..models import DisplaySelection, ProcessingJob, ReviewAction, ShortCandidate, User
from ..schemas import (
    CandidateEditRequest,
    CandidateReframeRequest,
    CandidateResponse,
    CandidateReviewActionRequest,
)
from ..tasks_client import get_task_client
from .auth import get_current_user

router = APIRouter(tags=["candidates"])


async def _get_owned_candidate(candidate_id: uuid.UUID, user: User, session: AsyncSession) -> ShortCandidate:
    candidate = await session.get(ShortCandidate, candidate_id)
    if candidate is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "candidate not found")
    job = await session.get(ProcessingJob, candidate.job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "candidate not found")
    return candidate


def _to_response(c: ShortCandidate) -> CandidateResponse:
    return CandidateResponse(id=c.id, job_id=c.job_id, state=c.state, comparability_class=c.comparability_class,
                              eligible=c.eligible, exclusion_reason=c.exclusion_reason)


@router.post("/v1/candidates/{candidate_id}/edit", response_model=CandidateResponse)
async def edit_candidate(
    candidate_id: uuid.UUID, body: CandidateEditRequest, user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings), session: AsyncSession = Depends(get_session),
):
    """v5.0 2.26.1: content edit -> new plan_origin=user_edit EditPlan lineage -> safe-boundary
    snap -> Layer 1 -> Layer 2 (speech-led, >=25 words) -> PASS=new verified descendant;
    REPAIRABLE/HARD_FAIL=BLOCKED_USER_EDIT, parent untouched, never auto-repaired.

    Phase 1 scope: validate the request, create the new EditPlan lineage row, transition the
    candidate to REVERIFYING, and enqueue the real verification work. The snap/Layer-1/Layer-2
    algorithms themselves are Phase 7/8 (workers.cpu.reverify_user_edit currently raises
    NotImplementedError by design, impl plan §13.4)."""
    candidate = await _get_owned_candidate(candidate_id, user, session)
    if candidate.state not in ("DISPLAYED",):
        raise HTTPException(status.HTTP_409_CONFLICT, f"candidate not editable in state {candidate.state}")

    new_lineage_id = uuid.uuid4()
    session.add(ReviewAction(user_id=user.id, short_candidate_id=candidate.id, action="edit",
                              request_body=body.model_dump(mode="json")))
    candidate.state = "USER_EDITING"
    await session.flush()
    candidate.state = "REVERIFYING"
    await session.commit()

    client = get_task_client(settings.redis_url)
    client.send_task(
        "workers.cpu.reverify_user_edit",
        kwargs={"short_candidate_id": str(candidate.id), "edit_plan_id": str(new_lineage_id)},
        queue="cpu",
    )
    return _to_response(candidate)


@router.post("/v1/candidates/{candidate_id}/reframe", response_model=CandidateResponse)
async def reframe_candidate(
    candidate_id: uuid.UUID, body: CandidateReframeRequest, user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings), session: AsyncSession = Depends(get_session),
):
    """v5.0 2.26.1: reframe-only edits never touch content/timing and skip content
    verification -- new reframe lineage only, no new EditPlan."""
    candidate = await _get_owned_candidate(candidate_id, user, session)
    session.add(ReviewAction(user_id=user.id, short_candidate_id=candidate.id, action="reframe",
                              request_body=body.model_dump(mode="json")))
    await session.commit()

    client = get_task_client(settings.redis_url)
    client.send_task(
        "workers.cpu.refresh_reframe_only",
        kwargs={"short_candidate_id": str(candidate.id), "strategy": body.strategy},
        queue="cpu",
    )
    return _to_response(candidate)


@router.post("/v1/candidates/{candidate_id}/accept", response_model=CandidateResponse)
async def accept_candidate(
    candidate_id: uuid.UUID, body: CandidateReviewActionRequest, user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    candidate = await _get_owned_candidate(candidate_id, user, session)
    if candidate.state != "DISPLAYED":
        raise HTTPException(status.HTTP_409_CONFLICT, f"candidate not acceptable in state {candidate.state}")
    session.add(ReviewAction(user_id=user.id, short_candidate_id=candidate.id, action="accept", reason=body.reason))
    candidate.state = "ACCEPTED"
    await session.commit()
    return _to_response(candidate)


@router.post("/v1/candidates/{candidate_id}/reject", response_model=CandidateResponse)
async def reject_candidate(
    candidate_id: uuid.UUID, body: CandidateReviewActionRequest, user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    candidate = await _get_owned_candidate(candidate_id, user, session)
    session.add(ReviewAction(user_id=user.id, short_candidate_id=candidate.id, action="reject", reason=body.reason))
    await session.commit()
    return _to_response(candidate)


@router.post("/v1/jobs/{job_id}/rerank", status_code=status.HTTP_201_CREATED)
async def rerank_job(job_id: uuid.UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """v5.0 2.26.1/2.39.8: the ONLY operation allowed to create a new display_selection_v1
    revision. Never modifies a prior selection row (impl plan §1.4)."""
    job = await session.get(ProcessingJob, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "job not found")
    from sqlalchemy import func, select
    last_revision = (await session.execute(
        select(func.max(DisplaySelection.revision)).where(DisplaySelection.job_id == job_id)
    )).scalar_one_or_none() or 0
    # Phase 1 scope: create the new immutable revision row; the actual MMR/display-selection
    # ALGORITHM (which candidates go into it) is Phase 11. selected_candidate_ids is empty
    # until that stage populates it.
    new_selection = DisplaySelection(
        job_id=job_id, revision=last_revision + 1, selected_candidate_ids=[],
        schema_version=1, stage_version="display_selection@1",
        config_version="pending-phase-11", config_sha256="0" * 64,
        artifact_id=uuid.uuid4(), checksum="0" * 64, storage_location="pending-phase-11",
    )
    session.add(new_selection)
    await session.commit()
    return {"job_id": str(job_id), "revision": new_selection.revision}
