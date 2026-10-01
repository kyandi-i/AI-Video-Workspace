"""Video result versions with independent storyboard and prompt provenance."""

import sqlalchemy as sa
from alembic import op

revision = "0010_video_results"
down_revision = "0009_storyboards"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "video_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("shot_id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("source_storyboard_id", sa.Uuid(), nullable=True),
        sa.Column("source_prompt_record_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_selected", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["shot_id"], ["shots.id"]),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["source_storyboard_id"], ["storyboards.id"]),
        sa.ForeignKeyConstraint(["source_prompt_record_id"], ["prompt_records.id"]),
        sa.UniqueConstraint("shot_id", "version", name="uq_video_result_version"),
        sa.CheckConstraint("version > 0", name="video_result_version_positive"),
    )
    for field in ("shot_id", "asset_id", "source_storyboard_id", "source_prompt_record_id"):
        op.create_index(f"ix_video_results_{field}", "video_results", [field])
    op.create_index(
        "uq_video_result_selected",
        "video_results",
        ["shot_id"],
        unique=True,
        sqlite_where=sa.text("is_selected = 1 AND deleted_at IS NULL"),
        postgresql_where=sa.text("is_selected = true AND deleted_at IS NULL"),
    )


def downgrade():
    op.drop_table("video_results")
