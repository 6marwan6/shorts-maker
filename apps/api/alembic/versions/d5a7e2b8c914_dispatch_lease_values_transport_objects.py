"""dispatch intent effective lease/reconcile values + transport_objects retention registry

Revision ID: d5a7e2b8c914
Revises: c3d41f7a9b20
Create Date: 2026-10-04

Owner decisions 2026-10-04 #2 (persist effective lease/reconcile values) and #7 (transport-object
retention with retention timestamp, cleanup attempts, result and failure reason).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d5a7e2b8c914"
down_revision: str | None = "c3d41f7a9b20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("phase3_dispatch_intents", sa.Column("lease_s", sa.Integer(), nullable=True))
    op.add_column("phase3_dispatch_intents", sa.Column("reconcile_interval_s", sa.Integer(), nullable=True))
    op.create_table(
        "transport_objects",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("job_id", sa.UUID(), sa.ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_video_id", sa.UUID(), sa.ForeignKey("source_videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage", sa.String(64), nullable=False),
        sa.Column("storage_location", sa.Text(), nullable=False, unique=True),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("retain_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retention_policy", postgresql.JSONB(), nullable=True),
        sa.Column("cleanup_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_cleanup_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cleanup_result", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("cleanup_failure_reason", sa.Text(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_transport_objects_job_id", "transport_objects", ["job_id"])
    op.create_index("ix_transport_objects_cleanup_result", "transport_objects", ["cleanup_result"])


def downgrade() -> None:
    op.drop_index("ix_transport_objects_cleanup_result", table_name="transport_objects")
    op.drop_index("ix_transport_objects_job_id", table_name="transport_objects")
    op.drop_table("transport_objects")
    op.drop_column("phase3_dispatch_intents", "reconcile_interval_s")
    op.drop_column("phase3_dispatch_intents", "lease_s")
