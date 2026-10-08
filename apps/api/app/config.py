"""Environment-driven settings (impl plan §1.3, §1.16 deployment modes D0/D1/D2/P0).

Nothing behavior-producing lives here -- product constants (export profiles, compression
ratios, etc.) come from shorts_config.load_config(), never duplicated into env vars. This
module only holds infrastructure connection strings and secrets, which legitimately do vary
per deployment mode (impl plan §14 technology decision record).
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DeploymentMode = Literal["D0", "D1", "D2", "P0"]
StorageBackend = Literal["local", "r2"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SHORTS_MAKER_", env_file=".env", extra="ignore")

    deployment_mode: DeploymentMode = "D0"

    database_url: str = "postgresql+asyncpg://shorts_maker:shorts_maker_dev@127.0.0.1:5432/shorts_maker_dev"
    redis_url: str = "redis://127.0.0.1:6379/0"

    # impl plan §1.6: D0 filesystem adapter for unit tests; D1/D2/P0 real R2 (§1.16). Never a
    # silent fallback -- storage.py raises if "r2" is selected without credentials.
    storage_backend: StorageBackend = "local"
    local_storage_root: str = "./.local-storage"
    r2_endpoint_url: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_bucket_source: str | None = None
    r2_bucket_artifacts: str | None = None
    r2_bucket_renders: str | None = None

    # OPERATIONAL configuration (owner decisions 2026-10-02 #8/#9, 2026-10-04 #2/#7): NOT config@1,
    # never behavior-producing. Effective values are persisted with the rows they governed.
    dispatch_lease_s: int = 60
    reconcile_interval_s: int = 15
    transport_retention_success_h: int = 24     # after the canonical artifact is materialized
    transport_retention_failed_d: int = 7
    transport_retention_cancelled_d: int = 7
    transport_sweep_interval_s: int = 3600      # sweep cadence is unspecified by the owner: flagged

    # Local immutable model directory (owner 2026-10-06 G3 materialization): operational path, not config@1.
    models_root: str = ""  # empty -> <repo>/models

    # Auth (impl plan §1.3: Argon2id + rotating refresh tokens).
    auth_secret_key: str = Field(default="dev-only-insecure-secret-change-me")
    access_token_ttl_seconds: int = 15 * 60
    refresh_token_ttl_seconds: int = 30 * 24 * 60 * 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
