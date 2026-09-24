"""Provider-neutral prompt templates; no seeded content."""

import sqlalchemy as sa
from alembic import op

revision = "0006_prompt_templates"
down_revision = "0005_shot_workspace"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prompt_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column(
            "scope",
            sa.Enum(
                "GLOBAL", "PROJECT", native_enum=False, create_constraint=True, name="templatescope"
            ),
            nullable=False,
        ),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "category",
            sa.Enum(
                "STORYBOARD_6GRID",
                "VIDEO_GENERATION",
                "CHARACTER_IMAGE",
                "SCENE_IMAGE",
                "IMAGE_REFERENCE",
                "START_END_FRAME",
                "OTHER",
                native_enum=False,
                create_constraint=True,
                name="templatecategory",
            ),
            nullable=False,
        ),
        sa.Column("template_content", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "(scope = 'GLOBAL' AND project_id IS NULL) OR "
            "(scope = 'PROJECT' AND project_id IS NOT NULL)",
            name="scope_project",
        ),
        sa.CheckConstraint("length(trim(name)) BETWEEN 1 AND 255", name="name_required"),
        sa.CheckConstraint(
            "length(trim(template_content)) > 0 AND length(template_content) <= 100000",
            name="content_required",
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for field in ("scope", "project_id", "category"):
        op.create_index(f"ix_prompt_templates_{field}", "prompt_templates", [field])
    op.create_index(
        "uq_template_global_name",
        "prompt_templates",
        ["name"],
        unique=True,
        sqlite_where=sa.text("scope = 'GLOBAL'"),
        postgresql_where=sa.text("scope = 'GLOBAL'"),
    )
    op.create_index(
        "uq_template_project_name", "prompt_templates", ["project_id", "name"], unique=True
    )


def downgrade():
    op.drop_table("prompt_templates")
