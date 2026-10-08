from __future__ import annotations

import hashlib
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from shorts_config import load_config
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings, get_settings
from ..db import get_session
from ..models import Artifact, SourceVideo, UploadSession, User
from ..schemas import (
    CompleteUploadRequest,
    CompleteUploadResponse,
    CreateUploadRequest,
    CreateUploadResponse,
)
from ..storage import build_storage_adapter
from .auth import get_current_user

router = APIRouter(prefix="/v1/uploads", tags=["uploads"])


@router.post("", response_model=CreateUploadResponse, status_code=status.HTTP_201_CREATED)
async def create_upload(
    body: CreateUploadRequest, user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings), session: AsyncSession = Depends(get_session),
):
    upload_id = uuid.uuid4()
    storage_key = f"raw/{user.id}/{upload_id}/{body.filename}"
    storage = build_storage_adapter(settings, bucket_kind="source")
    presigned = storage.presign_upload(storage_key=storage_key, content_type=body.content_type)

    session.add(UploadSession(id=upload_id, user_id=user.id, storage_key=storage_key,
                               original_filename=body.filename, declared_content_type=body.content_type))
    await session.commit()
    return CreateUploadResponse(upload_id=upload_id, upload_url=presigned.url,
                                 upload_method=presigned.method, storage_key=storage_key)


@router.post("/{upload_id}/complete", response_model=CompleteUploadResponse)
async def complete_upload(
    upload_id: uuid.UUID, body: CompleteUploadRequest, user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings), session: AsyncSession = Depends(get_session),
):
    upload = await session.get(UploadSession, upload_id)
    if upload is None or upload.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "upload session not found")
    if upload.status == "COMPLETED":
        raise HTTPException(status.HTTP_409_CONFLICT, "upload already completed")

    storage = build_storage_adapter(settings, bucket_kind="source")
    if not storage.object_exists(upload.storage_key):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "object not found in storage -- upload did not complete")

    size = storage.object_size(upload.storage_key)
    # impl plan §2.2/Phase 2: hard duration/size limits are enforced during normalization
    # (needs ffprobe on the actual bytes); here we only enforce the coarse, cheap size cap so
    # an obviously-oversized file is rejected before a worker ever picks it up.
    max_bytes = load_config()["MAX_SOURCE_SIZE_BYTES"]
    if size is not None and size > max_bytes:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE,
                             f"object size {size} exceeds MAX_SOURCE_SIZE_BYTES ({max_bytes})")

    source_video = SourceVideo(user_id=user.id, raw_storage_key=upload.storage_key,
                                original_filename=upload.original_filename, file_size_bytes=size,
                                checksum_sha256=body.checksum_sha256)
    session.add(source_video)
    await session.flush()

    # raw_source Artifact: server-computed checksum (never trust the client-supplied, optional
    # CompleteUploadRequest.checksum_sha256 for content addressing). D0-only read; D1 (R2) needs
    # its own whole-object hashing path -- see StorageAdapter.read_bytes.
    raw_bytes = storage.read_bytes(upload.storage_key)
    raw_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    cfg = load_config()  # real active snapshot identity, never a fabricated sentinel -- this
    # artifact isn't "behavior-produced" by config, but the NOT NULL fields must hold config
    # identity that actually resolves to a real snapshot, not an invented placeholder hash.
    session.add(Artifact(
        job_id=None, source_video_id=source_video.id, artifact_type="raw_source",
        stage="UPLOADED", stage_version="raw_source@1", schema_version=1,
        config_version=cfg.config_version, config_sha256=cfg.config_sha256,
        input_artifact_ids=[], checksum=raw_sha256, storage_location=upload.storage_key,
        model_versions={},
    ))

    upload.status = "COMPLETED"
    upload.source_video_id = source_video.id
    upload.completed_at = func.now()
    await session.commit()
    return CompleteUploadResponse(source_video_id=source_video.id)
