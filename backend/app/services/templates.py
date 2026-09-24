from sqlalchemy.exc import IntegrityError

from app.core.exceptions import AppError
from app.models.templates import PromptTemplate, TemplateScope
from app.repositories.templates import PromptTemplateRepository
from app.services.template_placeholders import validate_content
from app.services.workflow import WorkflowService, atomic


class PromptTemplateService(WorkflowService):
    def __init__(self, session):
        super().__init__(session)
        self.templates = PromptTemplateRepository(session)

    def detail(self, identifier, include_deleted=False):
        entity = self.required(self.templates, identifier, "PROMPT_TEMPLATE", include_deleted)
        if entity.project_id:
            self.project(entity.project_id)
        return entity

    def list_templates(self, **filters):
        if filters.get("project_id"):
            self.project(filters["project_id"])
        return self.templates.search(**filters)

    def save(self, values, entity=None):
        scope, project_id = values["scope"], values["project_id"]
        if (scope == TemplateScope.GLOBAL and project_id is not None) or (
            scope == TemplateScope.PROJECT and project_id is None
        ):
            raise AppError(
                "INVALID_TEMPLATE_SCOPE", "Global 模板不能关联项目；Project 模板必须关联项目。"
            )
        if project_id:
            self.project(project_id)
        validate_content(values["template_content"])
        matches = self.templates.matching(
            scope=scope, project_id=project_id, name=values["name"], include_deleted=True
        )
        if any(e.id != (entity.id if entity else None) for e in matches):
            raise AppError(
                "PROMPT_TEMPLATE_NAME_CONFLICT",
                "该名称已存在（包含已删除模板），请改名或恢复原模板。",
                409,
            )
        try:
            return (
                self.templates.update(entity, **values)
                if entity
                else self.templates.add(PromptTemplate(**values))
            )
        except IntegrityError as exc:
            raise AppError(
                "PROMPT_TEMPLATE_NAME_CONFLICT", "模板名称冲突，请使用其他名称。", 409
            ) from exc

    @atomic
    def create(self, data):
        return self.save(data.model_dump())

    @atomic
    def update(self, identifier, data):
        entity = self.detail(identifier)
        values = self.values(entity)
        values.update(data.model_dump(exclude_unset=True))
        return self.save(values, entity)

    @staticmethod
    def values(entity):
        return {
            key: getattr(entity, key)
            for key in (
                "scope",
                "project_id",
                "name",
                "description",
                "category",
                "template_content",
            )
        }

    @atomic
    def delete(self, identifier):
        self.templates.soft_delete(self.detail(identifier))

    @atomic
    def restore(self, identifier):
        return self.templates.restore(self.detail(identifier, True))

    def copy_values(self, source, scope, project_id, preserve_name=False):
        values = self.values(source)
        values.update(scope=scope, project_id=project_id)
        # Deleted names remain reserved, matching Character lifecycle semantics.
        names = {
            e.name
            for e in self.templates.matching(
                scope=scope, project_id=project_id, include_deleted=True
            )
        }
        if preserve_name and source.name not in names:
            return self.save(values)
        number = 1
        while True:
            suffix = " Copy" if number == 1 else f" Copy {number}"
            candidate = source.name[: 255 - len(suffix)] + suffix
            if candidate not in names:
                values["name"] = candidate
                return self.save(values)
            number += 1

    @atomic
    def duplicate(self, identifier):
        source = self.detail(identifier)
        return self.copy_values(source, source.scope, source.project_id)

    @atomic
    def copy_to_project(self, identifier, project_id):
        source = self.detail(identifier)
        if source.scope != TemplateScope.GLOBAL:
            raise AppError("INVALID_TEMPLATE_SCOPE", "只有 Global 模板可以复制到项目。")
        self.project(project_id)
        return self.copy_values(source, TemplateScope.PROJECT, project_id, preserve_name=True)
