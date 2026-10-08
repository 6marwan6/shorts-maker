from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from shorts_config import canonical_json, load_config, sha256_bytes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings, get_settings
from ..db import get_session
from ..dispatch import dispatch_normalize_source_video
from ..models import Artifact, ProcessingJob, ShortCandidate, SourceVideo, User
from ..schemas import CandidateResponse, CreateJobRequest, JobResponse, JobStatusResponse
from .auth import get_current_user

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


def _export_profile_sha256(profile: dict) -> str:
    """impl plan §3.10: every plan-level artifact carries export_profile_id + its hash. Hashed
    with the same canonical_json/sha256 pair as config identity (packages/config), not a
    separately invented hashing scheme."""
    return sha256_bytes(canonical_json(dict(profile)))


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(body: CreateJobRequest, user: User = Depends(get_current_user),
                      settings: Settings = Depends(get_settings),
                      session: AsyncSession = Depends(get_session)):
    source_video = await session.get(SourceVideo, body.source_video_id)
    if source_video is None or source_video.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "source video not found")

    raw_artifact = await session.scalar(
        select(Artifact).where(Artifact.source_video_id == source_video.id,
                                Artifact.artifact_type == "raw_source"))
    if raw_artifact is None:
        # Should be unreachable: complete_upload always commits raw_source atomically with the
        # SourceVideo row. Treated as PERMANENT_VALIDATION rather than silently proceeding
        # without an input_artifact_id for NORMALIZING.
        raise HTTPException(status.HTTP_409_CONFLICT, "source video has no raw_source artifact")

    config = load_config()
    try:
        profile = config.profile(body.export_profile_id)  # raises ValueError: unknown/disabled
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from e

    job = ProcessingJob(
        user_id=user.id, source_video_id=source_video.id, state="CREATED",
        export_profile_id=body.export_profile_id,
        export_profile_sha256=_export_profile_sha256(profile),
        config_version=config.config_version, config_sha256=config.config_sha256,
    )
    session.add(job)
    # Step 1: persist and return CREATED. This commit is the durability boundary -- the job
    # unambiguously exists before we touch the queue (owner correction, this session: no single
    # transaction may span the DB commit and the broker enqueue). The response below reflects
    # exactly this state, per the agreed contract ("job creation returns CREATED"), regardless
    # of what step 2 does to the row afterward in this same call.
    await session.commit()
    await session.refresh(job)
    created_response = JobResponse(job_id=job.id, state=job.state)

    # Step 2: dispatch NORMALIZING as an independent step. `workers.shared.stage_runner`'s
    # compute_stage_input_sha256 is the single canonical hash function (also used inside the
    # task body's run_stage call), so the task_id the API computes here is exactly the ID the
    # worker will execute under.
    from workers.shared.stage_runner import compute_stage_input_sha256

    stage_input_sha256 = compute_stage_input_sha256([str(raw_artifact.id)])
    max_duration_s = config["MAX_SOURCE_DURATION_S"]
    dispatch_normalize_source_video(
        settings, job_id=str(job.id), source_video_id=str(source_video.id),
        source_storage_key=source_video.raw_storage_key, source_artifact_id=str(raw_artifact.id),
        stage_input_sha256=stage_input_sha256, max_duration_s=max_duration_s,
    )
    job.state = "NORMALIZING"
    await session.commit()
    return created_response



async def _get_owned_job(job_id: uuid.UUID, user: User, session: AsyncSession) -> ProcessingJob:
    job = await session.get(ProcessingJob, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "job not found")
    return job


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: uuid.UUID, user: User = Depends(get_current_user),
                   session: AsyncSession = Depends(get_session)):
    job = await _get_owned_job(job_id, user, session)
    return JobStatusResponse(job_id=job.id, state=job.state, error=job.error,
                              created_at=job.created_at, updated_at=job.updated_at)


@router.post("/{job_id}/cancel", response_model=JobStatusResponse)
async def cancel_job(job_id: uuid.UUID, user: User = Depends(get_current_user),
                      session: AsyncSession = Depends(get_session)):
    job = await _get_owned_job(job_id, user, session)
    if job.state in ("COMPLETED", "FAILED", "CANCELLED"):
        raise HTTPException(status.HTTP_409_CONFLICT, f"job already terminal: {job.state}")
    # impl plan §18.3: mark CANCELLED, revoke queued downstream work, never delete artifacts.
    # Actual Celery revocation is enqueued by the worker layer (Phase 5+); this router only
    # owns the authoritative state transition.
    job.state = "CANCELLED"
    await session.commit()
    await session.refresh(job)
    return JobStatusResponse(job_id=job.id, state=job.state, error=job.error,
                              created_at=job.created_at, updated_at=job.updated_at)


@router.get("/{job_id}/candidates", response_model=list[CandidateResponse])
async def list_candidates(job_id: uuid.UUID, user: User = Depends(get_current_user),
                           session: AsyncSession = Depends(get_session)):
    await _get_owned_job(job_id, user, session)
    rows = (await session.execute(
        select(ShortCandidate).where(ShortCandidate.job_id == job_id)
    )).scalars().all()
    # impl plan §6: "Returns candidates sorted by display_rank while exposing score_rank
    # separately." display_rank/score_rank live on tier2_scores (Phase 11); until that stage
    # exists, candidates sort by creation order and both rank fields are null.
    return [
        CandidateResponse(id=c.id, job_id=c.job_id, state=c.state, comparability_class=c.comparability_class,
                           eligible=c.eligible, exclusion_reason=c.exclusion_reason)
        for c in rows
    ]
