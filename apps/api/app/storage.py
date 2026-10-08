"""Storage adapter (impl plan §1.6): browser uploads and artifact/render reads go through
presigned URLs; the API never proxies the full upload body. D0 uses a local filesystem
adapter for unit/pipeline tests; D1/D2/P0 use real Cloudflare R2 (S3-compatible). The
filesystem adapter is NEVER the production storage implementation (impl plan §1.6).
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import boto3
from botocore.client import Config as BotoConfig

from .config import Settings


@dataclass(frozen=True)
class PresignedUpload:
    url: str
    method: str
    fields: dict[str, str] | None  # POST-form fields (R2/S3 presigned POST); None for PUT-style URLs
    storage_key: str


@dataclass(frozen=True)
class PresignedDownload:
    url: str
    storage_key: str


class StorageAdapter(Protocol):
    """impl plan §1.6.1: api owns signed-URL issuance; workers read/write objects directly."""

    def presign_upload(self, *, storage_key: str, content_type: str, expires_in_s: int = 900) -> PresignedUpload: ...
    def presign_download(self, *, storage_key: str, expires_in_s: int = 900) -> PresignedDownload: ...
    def object_exists(self, storage_key: str) -> bool: ...
    def object_size(self, storage_key: str) -> int | None: ...
    def delete_object(self, storage_key: str) -> None: ...
    def read_bytes(self, storage_key: str) -> bytes: ...
    def write_bytes(self, storage_key: str, data: bytes) -> None:
        """The direct server-side write path workers use (impl plan §1.6.1: "workers read/write
        objects directly"; §1.6: "Python services access R2 through boto3"). NOT a browser
        upload path -- browsers only ever get a presigned PUT URL from presign_upload."""
        ...


class UnconfiguredStorageBackend(RuntimeError):
    """Raised rather than silently degrading to a different backend (impl plan §1.13:
    'do not introduce an additional cloud platform' / never a silent substitution, §0)."""


class LocalFilesystemStorage:
    """D0 test/dev adapter (impl plan §1.6.2). 'Presigning' is simulated: the returned URL is
    a local file:// path the test harness writes to directly. Never used in D1/D2/P0."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, storage_key: str) -> Path:
        # storage_key is always forward-slash object-store style; normalize defensively so a
        # malicious/odd key can never escape self.root via ".." traversal.
        parts = [p for p in storage_key.split("/") if p not in ("", ".", "..")]
        return self.root.joinpath(*parts)

    def presign_upload(self, *, storage_key: str, content_type: str, expires_in_s: int = 900) -> PresignedUpload:
        path = self._path(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        return PresignedUpload(url=f"file://{path}", method="PUT", fields=None, storage_key=storage_key)

    def presign_download(self, *, storage_key: str, expires_in_s: int = 900) -> PresignedDownload:
        return PresignedDownload(url=f"file://{self._path(storage_key)}", storage_key=storage_key)

    def object_exists(self, storage_key: str) -> bool:
        return self._path(storage_key).is_file()

    def object_size(self, storage_key: str) -> int | None:
        path = self._path(storage_key)
        return path.stat().st_size if path.is_file() else None

    def delete_object(self, storage_key: str) -> None:
        path = self._path(storage_key)
        if path.is_file():
            path.unlink()

    def write_bytes(self, storage_key: str, data: bytes) -> None:
        """Worker artifact-persistence path (Phase 2+): normalization and every later CPU/GPU/
        render stage write their output bytes here directly, via boto3 -- not a presigned URL
        (those are for the browser only). Also usable by tests to seed an object without going
        through a real HTTP PUT."""
        path = self._path(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def read_bytes(self, storage_key: str) -> bytes:
        """D0-only: used to compute a real server-side checksum for the raw_source artifact
        (impl plan §3.1 content-addressing) instead of trusting the client-supplied
        `checksum_sha256` on CompleteUploadRequest, which is optional and unverified."""
        return self._path(storage_key).read_bytes()

    def reset(self) -> None:
        """Test-only: wipe and recreate the storage root between test cases."""
        shutil.rmtree(self.root, ignore_errors=True)
        self.root.mkdir(parents=True, exist_ok=True)


class R2Storage:
    """D1/D2/P0 (impl plan §1.6/§1.16): boto3 against R2's S3-compatible endpoint, region=auto
    (impl plan §1.6). Presigned URL generation is a local signing computation -- it does not
    itself require reaching R2, only *using* the returned URL does."""

    def __init__(self, *, endpoint_url: str, access_key_id: str, secret_access_key: str, bucket: str):
        self.bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
            config=BotoConfig(signature_version="s3v4"),
        )

    def presign_upload(self, *, storage_key: str, content_type: str, expires_in_s: int = 900) -> PresignedUpload:
        url = self._client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket, "Key": storage_key, "ContentType": content_type},
            ExpiresIn=expires_in_s,
        )
        return PresignedUpload(url=url, method="PUT", fields=None, storage_key=storage_key)

    def presign_download(self, *, storage_key: str, expires_in_s: int = 900) -> PresignedDownload:
        url = self._client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": storage_key}, ExpiresIn=expires_in_s,
        )
        return PresignedDownload(url=url, storage_key=storage_key)

    def object_exists(self, storage_key: str) -> bool:
        from botocore.exceptions import ClientError
        try:
            self._client.head_object(Bucket=self.bucket, Key=storage_key)
            return True
        except ClientError:
            return False

    def object_size(self, storage_key: str) -> int | None:
        from botocore.exceptions import ClientError
        try:
            resp = self._client.head_object(Bucket=self.bucket, Key=storage_key)
            return resp["ContentLength"]
        except ClientError:
            return None

    def delete_object(self, storage_key: str) -> None:
        self._client.delete_object(Bucket=self.bucket, Key=storage_key)

    def write_bytes(self, storage_key: str, data: bytes) -> None:
        """Worker artifact-persistence path (§1.6.1): a direct boto3 put_object, never a
        presigned URL (those are for the browser upload path only, via presign_upload)."""
        self._client.put_object(Bucket=self.bucket, Key=storage_key, Body=data)

    def read_bytes(self, storage_key: str) -> bytes:
        return self._client.get_object(Bucket=self.bucket, Key=storage_key)["Body"].read()


def build_storage_adapter(settings: Settings, *, bucket_kind: str = "source") -> StorageAdapter:
    """bucket_kind in {"source","artifacts","renders"} (impl plan §1.6 required buckets)."""
    if settings.storage_backend == "local":
        return LocalFilesystemStorage(Path(settings.local_storage_root) / bucket_kind)
    if settings.storage_backend == "r2":
        bucket = {
            "source": settings.r2_bucket_source,
            "artifacts": settings.r2_bucket_artifacts,
            "renders": settings.r2_bucket_renders,
        }[bucket_kind]
        if not (settings.r2_endpoint_url and settings.r2_access_key_id and settings.r2_secret_access_key and bucket):
            raise UnconfiguredStorageBackend(
                f"storage_backend='r2' but R2 credentials/bucket are not fully configured for '{bucket_kind}'"
            )
        return R2Storage(
            endpoint_url=settings.r2_endpoint_url, access_key_id=settings.r2_access_key_id,
            secret_access_key=settings.r2_secret_access_key, bucket=bucket,
        )
    raise UnconfiguredStorageBackend(f"unknown storage_backend: {settings.storage_backend!r}")
