"""Structured shot requirements; preserve legacy creative_requirement."""

import sqlalchemy as sa
from alembic import op

revision = "0005_shot_workspace"
down_revision = "0004_characters"
branch_labels = None
depends_on = None


def upgrade():
    for name in ("main_action", "key_constraints", "negative_constraints", "free_notes"):
        op.add_column("shots", sa.Column(name, sa.Text(), nullable=True))


def downgrade():
    for name in ("free_notes", "negative_constraints", "key_constraints", "main_action"):
        op.drop_column("shots", name)
