"""Project script scene shot workflow

Revision ID: 0002_core_workflow
Revises: 0001_app_settings
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_core_workflow"
down_revision = "0001_app_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "ACTIVE",
                "PAUSED",
                "COMPLETED",
                "ARCHIVED",
                name="projectstatus",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("length(trim(name)) > 0", name=op.f("ck_projects_name_required")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_projects")),
    )
    op.create_table(
        "scripts",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name=op.f("fk_scripts_project_id_projects")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scripts")),
    )
    with op.batch_alter_table("scripts", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_scripts_project_id"), ["project_id"], unique=False)

    op.create_table(
        "script_nodes",
        sa.Column("script_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column(
            "node_type",
            sa.Enum(
                "CHAPTER",
                "SEQUENCE",
                "SCENE",
                "OTHER",
                name="nodetype",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("order_index >= 0", name=op.f("ck_script_nodes_order_nonnegative")),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["script_nodes.id"], name=op.f("fk_script_nodes_parent_id_script_nodes")
        ),
        sa.ForeignKeyConstraint(
            ["script_id"], ["scripts.id"], name=op.f("fk_script_nodes_script_id_scripts")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_script_nodes")),
    )
    with op.batch_alter_table("script_nodes", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_script_nodes_script_id"), ["script_id"], unique=False)

    op.create_table(
        "scenes",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("script_node_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("fixed_constraints", sa.Text(), nullable=False),
        sa.Column("negative_constraints", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name=op.f("fk_scenes_project_id_projects")
        ),
        sa.ForeignKeyConstraint(
            ["script_node_id"],
            ["script_nodes.id"],
            name=op.f("fk_scenes_script_node_id_script_nodes"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scenes")),
        sa.UniqueConstraint("script_node_id", name=op.f("uq_scenes_script_node_id")),
    )
    with op.batch_alter_table("scenes", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_scenes_project_id"), ["project_id"], unique=False)

    op.create_table(
        "shots",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("scene_id", sa.Uuid(), nullable=False),
        sa.Column("shot_code", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "ASSET_PREPARING",
                "STORYBOARD_PROMPT_READY",
                "STORYBOARD_READY",
                "VIDEO_PROMPT_READY",
                "VIDEO_GENERATING",
                "REVIEW",
                "DONE",
                name="shotstatus",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("creative_requirement", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("duration_seconds >= 0", name=op.f("ck_shots_duration_nonnegative")),
        sa.CheckConstraint("length(trim(shot_code)) > 0", name=op.f("ck_shots_code_required")),
        sa.CheckConstraint("length(trim(title)) > 0", name=op.f("ck_shots_title_required")),
        sa.CheckConstraint("order_index >= 0", name=op.f("ck_shots_order_nonnegative")),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name=op.f("fk_shots_project_id_projects")
        ),
        sa.ForeignKeyConstraint(["scene_id"], ["scenes.id"], name=op.f("fk_shots_scene_id_scenes")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shots")),
        sa.UniqueConstraint("project_id", "shot_code", name=op.f("uq_shots_project_id")),
    )
    with op.batch_alter_table("shots", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_shots_project_id"), ["project_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_shots_scene_id"), ["scene_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("shots", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_shots_scene_id"))
        batch_op.drop_index(batch_op.f("ix_shots_project_id"))

    op.drop_table("shots")
    with op.batch_alter_table("scenes", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_scenes_project_id"))

    op.drop_table("scenes")
    with op.batch_alter_table("script_nodes", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_script_nodes_script_id"))

    op.drop_table("script_nodes")
    with op.batch_alter_table("scripts", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_scripts_project_id"))

    op.drop_table("scripts")
    op.drop_table("projects")
