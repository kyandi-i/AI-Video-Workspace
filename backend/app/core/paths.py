from pathlib import Path

from app.core.exceptions import AppError


def reject_link(path: Path, code: str = "PATH_UNSAFE") -> None:
    if path.is_symlink() or path.is_junction():
        raise AppError(code, "受管理路径不能包含符号链接或目录联接。")


def managed_path(root: Path, relative: str, code: str = "PATH_UNSAFE") -> Path:
    """Validate the lexical path and its resolved containment, including Windows paths."""
    if (
        not relative
        or "\\" in relative
        or ":" in relative
        or "\x00" in relative
        or any(part in {"", ".", ".."} for part in relative.split("/"))
    ):
        raise AppError(code, "必须使用受管理目录内的有效相对路径。")
    reject_link(root, code)
    if root.resolve() != root:
        raise AppError(code, "受管理根目录的实际位置发生变化，请重新选择工作空间。")
    candidate = root
    for part in relative.split("/"):
        candidate = candidate / part
        reject_link(candidate, code)
    try:
        if not candidate.resolve().is_relative_to(root.resolve()):
            raise AppError(code, "路径超出受管理目录。")
    except (OSError, ValueError) as exc:
        raise AppError(code, "路径无法安全解析。") from exc
    return candidate
