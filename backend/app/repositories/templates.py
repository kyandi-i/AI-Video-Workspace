from sqlalchemy import or_, select

from app.models.templates import PromptTemplate
from app.models.workflow import Project
from app.repositories.workflow import WorkflowRepository


class PromptTemplateRepository(WorkflowRepository):
    def __init__(self, session):
        super().__init__(session, PromptTemplate)

    def search(
        self,
        scope=None,
        project_id=None,
        category=None,
        search=None,
        include_deleted=False,
        include_global=False,
    ):
        query = select(PromptTemplate).outerjoin(Project)
        # Parent deletion hides children until the parent is restored, even in the bin.
        query = query.where(or_(PromptTemplate.project_id.is_(None), Project.deleted_at.is_(None)))
        if not include_deleted:
            query = query.where(PromptTemplate.deleted_at.is_(None))
        if scope:
            query = query.where(PromptTemplate.scope == scope)
        if project_id:
            condition = PromptTemplate.project_id == project_id
            if include_global:
                condition = or_(condition, PromptTemplate.scope == "GLOBAL")
            query = query.where(condition)
        if category:
            query = query.where(PromptTemplate.category == category)
        if search:
            query = query.where(
                or_(
                    PromptTemplate.name.icontains(search, autoescape=True),
                    PromptTemplate.description.icontains(search, autoescape=True),
                )
            )
        return list(
            self.session.scalars(
                query.order_by(PromptTemplate.updated_at.desc(), PromptTemplate.id)
            )
        )
