"""Create the ordinary workspace settings infrastructure table.

Revision ID: 0001_app_settings
Revises: None
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_app_settings"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_app_settings")),
        sa.UniqueConstraint("key", name=op.f("uq_app_settings_key")),
    )


def downgrade() -> None:
    op.drop_table("app_settings")
