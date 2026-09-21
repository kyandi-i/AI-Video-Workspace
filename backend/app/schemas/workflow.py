from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.models.workflow import ProjectStatus, ShotStatus

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
Code = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
Duration = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Update(Input):
    @model_validator(mode="before")
    @classmethod
    def reject_null(cls, value):
        if isinstance(value, dict) and any(v is None for v in value.values()):
            raise ValueError("字段不能为 null；省略字段以保留原值。")
        return value


class Read(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class ProjectCreate(Input):
    name: Name
    description: str = ""
    status: ProjectStatus = ProjectStatus.DRAFT


class ProjectUpdate(Update):
    name: Name | None = None
    description: str | None = None
    status: ProjectStatus | None = None


class ProjectRead(Read):
    name: str
    description: str
    status: ProjectStatus


class ProjectStats(BaseModel):
    scripts: int
    scenes: int
    shots: int


class ScriptCreate(Input):
    name: Name
    description: str = ""


class ScriptUpdate(Update):
    name: Name | None = None
    description: str | None = None


class ScriptRead(Read):
    project_id: UUID
    name: str
    description: str


class SceneCreate(Input):
    script_id: UUID
    name: Name
    description: str = ""
    fixed_constraints: str = ""
    negative_constraints: str = ""


class SceneUpdate(Update):
    name: Name | None = None
    description: str | None = None
    fixed_constraints: str | None = None
    negative_constraints: str | None = None


class SceneRead(Read):
    project_id: UUID
    script_node_id: UUID
    name: str
    description: str
    fixed_constraints: str
    negative_constraints: str
    script_id: UUID
    order_index: int
    shot_count: int


class ShotCreate(Input):
    project_id: UUID
    shot_code: Code
    title: Name
    description: str = ""
    duration_seconds: Duration = 0
    status: ShotStatus = ShotStatus.DRAFT
    creative_requirement: str = ""


class ShotUpdate(Update):
    shot_code: Code | None = None
    title: Name | None = None
    description: str | None = None
    duration_seconds: Duration | None = None
    status: ShotStatus | None = None
    creative_requirement: str | None = None


class ShotRead(Read):
    project_id: UUID
    scene_id: UUID
    shot_code: str
    title: str
    description: str
    duration_seconds: float
    order_index: int
    status: ShotStatus
    creative_requirement: str


class ShotMove(Input):
    direction: Literal["up", "down"]
