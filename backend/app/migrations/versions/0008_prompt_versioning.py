"""Linear prompt history; preserve every original generation fact."""

import sqlalchemy as sa
from alembic import op

revision = "0008_prompt_versioning"
down_revision = "0007_prompt_generation"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("prompt_records", sa.Column("version", sa.Integer(), nullable=True))
    op.add_column("prompt_records", sa.Column("edited_content", sa.Text(), nullable=True))
    op.add_column("prompt_records", sa.Column("is_selected", sa.Boolean(), nullable=True))
    connection = op.get_bind()
    rows = (
        connection.execute(
            sa.text(
                "SELECT id, shot_id, prompt_type, deleted_at FROM prompt_records "
                "ORDER BY shot_id, prompt_type, created_at, id"
            )
        )
        .mappings()
        .all()
    )
    versions, selected = {}, {}
    for row in rows:
        group = (row["shot_id"], row["prompt_type"])
        versions[group] = versions.get(group, 0) + 1
        connection.execute(
            sa.text("UPDATE prompt_records SET version=:version, is_selected=0 WHERE id=:id"),
            {"version": versions[group], "id": row["id"]},
        )
        if row["deleted_at"] is None:
            selected[group] = row["id"]
    for identifier in selected.values():
        connection.execute(
            sa.text("UPDATE prompt_records SET is_selected=1 WHERE id=:id"), {"id": identifier}
        )
    with op.batch_alter_table("prompt_records") as batch:
        batch.alter_column("version", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("is_selected", existing_type=sa.Boolean(), nullable=False)
        batch.create_unique_constraint("uq_prompt_version", ["shot_id", "prompt_type", "version"])
        batch.create_check_constraint("prompt_version_positive", "version > 0")
    op.create_index(
        "uq_prompt_selected",
        "prompt_records",
        ["shot_id", "prompt_type"],
        unique=True,
        sqlite_where=sa.text("is_selected = 1 AND deleted_at IS NULL"),
        postgresql_where=sa.text("is_selected = true AND deleted_at IS NULL"),
    )


def downgrade():
    op.drop_index("uq_prompt_selected", table_name="prompt_records")
    with op.batch_alter_table("prompt_records") as batch:
        batch.drop_constraint("uq_prompt_version", type_="unique")
        batch.drop_constraint("prompt_version_positive", type_="check")
        batch.drop_column("is_selected")
        batch.drop_column("edited_content")
        batch.drop_column("version")
