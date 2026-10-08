"""stage_runs.execution_metadata + phase3_dispatch_intents

Revision ID: c3d41f7a9b20
Revises: 74099a393025
Create Date: 2026-10-02

Owner decisions 2026-10-02: #6/#8 (transport-envelope descriptors and effective polling/timeout
recorded in stage-run execution metadata, no new artifact lineage type) and #9 (durable
Phase-3 dispatch intent, written atomically with normalization).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c3d41f7a9b20"
down_revision: str | None = "74099a393025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("stage_runs", sa.Column("execution_metadata", postgresql.JSONB(), nullable=False,
                                          server_default=sa.text("'{}'::jsonb")))
    op.create_table(
        "phase3_dispatch_intents",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("job_id", sa.UUID(), sa.ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("source_video_id", sa.UUID(), sa.ForeignKey("source_videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("state", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("task_id", sa.String(64), nullable=False),
        sa.Column("dispatch_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_phase3_dispatch_intents_state", "phase3_dispatch_intents", ["state"])


def downgrade() -> None:
    op.drop_index("ix_phase3_dispatch_intents_state", table_name="phase3_dispatch_intents")
    op.drop_table("phase3_dispatch_intents")
    op.drop_column("stage_runs", "execution_metadata")
