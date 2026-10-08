"""Phase 1 unit tests: app.storage. LocalFilesystemStorage is fully exercised (D0, no network).
R2Storage's presign_* methods are pure local signing computations (boto3 SigV4) and are
exercised with dummy credentials against a fake endpoint -- generating a presigned URL never
itself contacts R2, only *using* the returned URL would (impl plan §1.6)."""
import pytest
from app.storage import (
    LocalFilesystemStorage,
    R2Storage,
    Settings,
    UnconfiguredStorageBackend,
    build_storage_adapter,
)


def test_local_storage_presign_upload_and_write_roundtrip(tmp_path):
    storage = LocalFilesystemStorage(tmp_path)
    presigned = storage.presign_upload(storage_key="raw/u1/video.mp4", content_type="video/mp4")
    assert presigned.method == "PUT"
    assert not storage.object_exists("raw/u1/video.mp4")

    storage.write_bytes("raw/u1/video.mp4", b"hello world")
    assert storage.object_exists("raw/u1/video.mp4")
    assert storage.object_size("raw/u1/video.mp4") == len(b"hello world")


def test_local_storage_delete_object(tmp_path):
    storage = LocalFilesystemStorage(tmp_path)
    storage.write_bytes("a/b.txt", b"x")
    assert storage.object_exists("a/b.txt")
    storage.delete_object("a/b.txt")
    assert not storage.object_exists("a/b.txt")


def test_local_storage_missing_object_size_is_none(tmp_path):
    storage = LocalFilesystemStorage(tmp_path)
    assert storage.object_size("does/not/exist.mp4") is None


def test_local_storage_rejects_path_traversal(tmp_path):
    storage = LocalFilesystemStorage(tmp_path)
    storage.write_bytes("../escaped.txt", b"should not escape root")
    escaped = (tmp_path.parent / "escaped.txt")
    assert not escaped.exists()
    assert (tmp_path / "escaped.txt").exists()


def test_local_storage_reset_clears_root(tmp_path):
    storage = LocalFilesystemStorage(tmp_path)
    storage.write_bytes("a.txt", b"x")
    storage.reset()
    assert not storage.object_exists("a.txt")
    assert tmp_path.is_dir()


def test_local_storage_presigned_download_url_shape(tmp_path):
    storage = LocalFilesystemStorage(tmp_path)
    presigned = storage.presign_download(storage_key="clips/out.mp4")
    assert presigned.url.startswith("file://")
    assert presigned.storage_key == "clips/out.mp4"


def _dummy_r2_settings(**overrides) -> Settings:
    defaults = {
        "storage_backend": "r2",
        "r2_endpoint_url": "https://dummy-account.r2.cloudflarestorage.com",
        "r2_access_key_id": "AKIA_TEST",
        "r2_secret_access_key": "test-secret",
        "r2_bucket_source": "shorts-source-staging",
    }
    defaults.update(overrides)
    return Settings(**defaults)


def test_r2_presign_upload_is_offline_signing_only():
    storage = R2Storage(
        endpoint_url="https://dummy-account.r2.cloudflarestorage.com",
        access_key_id="AKIA_TEST", secret_access_key="test-secret", bucket="shorts-source-staging",
    )
    presigned = storage.presign_upload(storage_key="raw/u1/video.mp4", content_type="video/mp4")
    assert presigned.url.startswith("https://dummy-account.r2.cloudflarestorage.com/")
    assert "X-Amz-Signature" in presigned.url
    assert presigned.method == "PUT"


def test_r2_presign_download_is_offline_signing_only():
    storage = R2Storage(
        endpoint_url="https://dummy-account.r2.cloudflarestorage.com",
        access_key_id="AKIA_TEST", secret_access_key="test-secret", bucket="shorts-source-staging",
    )
    presigned = storage.presign_download(storage_key="renders/out.mp4")
    assert "X-Amz-Signature" in presigned.url


def test_build_storage_adapter_local():
    settings = Settings(storage_backend="local", local_storage_root="./.local-storage-test")
    adapter = build_storage_adapter(settings, bucket_kind="source")
    assert isinstance(adapter, LocalFilesystemStorage)


def test_build_storage_adapter_r2_requires_full_credentials():
    settings = Settings(storage_backend="r2")  # no endpoint/keys/bucket configured
    with pytest.raises(UnconfiguredStorageBackend):
        build_storage_adapter(settings, bucket_kind="source")


def test_build_storage_adapter_r2_with_credentials_succeeds():
    settings = _dummy_r2_settings()
    adapter = build_storage_adapter(settings, bucket_kind="source")
    assert isinstance(adapter, R2Storage)
