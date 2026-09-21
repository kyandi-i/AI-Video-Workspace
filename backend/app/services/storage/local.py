import hashlib
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from app.core.exceptions import AppError
from app.core.paths import managed_path, reject_link
from app.services.storage.base import StorageObject, StorageProvider


class LocalStorageProvider(StorageProvider):
    def __init__(self, storage_root: Path):
        reject_link(storage_root)
        self.root = storage_root.resolve()
        if not self.root.is_dir():
            raise AppError("STORAGE_NOT_READY", "存储目录尚未初始化。", 503)

    def _safe(self, relative_path: str) -> Path:
        if not isinstance(relative_path, str):
            raise AppError("PATH_UNSAFE", "存储路径必须为相对路径字符串。")
        parts = relative_path.split("/")
        if len(parts) < 2 or parts[0] not in {"assets", "thumbnails", "temp"}:
            raise AppError("PATH_UNSAFE", "路径不属于受管理文件目录。")
        # Apply Windows restrictions everywhere to keep storage keys portable.
        reserved = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            *(f"COM{i}" for i in range(1, 10)),
            *(f"LPT{i}" for i in range(1, 10)),
        }
        if any(
            part.endswith((" ", "."))
            or any(c in part for c in '<>"|?*')
            or any(ord(c) < 32 for c in part)
            or part.split(".")[0].upper() in reserved
            for part in parts
        ):
            raise AppError("PATH_UNSAFE", "存储路径包含无效名称。")
        return managed_path(self.root, relative_path)

    def get_absolute_path(self, relative_path: str) -> Path:
        return self._safe(relative_path)

    def get_file(self, relative_path: str) -> BinaryIO:
        path = self._safe(relative_path)
        if not path.is_file():
            raise AppError("FILE_NOT_FOUND", "受管理文件不存在。", 404)
        try:
            return path.open("rb")
        except OSError as exc:
            raise AppError("FILE_READ_FAILED", "无法读取受管理文件。", 500) from exc

    def exists(self, relative_path: str) -> bool:
        return self._safe(relative_path).is_file()

    def _copy(self, source: BinaryIO, destination: BinaryIO) -> tuple[int, str]:
        digest = hashlib.sha256()
        size = 0
        while block := source.read(1024 * 1024):
            destination.write(block)
            digest.update(block)
            size += len(block)
        return size, digest.hexdigest()

    def _move_no_replace(self, source: Path, destination: Path) -> None:
        if os.name == "nt":
            # Windows rename is atomic and refuses an existing destination, also on exFAT.
            os.rename(source, destination)
            return
        # POSIX rename overwrites. Publish with an exclusive link, then remove the old name.
        os.link(source, destination)
        try:
            source.unlink()
        except OSError:
            destination.unlink()
            raise

    def save_file(self, source: Path, *, original_filename: str | None = None) -> StorageObject:
        source = Path(source)
        if not source.is_file():
            raise AppError("FILE_NOT_FOUND", "源文件不存在或不是普通文件。", 404)
        original = original_filename if original_filename is not None else source.name
        suffix = Path(original).suffix.lower()
        if not re.fullmatch(r"\.[a-z0-9]{1,16}", suffix):
            suffix = ""
        identifier = str(uuid4())
        relative = f"assets/{identifier[:2]}/{identifier}{suffix}"
        destination = self._safe(relative)
        temporary: Path | None = None
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            temp_directory = self._safe("temp/probe").parent
            with (
                source.open("rb") as input_file,
                tempfile.NamedTemporaryFile(
                    mode="w+b",
                    prefix="import-",
                    suffix=".partial",
                    dir=temp_directory,
                    delete=False,
                ) as output_file,
            ):
                temporary = Path(output_file.name)
                size, checksum = self._copy(input_file, output_file)
                output_file.flush()
                os.fsync(output_file.fileno())
                if output_file.tell() != size:
                    raise OSError("Incomplete copy")
            # Only publish the completed temporary file, never a partially written destination.
            self._safe(relative)
            self._safe(temporary.relative_to(self.root).as_posix())
            self._move_no_replace(temporary, destination)
            temporary = None
            return StorageObject(original, relative, size, checksum)
        except FileExistsError as exc:
            raise AppError("FILE_CONFLICT", "内部存储名称冲突，请重试。", 409) from exc
        except OSError as exc:
            raise AppError(
                "FILE_WRITE_FAILED", "保存文件失败，请检查磁盘空间与目录权限。", 500
            ) from exc
        finally:
            if temporary is not None:
                self._safe(temporary.relative_to(self.root).as_posix()).unlink(missing_ok=True)

    def delete_file(self, relative_path: str) -> None:
        path = self._safe(relative_path)
        if path.exists() and not path.is_file():
            raise AppError("PATH_UNSAFE", "只能删除受管理的普通文件，不能删除目录。")
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise AppError(
                "FILE_DELETE_FAILED", "文件删除失败，请检查文件是否被占用。", 409
            ) from exc

    def move_file(self, source: str, destination: str) -> str:
        source_path, target_path = self._safe(source), self._safe(destination)
        if not source_path.is_file():
            raise AppError("FILE_NOT_FOUND", "待移动文件不存在。", 404)
        if source_path == target_path:
            return source
        if target_path.exists():
            raise AppError("FILE_CONFLICT", "目标文件已存在，不允许覆盖。", 409)
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            self._safe(source)
            self._safe(destination)
            self._move_no_replace(source_path, target_path)
        except FileExistsError as exc:
            raise AppError("FILE_CONFLICT", "目标文件已存在，不允许覆盖。", 409) from exc
        except OSError as exc:
            raise AppError("FILE_MOVE_FAILED", "文件移动失败，原文件已保留。", 500) from exc
        return destination

    def create_thumbnail(self, relative_path: str) -> str:
        from app.services.storage.media import decode_preview

        _, preview = decode_preview(self._safe(relative_path))
        key = f"thumbnails/{uuid4()}.jpg"
        destination = self._safe(key)
        published = False
        try:
            with self.stage_upload() as (temporary, output):
                preview.save(output, format="JPEG", quality=82)
                output.flush()
                os.fsync(output.fileno())
                output.close()
                self._move_no_replace(self._safe(temporary), destination)
                published = True
            return key
        except BaseException:
            if published:
                destination.unlink(missing_ok=True)
            raise
        finally:
            preview.close()

    def inspect_media(self, relative_path: str):
        from app.services.storage.media import decode_preview

        info, preview = decode_preview(self._safe(relative_path))
        preview.close()
        return info

    @contextmanager
    def stage_upload(self):
        key = f"temp/{uuid4()}.partial"
        path = self._safe(key)
        # Exclusive-open failure must not remove another operation's temporary file.
        output = path.open("xb+")
        try:
            with output:
                yield key, output
        finally:
            self._safe(key).unlink(missing_ok=True)
