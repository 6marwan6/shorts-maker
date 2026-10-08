"""artifact raw_source ownership (nullable job_id + source_video_id)

Revision ID: 74099a393025
Revises: 75434a093ae7
Create Date: 2026-09-29

Owner decision (this session, Phase 2 blocking question): a `raw_source` Artifact must be
committed at upload-complete time, before any ProcessingJob exists (impl plan §3.2's
input_artifact_ids contract applied to the very first pipeline stage, NORMALIZING). That
requires `artifacts.job_id` to become nullable, plus a new nullable `source_video_id` FK.

Ownership convention (strict, no convenience population -- confirmed): artifact_type ==
"raw_source" rows have source_video_id set and job_id NULL; every other artifact_type keeps
job_id set and source_video_id NULL.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "74099a393025"
down_revision: str | None = "75434a093ae7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("artifacts", "job_id", existing_type=sa.UUID(), nullable=True)
    op.add_column("artifacts", sa.Column("source_video_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_artifacts_source_video_id", "artifacts", "source_videos",
        ["source_video_id"], ["id"], ondelete="CASCADE",
    )
    op.create_index("ix_artifacts_source_video_id", "artifacts", ["source_video_id"])
    op.create_check_constraint(
        "ck_artifacts_exactly_one_owner",
        "artifacts",
        "(job_id IS NOT NULL AND source_video_id IS NULL) "
        "OR (job_id IS NULL AND source_video_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_artifacts_exactly_one_owner", "artifacts", type_="check")
    op.drop_index("ix_artifacts_source_video_id", table_name="artifacts")
    op.drop_constraint("fk_artifacts_source_video_id", "artifacts", type_="foreignkey")
    op.drop_column("artifacts", "source_video_id")
    op.alter_column("artifacts", "job_id", existing_type=sa.UUID(), nullable=False)
