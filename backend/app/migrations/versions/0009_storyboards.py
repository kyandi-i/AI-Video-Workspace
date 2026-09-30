"""Shot storyboard versions referencing managed assets and prompt facts."""

import sqlalchemy as sa
from alembic import op

revision = "0009_storyboards"
down_revision = "0008_prompt_versioning"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "storyboards",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("shot_id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("source_prompt_record_id", sa.Uuid(), nullable=True),
        sa.Column("storyboard_type", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_selected", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["shot_id"], ["shots.id"]),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["source_prompt_record_id"], ["prompt_records.id"]),
        sa.UniqueConstraint("shot_id", "version", name="uq_storyboard_version"),
        sa.CheckConstraint("version > 0", name="storyboard_version_positive"),
        sa.CheckConstraint("storyboard_type = 'GRID_6'", name="storyboard_type_grid6"),
    )
    for field in ("shot_id", "asset_id", "source_prompt_record_id"):
        op.create_index(f"ix_storyboards_{field}", "storyboards", [field])
    op.create_index(
        "uq_storyboard_selected",
        "storyboards",
        ["shot_id"],
        unique=True,
        sqlite_where=sa.text("is_selected = 1 AND deleted_at IS NULL"),
        postgresql_where=sa.text("is_selected = true AND deleted_at IS NULL"),
    )


def downgrade():
    op.drop_table("storyboards")
