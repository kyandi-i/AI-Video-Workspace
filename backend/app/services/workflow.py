from datetime import timedelta
from functools import wraps

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import AppError
from app.models.base import utc_now
from app.models.workflow import NodeType, Project, Scene, Script, ScriptNode, Shot
from app.repositories.workflow import (
    ProjectRepository,
    SceneRepository,
    ScriptNodeRepository,
    ScriptRepository,
    ShotRepository,
)
from app.schemas.workflow import SceneRead


def atomic(method):
    """Savepoint protects multi-entity writes even if a caller catches the error.

    WorkspaceService.session owns outer commit/rollback and the existing workspace
    lease serializes requests through commit in this single-process local app.
    """

    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self.session.begin_nested():
            return method(self, *args, **kwargs)

    return wrapped


class WorkflowService:
    def __init__(self, session):
        self.session = session
        self.projects = ProjectRepository(session)
        self.scripts = ScriptRepository(session)
        self.nodes = ScriptNodeRepository(session)
        self.scenes = SceneRepository(session)
        self.shots = ShotRepository(session)

    def deletion_timestamp(self):
        # The shared timestamp is also a cascade marker. Ensure distinct operations
        # cannot share it on coarse clocks or after a wall-clock adjustment.
        latest = self.projects.latest_deletion()
        now = utc_now()
        return max(now, latest + timedelta(microseconds=1)) if latest else now

    def required(self, repository, identifier, code, include_deleted=False):
        entity = repository.get(identifier, include_deleted=include_deleted)
        if entity is None:
            raise AppError(f"{code}_NOT_FOUND", f"{code.title()} 不存在或已删除。", 404)
        return entity

    def project(self, identifier, include_deleted=False):
        return self.required(self.projects, identifier, "PROJECT", include_deleted)

    def script(self, identifier, include_deleted=False):
        entity = self.required(self.scripts, identifier, "SCRIPT", include_deleted)
        self.project(entity.project_id, include_deleted)
        return entity

    def scene(self, identifier, include_deleted=False):
        entity = self.required(self.scenes, identifier, "SCENE", include_deleted)
        node = self.required(self.nodes, entity.script_node_id, "SCENE", include_deleted)
        script = self.script(node.script_id, include_deleted)
        self.relation(script.project_id == entity.project_id and node.node_type == NodeType.SCENE)
        return entity

    def shot(self, identifier, include_deleted=False):
        entity = self.required(self.shots, identifier, "SHOT", include_deleted)
        scene = self.scene(entity.scene_id, include_deleted)
        self.relation(scene.project_id == entity.project_id)
        return entity

    @staticmethod
    def relation(valid):
        if not valid:
            raise AppError("INVALID_PROJECT_RELATION", "所选剧本或场景不属于该项目。", 400)

    def normalize_nodes(self, script_id):
        for index, node in enumerate(self.nodes.matching(script_id=script_id, parent_id=None)):
            self.nodes.update(node, order_index=index)

    def normalize_shots(self, scene_id):
        for index, shot in enumerate(self.shots.matching(scene_id=scene_id)):
            self.shots.update(shot, order_index=index)

    def delete_scene_tree(self, scene, timestamp):
        for shot in self.shots.matching(scene_id=scene.id):
            self.shots.mark_deleted(shot, timestamp)
        node = self.nodes.get(scene.script_node_id)
        self.scenes.mark_deleted(scene, timestamp)
        self.nodes.mark_deleted(node, timestamp)
        self.normalize_nodes(node.script_id)

    def delete_script_tree(self, script, timestamp):
        for node in self.nodes.matching(script_id=script.id):
            for scene in self.scenes.matching(script_node_id=node.id):
                self.delete_scene_tree(scene, timestamp)
            if node.deleted_at is None:
                self.nodes.mark_deleted(node, timestamp)
        self.scripts.mark_deleted(script, timestamp)

    def restore_scene_tree(self, scene):
        timestamp = scene.deleted_at
        if timestamp is None:
            return
        node = self.nodes.get(scene.script_node_id, include_deleted=True)
        script = self.script(node.script_id)
        self.relation(script.project_id == scene.project_id and node.node_type == NodeType.SCENE)
        self.nodes.update(
            node, order_index=len(self.nodes.matching(script_id=script.id, parent_id=None))
        )
        self.nodes.restore(node)
        self.scenes.restore(scene)
        for shot in self.shots.matching(scene_id=scene.id, include_deleted=True):
            # Do not resurrect shots separately deleted before their parent.
            if shot.deleted_at == timestamp:
                self.shots.restore(shot)
        self.normalize_shots(scene.id)

    def restore_script_tree(self, script):
        timestamp = script.deleted_at
        if timestamp is None:
            return
        self.project(script.project_id)
        self.scripts.restore(script)
        for node in self.nodes.matching(script_id=script.id, include_deleted=True):
            if node.deleted_at == timestamp:
                scenes = self.scenes.matching(script_node_id=node.id, include_deleted=True)
                for scene in scenes:
                    if scene.deleted_at == timestamp:
                        self.restore_scene_tree(scene)
                if not scenes:
                    self.nodes.restore(node)
        self.normalize_nodes(script.id)


class ProjectService(WorkflowService):
    def list_projects(self, include_deleted=False):
        return self.projects.matching(include_deleted=include_deleted)

    @atomic
    def create_project(self, data):
        return self.projects.add(Project(**data.model_dump()))

    @atomic
    def update_project(self, identifier, data):
        return self.projects.update(self.project(identifier), **data.model_dump(exclude_unset=True))

    @atomic
    def delete_project(self, identifier):
        project = self.project(identifier)
        timestamp = self.deletion_timestamp()
        for script in self.scripts.matching(project_id=identifier):
            self.delete_script_tree(script, timestamp)
        self.projects.mark_deleted(project, timestamp)

    @atomic
    def restore_project(self, identifier):
        project = self.project(identifier, True)
        timestamp = project.deleted_at
        if timestamp is not None:
            self.projects.restore(project)
            for script in self.scripts.matching(project_id=identifier, include_deleted=True):
                if script.deleted_at == timestamp:
                    self.restore_script_tree(script)
        return project

    def stats(self, identifier):
        self.project(identifier)
        return {
            "scripts": self.scripts.count(project_id=identifier),
            "scenes": self.scenes.count(project_id=identifier),
            "shots": self.shots.count(project_id=identifier),
        }


class ScriptService(WorkflowService):
    def list_scripts(self, project_id, include_deleted=False):
        self.project(project_id, include_deleted)
        return self.scripts.matching(project_id=project_id, include_deleted=include_deleted)

    @atomic
    def create_script(self, project_id, data):
        self.project(project_id)
        return self.scripts.add(Script(project_id=project_id, **data.model_dump()))

    @atomic
    def update_script(self, identifier, data):
        return self.scripts.update(self.script(identifier), **data.model_dump(exclude_unset=True))

    @atomic
    def delete_script(self, identifier):
        self.delete_script_tree(self.script(identifier), self.deletion_timestamp())

    @atomic
    def restore_script(self, identifier):
        script = self.script(identifier, True)
        self.restore_script_tree(script)
        return script


class SceneService(WorkflowService):
    def read(self, scene):
        node = self.nodes.get(scene.script_node_id, include_deleted=True)
        return SceneRead(
            **{column.name: getattr(scene, column.name) for column in Scene.__table__.columns},
            script_id=node.script_id,
            order_index=node.order_index,
            shot_count=self.shots.count(scene_id=scene.id),
        )

    def list_scenes(self, project_id, include_deleted=False):
        self.project(project_id, include_deleted)
        return [
            self.read(scene)
            for scene in self.scenes.ordered(project_id, include_deleted=include_deleted)
        ]

    @atomic
    def create_scene(self, project_id, data):
        self.project(project_id)
        script = self.script(data.script_id)
        self.relation(script.project_id == project_id)
        node = self.nodes.add(
            ScriptNode(
                script_id=script.id,
                parent_id=None,
                node_type=NodeType.SCENE,
                order_index=len(self.nodes.matching(script_id=script.id, parent_id=None)),
            )
        )
        scene = self.scenes.add(
            Scene(
                project_id=project_id,
                script_node_id=node.id,
                **data.model_dump(exclude={"script_id"}),
            )
        )
        return self.read(scene)

    @atomic
    def update_scene(self, identifier, data):
        scene = self.scenes.update(self.scene(identifier), **data.model_dump(exclude_unset=True))
        return self.read(scene)

    @atomic
    def delete_scene(self, identifier):
        self.delete_scene_tree(self.scene(identifier), self.deletion_timestamp())

    @atomic
    def restore_scene(self, identifier):
        scene = self.scene(identifier, True)
        self.restore_scene_tree(scene)
        return self.read(scene)


class ShotService(WorkflowService):
    def check_code(self, project_id, code, identifier=None):
        matches = self.shots.matching(project_id=project_id, shot_code=code, include_deleted=True)
        if any(shot.id != identifier for shot in matches):
            raise AppError("SHOT_CODE_CONFLICT", "该项目中镜头编号已存在（包含已删除镜头）。", 409)

    def list_shots(self, project_id, *, include_deleted=False, **filters):
        self.project(project_id, include_deleted)
        if filters.get("scene_id"):
            self.relation(self.scene(filters["scene_id"], include_deleted).project_id == project_id)
        return self.shots.by_project(project_id, include_deleted=include_deleted, **filters)

    @atomic
    def create_shot(self, scene_id, data):
        scene = self.scene(scene_id)
        self.relation(scene.project_id == data.project_id)
        self.check_code(data.project_id, data.shot_code)
        try:
            return self.shots.add(
                Shot(
                    scene_id=scene_id,
                    order_index=len(self.shots.matching(scene_id=scene_id)),
                    **data.model_dump(),
                )
            )
        except IntegrityError as exc:
            raise AppError("SHOT_CODE_CONFLICT", "该项目中镜头编号已存在。", 409) from exc

    @atomic
    def update_shot(self, identifier, data):
        shot = self.shot(identifier)
        changes = data.model_dump(exclude_unset=True)
        self.check_code(shot.project_id, changes.get("shot_code", shot.shot_code), shot.id)
        try:
            return self.shots.update(shot, **changes)
        except IntegrityError as exc:
            raise AppError("SHOT_CODE_CONFLICT", "该项目中镜头编号已存在。", 409) from exc

    @atomic
    def soft_delete_shot(self, identifier):
        shot = self.shot(identifier)
        self.shots.mark_deleted(shot, self.deletion_timestamp())
        self.normalize_shots(shot.scene_id)

    @atomic
    def restore_shot(self, identifier):
        shot = self.shot(identifier, True)
        self.scene(shot.scene_id)
        if shot.deleted_at is not None:
            self.check_code(shot.project_id, shot.shot_code, shot.id)
            self.shots.update(shot, order_index=len(self.shots.matching(scene_id=shot.scene_id)))
            self.shots.restore(shot)
        return shot

    @atomic
    def move_shot(self, identifier, direction):
        if direction not in {"up", "down"}:
            raise AppError("INVALID_DIRECTION", "移动方向必须为 up 或 down。", 422)
        shot = self.shot(identifier)
        siblings = self.shots.matching(scene_id=shot.scene_id)
        index = siblings.index(shot)
        target = index + (-1 if direction == "up" else 1)
        if 0 <= target < len(siblings):
            siblings[index], siblings[target] = siblings[target], siblings[index]
        for order, sibling in enumerate(siblings):
            self.shots.update(sibling, order_index=order)
        return siblings
