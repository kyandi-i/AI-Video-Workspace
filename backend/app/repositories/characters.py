from sqlalchemy import select

from app.models.assets import Asset
from app.models.characters import Character, CharacterState
from app.repositories.workflow import WorkflowRepository


class CharacterRepository(WorkflowRepository):
    def __init__(self, session):
        super().__init__(session, Character)

    def search(self, project_id, search=None, include_deleted=False):
        query = select(Character).where(Character.project_id == project_id)
        if not include_deleted:
            query = query.where(Character.deleted_at.is_(None))
        if search:
            query = query.where(
                Character.name.icontains(search, autoescape=True)
                | Character.description.icontains(search, autoescape=True)
            )
        return list(self.session.scalars(query.order_by(Character.created_at, Character.id)))


class CharacterStateRepository(WorkflowRepository):
    def __init__(self, session):
        super().__init__(session, CharacterState)


class CharacterLinkRepository(WorkflowRepository):
    def assets(self, **filters):
        return list(
            self.session.scalars(
                select(Asset)
                .join(self.model)
                .where(
                    *(getattr(self.model, key) == value for key, value in filters.items()),
                    self.model.deleted_at.is_(None),
                    Asset.deleted_at.is_(None),
                )
                .order_by(self.model.created_at, self.model.id)
            )
        )
