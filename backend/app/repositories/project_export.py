from sqlalchemy import select, text

from app.core.exceptions import AppError
from app.models import (
    Asset,
    AssetTag,
    Character,
    CharacterAssetLink,
    CharacterState,
    CharacterStateAssetLink,
    Project,
    ProjectAssetLink,
    PromptRecord,
    PromptTemplate,
    Scene,
    Script,
    ScriptNode,
    Shot,
    ShotAssetLink,
    ShotCharacterStateLink,
    Storyboard,
    Tag,
    VideoResult,
)


class ProjectExportRepository:
    """Read a project graph in the caller's single SQLite snapshot."""

    def __init__(self, session):
        self.session = session

    def active(self, model, *conditions):
        return list(
            self.session.scalars(
                select(model).where(model.deleted_at.is_(None), *conditions).order_by(model.id)
            )
        )

    def graph(self, project_id):
        project = self.session.get(Project, project_id)
        if project is None or project.deleted_at is not None:
            raise AppError("PROJECT_NOT_FOUND", "项目不存在或已删除。", 404)
        graph = {"projects": [project]}

        def add(model, *conditions):
            rows = self.active(model, *conditions)
            graph[model.__tablename__] = rows
            return {row.id for row in rows}

        scripts = add(Script, Script.project_id == project_id)
        add(ScriptNode, ScriptNode.script_id.in_(scripts))
        # A node beneath a deleted ancestor is not an active project subtree.
        nodes = graph["script_nodes"]
        reachable = set()
        while True:
            expanded = reachable | {
                n.id for n in nodes if n.parent_id is None or n.parent_id in reachable
            }
            if expanded == reachable:
                break
            reachable = expanded
        graph["script_nodes"] = [n for n in nodes if n.id in reachable]
        scenes = add(Scene, Scene.project_id == project_id, Scene.script_node_id.in_(reachable))
        shots = add(Shot, Shot.project_id == project_id, Shot.scene_id.in_(scenes))
        characters = add(Character, Character.project_id == project_id)
        states = add(CharacterState, CharacterState.character_id.in_(characters))
        add(
            PromptTemplate,
            PromptTemplate.project_id == project_id,
            PromptTemplate.scope == "PROJECT",
        )
        add(PromptRecord, PromptRecord.shot_id.in_(shots))
        add(Storyboard, Storyboard.shot_id.in_(shots))
        add(VideoResult, VideoResult.shot_id.in_(shots))
        add(ProjectAssetLink, ProjectAssetLink.project_id == project_id)
        add(ShotAssetLink, ShotAssetLink.shot_id.in_(shots))
        add(CharacterAssetLink, CharacterAssetLink.character_id.in_(characters))
        add(CharacterStateAssetLink, CharacterStateAssetLink.character_state_id.in_(states))
        add(
            ShotCharacterStateLink,
            ShotCharacterStateLink.shot_id.in_(shots),
            ShotCharacterStateLink.character_state_id.in_(states),
            ShotCharacterStateLink.character_id.in_(characters),
        )
        media_tables = (
            "project_asset_links",
            "shot_asset_links",
            "character_asset_links",
            "character_state_asset_links",
            "storyboards",
            "video_results",
        )
        asset_ids = {r.asset_id for table in media_tables for r in graph[table]}
        present = set(self.session.scalars(select(Asset.id).where(Asset.id.in_(asset_ids))))
        if present != asset_ids:
            raise AppError("EXPORT_BROKEN_REFERENCE", "导出资产记录缺失。", 409)
        assets = add(Asset, Asset.id.in_(asset_ids))
        for table in media_tables:
            graph[table] = [r for r in graph[table] if r.asset_id in assets]
        add(AssetTag, AssetTag.asset_id.in_(assets))
        tags = add(Tag, Tag.id.in_({r.tag_id for r in graph["asset_tags"]}))
        graph["asset_tags"] = [r for r in graph["asset_tags"] if r.tag_id in tags]
        revision = self.session.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
        return graph, revision

    def source(self, model, identifier):
        return self.session.get(model, identifier)
