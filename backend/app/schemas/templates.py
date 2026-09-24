from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, Field, model_validator

from app.models.templates import TemplateCategory, TemplateScope
from app.schemas.workflow import Input, Name, Read


def nonblank(value: str) -> str:
    if not value.strip():
        raise ValueError("Template content must not be blank")
    return value


Content = Annotated[str, Field(max_length=100000), AfterValidator(nonblank)]


class TemplateCreate(Input):
    scope: TemplateScope
    project_id: UUID | None = None
    name: Name
    description: str | None = Field(default=None, max_length=100000)
    category: TemplateCategory
    template_content: Content


class TemplateUpdate(Input):
    scope: TemplateScope | None = None
    project_id: UUID | None = None
    name: Name | None = None
    description: str | None = Field(default=None, max_length=100000)
    category: TemplateCategory | None = None
    template_content: Content | None = None

    @model_validator(mode="before")
    @classmethod
    def required_not_null(cls, value):
        if isinstance(value, dict) and any(
            value[k] is None
            for k in ("scope", "name", "category", "template_content")
            if k in value
        ):
            raise ValueError("Required fields cannot be null")
        return value


class TemplateRead(Read):
    scope: TemplateScope
    project_id: UUID | None
    name: str
    description: str | None
    category: TemplateCategory
    template_content: str


class TemplateCopy(Input):
    project_id: UUID


class TemplatePreview(Input):
    template_content: Content
