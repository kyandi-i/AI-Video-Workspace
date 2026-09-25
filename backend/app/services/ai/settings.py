import json
import os
import tempfile
from pathlib import Path
from threading import Lock
from typing import Protocol

from pydantic import SecretStr, ValidationError

from app.core.exceptions import AppError
from app.core.paths import reject_link
from app.schemas.ai import ProviderRead, ProviderUpdate


class AISettingsStorageProvider(Protocol):
    """Private local configuration storage, separate from project/asset storage."""

    def read(self) -> ProviderUpdate | None: ...
    def write(self, config: ProviderUpdate) -> None: ...


class LocalAISettingsStorageProvider:
    def __init__(self, bootstrap_path: Path):
        self.path = bootstrap_path.with_name("ai-provider.json")

    def read(self):
        try:
            reject_link(self.path)
            if not self.path.exists():
                return None
            return ProviderUpdate.model_validate_json(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, ValidationError):
            raise AppError("AI_CONFIG_INVALID", "AI 配置无法读取，请重新保存设置。", 503) from None

    def write(self, config):
        temporary = None
        try:
            reject_link(self.path)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.path.parent, delete=False
            ) as handle:
                temporary = Path(handle.name)
                # Private config only; never serialize this into an API response or export.
                json.dump(
                    {
                        "api_base_url": config.api_base_url,
                        "model": config.model,
                        "api_key": config.api_key.get_secret_value() if config.api_key else "",
                    },
                    handle,
                )
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        except OSError:
            raise AppError("AI_CONFIG_WRITE_FAILED", "无法保存 AI 本地配置。", 500) from None
        finally:
            if temporary and temporary.exists():
                temporary.unlink()


class AISettingsService:
    def __init__(self, storage: AISettingsStorageProvider):
        self.storage = storage
        self.lock = Lock()

    @staticmethod
    def public(config):
        return ProviderRead(
            api_base_url=config.api_base_url if config else "",
            model=config.model if config else "",
            api_key_configured=bool(
                config and config.api_key and config.api_key.get_secret_value()
            ),
        )

    def read(self):
        with self.lock:
            return self.public(self.storage.read())

    def update(self, data):
        with self.lock:
            try:
                previous = self.storage.read()
            except AppError:
                if data.api_key is None:
                    raise
                previous = None
            key = data.api_key
            if key is None:
                key = previous.api_key if previous else SecretStr("")
            config = data.model_copy(update={"api_key": key})
            self.storage.write(config)
            return self.public(config)

    def configured(self):
        with self.lock:
            config = self.storage.read()
        if config is None:
            raise AppError("AI_NOT_CONFIGURED", "请先在 Settings 配置 AI Provider。", 409)
        if not config.api_key or not config.api_key.get_secret_value():
            raise AppError("AI_KEY_MISSING", "请先在 Settings 保存 API Key。", 409)
        return config
