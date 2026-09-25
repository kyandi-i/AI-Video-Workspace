"""Immutable prompt generation facts; no versioning or provider credentials."""

import sqlalchemy as sa
from alembic import op

revision = "0007_prompt_generation"
down_revision = "0006_prompt_templates"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prompt_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("shot_id", sa.Uuid(), nullable=False),
        sa.Column("template_id", sa.Uuid(), nullable=False),
        sa.Column("template_name", sa.String(255), nullable=False),
        sa.Column("template_content", sa.Text(), nullable=False),
        sa.Column("prompt_type", sa.String(40), nullable=False),
        sa.Column("context_json", sa.JSON(), nullable=False),
        sa.Column("rendered_input", sa.Text(), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("generated_content", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(["shot_id"], ["shots.id"]),
        sa.ForeignKeyConstraint(["template_id"], ["prompt_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_prompt_records_shot_id", "prompt_records", ["shot_id"])
    op.create_index("ix_prompt_records_template_id", "prompt_records", ["template_id"])


def downgrade():
    op.drop_table("prompt_records")
