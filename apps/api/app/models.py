"""SQLAlchemy models (impl plan Phase 1.2's migration list; impl plan §7 key relationships).

Design rule (impl plan §3.1 "Artifact immutability" + v5.0 2.25 "Artifacts should carry"):
content-addressed artifact JSON is the canonical record and lives in object storage at
`artifacts/{source_video_id}/{artifact_type}/{artifact_id}/{artifact_sha256}.json`
(impl plan §3.1). These tables are metadata/pointers + the columns actually needed for
querying and lifecycle state -- they do NOT duplicate each JSON Schema's full field set as
relational columns (packages/schemas/json/*.schema.json remains the one canonical schema for
artifact *content*, impl plan §4.3). Every table therefore carries the common
config/stage/schema identity columns (ArtifactEnvelopeMixin) plus only the columns a router or
worker actually needs to filter/join/transition on.

Rows are inserted, never mutated in place for the artifact-content fields (impl plan §3.1);
`updated_at` exists only on rows with real mutable lifecycle state (jobs, candidates, uploads).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class ArtifactEnvelopeMixin:
    """v5.0 2.25 'Artifacts should carry' + impl plan config-identity invariant (§0)."""

    schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    stage_version: Mapped[str] = mapped_column(String(128), nullable=False)
    config_version: Mapped[str] = mapped_column(String(64), nullable=False)
    config_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, unique=True, default=uuid.uuid4)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_location: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# --------------------------------------------------------------------------------------
# Users / auth
# --------------------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _uuid_pk()
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)  # Argon2id (impl plan §1.3)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RefreshToken(Base):
    """Rotating refresh tokens (impl plan §1.3). token_hash only -- the raw token is never
    stored, matching the same never-store-secrets-in-plaintext posture as R2/LLM credentials."""

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)  # sha256 hex
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("refresh_tokens.id"), nullable=True)


# --------------------------------------------------------------------------------------
# Source video / upload / job
# --------------------------------------------------------------------------------------

class SourceVideo(Base):
    __tablename__ = "source_videos"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    raw_storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UploadSession(Base):
    """Presigned-upload bookkeeping (impl plan §1.4 POST /v1/uploads, /v1/uploads/{id}/complete).
    Never proxies the upload body -- storage_key + presigned URL only (impl plan §1.6)."""

    __tablename__ = "upload_sessions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    declared_content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")  # PENDING | COMPLETED | EXPIRED
    source_video_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("source_videos.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


JOB_STATES = (
    "CREATED", "UPLOADING", "UPLOADED", "NORMALIZING", "NORMALIZED", "ANALYZING",
    "DISCOVERING_REGIONS", "QUALIFYING_REGIONS", "RANKING_REGIONS", "CLASSIFYING_STYLE",
    "PLANNING_EDITS", "VERIFYING_EDITS", "ANALYZING_HOOKS", "PLANNING_REFRAME",
    "RANKING_SHORTS", "READY_FOR_REVIEW", "RENDERING", "COMPLETED", "FAILED", "CANCELLED",
)  # v5.0 2.25 minimum job states, verbatim order


class ProcessingJob(Base):
    """Coarse job state machine (v5.0 2.25). Candidate-level lifecycle (2.26.1) is tracked on
    ShortCandidate.state instead -- impl plan §1.6/Phase 12: "do not overload the job state
    machine with per-candidate states."""

    __tablename__ = "processing_jobs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("source_videos.id"), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="CREATED")

    # impl plan §1.2/§3.10: exactly one immutable export profile per job.
    export_profile_id: Mapped[str] = mapped_column(String(64), nullable=False)
    export_profile_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    config_version: Mapped[str] = mapped_column(String(64), nullable=False)
    config_sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class StageRun(Base):
    """Stage idempotency record (impl plan §3.2): one row per
    (stage_version, stage_input_sha256, config_sha256) attempt."""

    __tablename__ = "stage_runs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False)
    stage_name: Mapped[str] = mapped_column(String(64), nullable=False)
    stage_version: Mapped[str] = mapped_column(String(128), nullable=False)
    stage_input_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    config_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="RUNNING")  # RUNNING|SUCCEEDED|FAILED
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    failure_taxonomy: Mapped[str | None] = mapped_column(String(32), nullable=True)  # impl plan §3.4
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_artifact_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # Execution metadata (owner decision 2026-10-02 #6/#8): non-artifact stage outputs (internal
    # transport-envelope descriptors, inline results of cheap CPU stages) and the EFFECTIVE
    # operational parameters of the run (GPU poll interval / timeout, attempts, provider job ids).
    execution_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("stage_version", "stage_input_sha256", "config_sha256", "attempt",
                          name="uq_stage_run_identity_attempt"),
    )


class Phase3DispatchIntent(Base):
    """Durable Phase-3 dispatch intent (owner decision 2026-10-02 #9). Written in the SAME
    transaction that persists the normalization artifacts and moves the job to NORMALIZED, so a
    crash can never leave a NORMALIZED job with no record that Phase 3 must run. A dispatcher
    sends the Celery task and marks the intent DISPATCHED (leased); a reconciler resubmits
    PENDING or lease-expired intents. Minimal mechanism: Phase 18 may replace it with the final
    transactional outbox.

    state: PENDING -> DISPATCHED -> RUNNING -> COMPLETED   (COMPLETED = terminal, success OR failure
    of Phase 3; the job's own state says which).
    """

    __tablename__ = "phase3_dispatch_intents"

    id: Mapped[uuid.UUID] = _uuid_pk()
    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False, unique=True)
    source_video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("source_videos.id", ondelete="CASCADE"), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING", index=True)
    task_id: Mapped[str] = mapped_column(String(64), nullable=False)  # deterministic Celery task id
    dispatch_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Effective operational values at the last dispatch (owner 2026-10-04 #2): auditable/reproducible.
    lease_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reconcile_interval_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Artifact(Base):
    """Generic artifact metadata pointer (impl plan §1.2 'artifacts' table; v5.0 2.25).

    Ownership is strict and mutually exclusive by convention (owner decision, this session):
      * artifact_type == "raw_source": source_video_id is set, job_id is NULL. Committed at
        upload-complete time, before any job exists.
      * every other artifact_type: job_id is set, source_video_id stays NULL (never populated
        "for convenience" -- source ownership belongs to raw_source only, job ownership to
        everything a job's stages produce).
    """

    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = _uuid_pk()
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=True)
    source_video_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("source_videos.id", ondelete="CASCADE"), nullable=True)
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False)  # matches a packages/schemas/json/*.schema.json title
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    stage_version: Mapped[str] = mapped_column(String(128), nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    config_version: Mapped[str] = mapped_column(String(64), nullable=False)
    config_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    input_artifact_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_location: Mapped[str] = mapped_column(Text, nullable=False)
    model_versions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# --------------------------------------------------------------------------------------
# Pipeline artifact tables (2.9 - 2.39): metadata envelope + queryable lifecycle columns only.
# Full content lives in the content-addressed JSON (packages/schemas/json/*.schema.json).
# --------------------------------------------------------------------------------------

class SourceRegion(ArtifactEnvelopeMixin, Base):
    __tablename__ = "source_regions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False)
    region_kind: Mapped[str] = mapped_column(String(16), nullable=False)  # speech_led | event_led
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)


class QualificationRecord(ArtifactEnvelopeMixin, Base):
    __tablename__ = "qualification_records"

    id: Mapped[uuid.UUID] = _uuid_pk()
    source_region_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("source_regions.id", ondelete="CASCADE"), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)


class EditPlan(ArtifactEnvelopeMixin, Base):
    __tablename__ = "edit_plans"

    id: Mapped[uuid.UUID] = _uuid_pk()
    source_region_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("source_regions.id", ondelete="CASCADE"), nullable=False)
    lineage_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    plan_origin: Mapped[str] = mapped_column(String(16), nullable=False)  # model | user_edit
    parent_edit_plan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("edit_plans.id"), nullable=True)
    intensity: Mapped[str] = mapped_column(String(16), nullable=False)


class VerifiedEditPlan(ArtifactEnvelopeMixin, Base):
    __tablename__ = "verified_edit_plans"

    id: Mapped[uuid.UUID] = _uuid_pk()
    edit_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("edit_plans.id", ondelete="CASCADE"), nullable=False)
    final_status: Mapped[str] = mapped_column(String(32), nullable=False)  # TRANSCRIPT_VERIFIED_PASS | LAYER1_ONLY_PASS


class ContentStyle(ArtifactEnvelopeMixin, Base):
    __tablename__ = "content_styles"

    id: Mapped[uuid.UUID] = _uuid_pk()
    source_region_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("source_regions.id", ondelete="CASCADE"), nullable=False)
    content_style: Mapped[str] = mapped_column(String(32), nullable=False)


class HookAnalysis(ArtifactEnvelopeMixin, Base):
    __tablename__ = "hook_analyses"

    id: Mapped[uuid.UUID] = _uuid_pk()
    verified_edit_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("verified_edit_plans.id", ondelete="CASCADE"), nullable=False)
    analysis_status: Mapped[str] = mapped_column(String(32), nullable=False)


class ReframePlan(ArtifactEnvelopeMixin, Base):
    __tablename__ = "reframe_plans"

    id: Mapped[uuid.UUID] = _uuid_pk()
    verified_edit_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("verified_edit_plans.id", ondelete="CASCADE"), nullable=False)
    reframe_lineage_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)  # ok | degraded | infeasible


class CaptionPlan(ArtifactEnvelopeMixin, Base):
    __tablename__ = "caption_plans"

    id: Mapped[uuid.UUID] = _uuid_pk()
    verified_edit_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("verified_edit_plans.id", ondelete="CASCADE"), nullable=False)
    caption_mode: Mapped[str] = mapped_column(String(16), nullable=False)  # burned_in | sidecar | none


SHORT_CANDIDATE_STATES = (
    "DISPLAYED", "USER_EDITING", "REVERIFYING", "BLOCKED_USER_EDIT", "ACCEPTED", "RENDERING", "RENDERED",
)  # v5.0 2.26.1


class ShortCandidate(ArtifactEnvelopeMixin, Base):
    __tablename__ = "short_candidates"

    id: Mapped[uuid.UUID] = _uuid_pk()
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False)
    verified_edit_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("verified_edit_plans.id", ondelete="CASCADE"), nullable=False)
    source_region_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("source_regions.id"), nullable=False)
    plan_origin: Mapped[str] = mapped_column(String(16), nullable=False)
    parent_short_candidate_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("short_candidates.id"), nullable=True)
    replaces_short_candidate_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("short_candidates.id"), nullable=True)
    comparability_class: Mapped[str] = mapped_column(String(4), nullable=False)  # A | B
    eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    exclusion_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="DISPLAYED")  # v5.0 2.26.1 candidate lifecycle
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Tier1Score(ArtifactEnvelopeMixin, Base):
    __tablename__ = "tier1_scores"

    id: Mapped[uuid.UUID] = _uuid_pk()
    source_region_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("source_regions.id", ondelete="CASCADE"), nullable=False)
    region_priority_score: Mapped[float] = mapped_column(nullable=False)
    queue: Mapped[str] = mapped_column(String(16), nullable=False)  # send_to_edit | backfill | dropped


class Tier2Score(ArtifactEnvelopeMixin, Base):
    __tablename__ = "tier2_scores"

    id: Mapped[uuid.UUID] = _uuid_pk()
    short_candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("short_candidates.id", ondelete="CASCADE"), nullable=False)
    final_rank_score: Mapped[float | None] = mapped_column(nullable=True)
    score_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    display_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)


class DisplaySelection(ArtifactEnvelopeMixin, Base):
    """v5.0 2.39.8: immutable per revision. A rerank creates a NEW row, never an update
    (impl plan §1.4 POST /v1/jobs/{job_id}/rerank / §3.6-style immutability posture)."""

    __tablename__ = "display_selections"

    id: Mapped[uuid.UUID] = _uuid_pk()
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    selected_candidate_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    __table_args__ = (UniqueConstraint("job_id", "revision", name="uq_display_selection_job_revision"),)


# --------------------------------------------------------------------------------------
# Review / outcomes / audit
# --------------------------------------------------------------------------------------

class ReviewAction(Base):
    """impl plan §1.4 accept/reject/edit/reframe actions -- preference data, distinct from
    platform performance data (v5.0 2.19/2.26)."""

    __tablename__ = "review_actions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    short_candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("short_candidates.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)  # accept | reject | edit | reframe
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)  # impl plan §1.4: "review metadata only, never a model/ranking feature"
    request_body: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Outcome(Base):
    """v5.0 2.18 outcome/label logging -- Phase 14, columns kept minimal until that phase."""

    __tablename__ = "outcomes"

    id: Mapped[uuid.UUID] = _uuid_pk()
    short_candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("short_candidates.id", ondelete="CASCADE"), nullable=False)
    whether_shown: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    whether_selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    whether_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    publication_platform: Mapped[str | None] = mapped_column(String(32), nullable=True)
    published_video_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    performance_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditEvent(Base):
    """impl plan §3.2/§18.1: generic audit trail (auth events, admin actions, security-relevant state changes)."""

    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TransportObject(Base):
    """Registry of internal transport-envelope objects (owner 2026-10-04 #6/#7). NOT an artifact:
    never listed to users, never part of lineage or reproducibility references. It exists only so a
    maintenance sweep can delete the object safely and audit the cleanup. Canonical artifacts and
    their hashes are never touched by the sweep."""

    __tablename__ = "transport_objects"

    id: Mapped[uuid.UUID] = _uuid_pk()
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    source_video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("source_videos.id", ondelete="CASCADE"), nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_location: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    retain_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retention_policy: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # effective values + basis
    cleanup_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_cleanup_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cleanup_result: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    cleanup_failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
