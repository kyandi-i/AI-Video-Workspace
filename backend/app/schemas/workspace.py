from pydantic import BaseModel, ConfigDict, Field


class WorkspaceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workspace_root: str = Field(min_length=1, max_length=4096)


class WorkspaceResponse(BaseModel):
    workspace_root: str
    database_path: str
    initialized: bool
