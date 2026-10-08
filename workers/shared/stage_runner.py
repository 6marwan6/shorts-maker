"""Generic stage idempotency contract (impl plan §3.2). Every pipeline stage is a call to
`run_stage`: canonicalize input artifact IDs -> compute stage_input_sha256 -> look for an
existing SUCCEEDED StageRun with identical (stage_version, stage_input_sha256, config_sha256)
-> reuse it, else execute and persist a new StageRun row (+ Artifact rows the executor returns).

This module is infra-only. It knows nothing about what a stage computes; `execute` is supplied
by the caller (normalization in Phase 2, ASR in Phase 3, ...)."""
from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from app.models import Artifact, StageRun
from shorts_config import canonical_json, sha256_bytes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class ConfigIdentity:
    config_version: str
    config_sha256: str


def deterministic_task_id(*, job_id: str, stage_name: str, stage_input_sha256: str) -> str:
    """impl plan §3.3: Celery task IDs are deterministic from job_id + stage_name +
    stage_input_sha256, so at-least-once delivery is safe to execute twice."""
    return sha256_bytes(f"{job_id}:{stage_name}:{stage_input_sha256}".encode())


def compute_stage_input_sha256(input_artifact_ids: list[str], *, extra: dict | None = None) -> str:
    """Canonicalization = sorted artifact-ID list (order must never be a hidden dependency)
    plus any stage-specific non-artifact parameters the caller declares up front."""
    payload = {"input_artifact_ids": sorted(input_artifact_ids), "extra": extra or {}}
    return sha256_bytes(canonical_json(payload))


ARTIFACT_ID_NAMESPACE = uuid.UUID("6f1c2a7e-3b8d-4c55-9a10-5d2f8e7b4c01")


def deterministic_artifact_id(*, job_id: str, stage_input_sha256: str, artifact_type: str) -> uuid.UUID:
    """uuid5 over (job, stage input hash, artifact type): lets a stage embed its sibling artifacts'
    ids in another artifact (media_manifest_v1) before any row exists (owner #12)."""
    return uuid.uuid5(ARTIFACT_ID_NAMESPACE, f"{job_id}:{stage_input_sha256}:{artifact_type}")


@dataclass(frozen=True)
class NewArtifact:
    artifact_type: str
    stage: str
    stage_version: str
    schema_version: int
    storage_location: str
    checksum: str
    model_versions: dict[str, Any]
    artifact_id: uuid.UUID | None = None  # pre-assigned (deterministic) id, if the stage needs it early


@dataclass(frozen=True)
class StageOutcome:
    """What `execute` returns when a stage has non-artifact outputs / execution metadata
    (owner 2026-10-02 #6/#8). A plain list[NewArtifact] is still accepted."""
    artifacts: list[NewArtifact] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StageResult:
    artifact_ids: list[str]
    metadata: dict[str, Any]
    reused: bool


async def run_stage(
    session: AsyncSession, *, job_id: str, stage_name: str, stage_version: str,
    input_artifact_ids: list[str], config: ConfigIdentity,
    execute: Callable[[], Awaitable[list[NewArtifact]]], extra: dict | None = None,
) -> list[str]:
    return (await run_stage_ex(
        session, job_id=job_id, stage_name=stage_name, stage_version=stage_version,
        input_artifact_ids=input_artifact_ids, config=config, execute=execute, extra=extra)).artifact_ids


async def run_stage_ex(
    session: AsyncSession, *, job_id: str, stage_name: str, stage_version: str,
    input_artifact_ids: list[str], config: ConfigIdentity,
    execute: Callable[[], Awaitable[list[NewArtifact] | StageOutcome]], extra: dict | None = None,
) -> StageResult:
    stage_input_sha256 = compute_stage_input_sha256(input_artifact_ids, extra=extra)

    existing = await session.scalar(
        select(StageRun).where(
            StageRun.stage_version == stage_version,
            StageRun.stage_input_sha256 == stage_input_sha256,
            StageRun.config_sha256 == config.config_sha256,
            StageRun.status == "SUCCEEDED",
        ).order_by(StageRun.attempt.desc()).limit(1)
    )
    if existing is not None:
        return StageResult(list(existing.output_artifact_ids), dict(existing.execution_metadata or {}), True)

    prior_attempts = await session.scalar(
        select(StageRun).where(
            StageRun.stage_version == stage_version,
            StageRun.stage_input_sha256 == stage_input_sha256,
            StageRun.config_sha256 == config.config_sha256,
        ).order_by(StageRun.attempt.desc()).limit(1)
    )
    attempt = (prior_attempts.attempt + 1) if prior_attempts else 1

    run = StageRun(
        job_id=job_id, stage_name=stage_name, stage_version=stage_version,
        stage_input_sha256=stage_input_sha256, config_sha256=config.config_sha256,
        status="RUNNING", attempt=attempt, output_artifact_ids=[],
    )
    session.add(run)
    await session.flush()

    try:
        outcome = await execute()
    except Exception as exc:
        run.status = "FAILED"
        run.failure_taxonomy = getattr(exc, "kind", "PERMANENT_MODEL")
        run.failure_reason = str(exc)[:2000]
        partial = getattr(exc, "execution_metadata", None)
        if partial:
            run.execution_metadata = partial  # effective polling/timeout survive a failed run
        await session.flush()
        raise

    new_artifacts = outcome.artifacts if isinstance(outcome, StageOutcome) else outcome
    metadata = dict(outcome.metadata) if isinstance(outcome, StageOutcome) else {}

    artifact_ids: list[str] = []
    for na in new_artifacts:
        art = Artifact(
            **({"id": na.artifact_id} if na.artifact_id is not None else {}),
            job_id=job_id, artifact_type=na.artifact_type, stage=na.stage,
            stage_version=na.stage_version, schema_version=na.schema_version,
            config_version=config.config_version, config_sha256=config.config_sha256,
            input_artifact_ids=input_artifact_ids, checksum=na.checksum,
            storage_location=na.storage_location, model_versions=na.model_versions,
        )
        session.add(art)
        await session.flush()
        artifact_ids.append(str(art.id))

    run.status = "SUCCEEDED"
    run.output_artifact_ids = artifact_ids
    run.execution_metadata = metadata
    await session.flush()
    return StageResult(artifact_ids, metadata, False)
