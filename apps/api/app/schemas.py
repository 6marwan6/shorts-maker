"""Pydantic v2 request/response schemas (impl plan §1.4 exact endpoint list, §1.4 candidate
mutation request bodies verbatim, §6 API contract summary).

These are API wire schemas, not artifact schemas -- artifact content schemas live in
packages/schemas/json (impl plan §4.3). Do not duplicate artifact fields here beyond what an
endpoint actually accepts/returns.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

# --------------------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    created_at: datetime


# --------------------------------------------------------------------------------------
# Uploads (impl plan §1.6: presigned URLs only, API never proxies the body)
# --------------------------------------------------------------------------------------

class CreateUploadRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=512)
    content_type: str = Field(min_length=1, max_length=255)
    declared_size_bytes: int | None = Field(default=None, ge=0)


class CreateUploadResponse(BaseModel):
    upload_id: uuid.UUID
    upload_url: str
    upload_method: Literal["PUT", "POST"]
    storage_key: str


class CompleteUploadRequest(BaseModel):
    checksum_sha256: str | None = Field(default=None, min_length=64, max_length=64)


class CompleteUploadResponse(BaseModel):
    source_video_id: uuid.UUID


# --------------------------------------------------------------------------------------
# Jobs
# --------------------------------------------------------------------------------------

class CreateJobRequest(BaseModel):
    source_video_id: uuid.UUID
    export_profile_id: str = Field(min_length=1, max_length=64)


class JobResponse(BaseModel):
    job_id: uuid.UUID
    state: str


class JobStatusResponse(BaseModel):
    job_id: uuid.UUID
    state: str
    progress: float | None = None
    current_stage: str | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------------------
# Candidate mutation request bodies (impl plan §1.4, verbatim shape)
# --------------------------------------------------------------------------------------

class TrimStartOp(BaseModel):
    type: Literal["trim_start"]
    requested_source_ms: int = Field(ge=0)


class TrimEndOp(BaseModel):
    type: Literal["trim_end"]
    requested_source_ms: int = Field(ge=0)


class RemoveRetainedIntervalOp(BaseModel):
    type: Literal["remove_retained_interval"]
    output_segment_id: uuid.UUID


CandidateEditOperation = TrimStartOp | TrimEndOp | RemoveRetainedIntervalOp


class CandidateEditRequest(BaseModel):
    """impl plan §1.4: 'At least one operation is required. Operations are applied in array
    order against a working copy of the parent's verified timeline.'"""

    operations: list[CandidateEditOperation] = Field(min_length=1)


class CandidateReframeRequest(BaseModel):
    strategy: Literal["auto", "fixed_center", "face_aware", "multi_speaker", "blurred_background"] = "auto"


class CandidateReviewActionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)


class CandidateResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    state: str
    comparability_class: Literal["A", "B"]
    eligible: bool
    exclusion_reason: str | None
    score_rank: int | None = None
    display_rank: int | None = None


# --------------------------------------------------------------------------------------
# Error envelope (used by every router)
# --------------------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    detail: str
