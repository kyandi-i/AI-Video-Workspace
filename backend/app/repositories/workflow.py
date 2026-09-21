from sqlalchemy import func, select

from app.models.workflow import Project, Scene, Script, ScriptNode, Shot
from app.repositories.base import BaseRepository


class WorkflowRepository(BaseRepository):
    def matching(self, *, include_deleted=False, **filters):
        query = select(self.model).filter_by(**filters)
        if not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))
        order = [self.model.created_at, self.model.id]
        if hasattr(self.model, "order_index"):
            order.insert(0, self.model.order_index)
        return list(self.session.scalars(query.order_by(*order)))

    def count(self, **filters):
        return self.session.scalar(
            select(func.count())
            .select_from(self.model)
            .filter_by(**filters)
            .where(self.model.deleted_at.is_(None))
        )

    def mark_deleted(self, entity, timestamp):
        entity.deleted_at = timestamp
        self.session.flush()


class ProjectRepository(WorkflowRepository):
    def __init__(self, session):
        super().__init__(session, Project)

    def latest_deletion(self):
        timestamps = [
            self.session.scalar(select(func.max(model.deleted_at)))
            for model in (Project, Script, ScriptNode, Scene, Shot)
        ]
        return max((stamp for stamp in timestamps if stamp is not None), default=None)


class ScriptRepository(WorkflowRepository):
    def __init__(self, session):
        super().__init__(session, Script)


class ScriptNodeRepository(WorkflowRepository):
    def __init__(self, session):
        super().__init__(session, ScriptNode)


class SceneRepository(WorkflowRepository):
    def __init__(self, session):
        super().__init__(session, Scene)

    def ordered(self, project_id, *, include_deleted=False):
        query = select(Scene).join(ScriptNode).join(Script, Script.id == ScriptNode.script_id)
        query = query.where(Scene.project_id == project_id)
        if not include_deleted:
            query = query.where(Scene.deleted_at.is_(None))
        return list(
            self.session.scalars(
                query.order_by(
                    Script.created_at,
                    Script.id,
                    ScriptNode.order_index,
                    ScriptNode.created_at,
                    Scene.id,
                )
            )
        )


class ShotRepository(WorkflowRepository):
    def __init__(self, session):
        super().__init__(session, Shot)

    def by_project(
        self, project_id, *, scene_id=None, status=None, search=None, include_deleted=False
    ):
        query = (
            select(Shot)
            .join(Scene)
            .join(ScriptNode)
            .join(Script, Script.id == ScriptNode.script_id)
            .where(Shot.project_id == project_id)
        )
        if not include_deleted:
            query = query.where(Shot.deleted_at.is_(None))
        if scene_id:
            query = query.where(Shot.scene_id == scene_id)
        if status:
            query = query.where(Shot.status == status)
        if search:
            query = query.where(
                Shot.shot_code.icontains(search, autoescape=True)
                | Shot.title.icontains(search, autoescape=True)
            )
        return list(
            self.session.scalars(
                query.order_by(
                    Script.created_at,
                    Script.id,
                    ScriptNode.order_index,
                    ScriptNode.created_at,
                    Scene.id,
                    Shot.order_index,
                    Shot.created_at,
                    Shot.id,
                )
            )
        )
