from typing import Annotated
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import Field, SecretStr, field_validator

from app.schemas.workflow import Input, Read


class ProviderUpdate(Input):
    api_base_url: str = Field(max_length=2048)
    model: str = Field(max_length=255)
    # Omitted/null keeps the existing key; an empty string explicitly removes it.
    api_key: SecretStr | None = None

    @field_validator("api_base_url")
    @classmethod
    def valid_url(cls, value):
        value = value.strip().rstrip("/")
        try:
            url = urlsplit(value)
            valid = (
                url.scheme in {"http", "https"}
                and url.hostname
                and not url.username
                and not url.password
                and not url.query
                and not url.fragment
                and not any(c.isspace() or ord(c) < 32 for c in value)
            )
            _ = url.port
        except ValueError:
            valid = False
        if not valid:
            raise ValueError("Invalid API Base URL")
        return value

    @field_validator("model")
    @classmethod
    def valid_model(cls, value):
        value = value.strip()
        if not value or any(ord(c) < 32 for c in value):
            raise ValueError("Model is required")
        return value

    @field_validator("api_key")
    @classmethod
    def valid_key(cls, value):
        if value is not None:
            raw = value.get_secret_value()
            if len(raw) > 4096 or any(ord(c) < 33 or ord(c) > 126 for c in raw):
                raise ValueError("Invalid API Key")
        return value


class ProviderRead(Input):
    provider: str = "openai-compatible"
    api_base_url: str = ""
    model: str = ""
    api_key_configured: bool = False


class PromptPreviewRequest(Input):
    template_id: UUID


class PromptPreview(Input):
    template_id: UUID
    template_name: str
    rendered_input: str
    context: dict[str, str]
    input_hash: str


class PromptGenerate(PromptPreviewRequest):
    operation_id: UUID
    input_hash: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class PromptRead(Read):
    shot_id: UUID
    template_id: UUID
    template_name: str
    template_content: str
    prompt_type: str
    context_json: dict[str, str]
    rendered_input: str
    input_hash: str
    generated_content: str
    provider: str
    model_name: str
