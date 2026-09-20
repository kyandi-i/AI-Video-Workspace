import json
import os
import tempfile
from pathlib import Path

from app.core.exceptions import AppError


class BootstrapConfig:
    """The only persisted bootstrap value is the selected workspace root."""

    def __init__(self, path: Path):
        # Packaged Windows apps can redirect APPDATA across volumes. Both sides of
        # atomic replace must use the same resolved physical directory.
        self.path = path.expanduser().resolve()

    def load(self) -> Path | None:
        if not self.path.exists():
            return None
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or set(data) != {"workspace_root"}:
                raise ValueError("Invalid config shape")
            root = data["workspace_root"]
            if not isinstance(root, str) or not root.strip() or not Path(root).is_absolute():
                raise ValueError("Invalid workspace root")
            return Path(root)
        except (OSError, ValueError, TypeError) as exc:
            raise AppError(
                "BOOTSTRAP_INVALID", "启动配置无法读取，请检查 config.json。", 500
            ) from exc

    def save(self, root: Path) -> None:
        temporary: str | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=".config-",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary = handle.name
                json.dump({"workspace_root": str(root)}, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        except OSError as exc:
            raise AppError(
                "BOOTSTRAP_WRITE_FAILED", "无法保存启动配置，原工作空间仍然有效。", 500
            ) from exc
        finally:
            if temporary is not None:
                Path(temporary).unlink(missing_ok=True)
