from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import BinaryIO


@dataclass(frozen=True)
class StorageObject:
    original_filename: str
    relative_path: str
    file_size: int
    checksum: str

    @property
    def stored_filename(self) -> str:
        return PurePosixPath(self.relative_path).name


class StorageProvider(ABC):
    @abstractmethod
    def save_file(self, source: Path, *, original_filename: str | None = None) -> StorageObject:
        """Publish a complete managed copy and return portable metadata."""

    @abstractmethod
    def delete_file(self, relative_path: str) -> None:
        """Delete a managed file; missing files are treated as already removed."""

    @abstractmethod
    def move_file(self, source: str, destination: str) -> str:
        """Move within managed storage without overwriting an existing file."""

    @abstractmethod
    def exists(self, relative_path: str) -> bool: ...

    @abstractmethod
    def get_absolute_path(self, relative_path: str) -> Path:
        """Local delivery adapter only; never persist this value in domain metadata."""

    @abstractmethod
    def get_file(self, relative_path: str) -> BinaryIO:
        """Open for reading. Caller owns closing the handle."""

    @abstractmethod
    def create_thumbnail(self, relative_path: str) -> str: ...

    @abstractmethod
    def stage_upload(self):
        """Context manager yielding (relative key, writable binary handle); always cleans up."""

    @abstractmethod
    def inspect_media(self, relative_path: str): ...

    @contextmanager
    def save_with_compensation(self, source: Path) -> Iterator[StorageObject]:
        """Enclose a DB transaction (including commit) to clean up a rejected import."""
        stored = self.save_file(source)
        try:
            yield stored
        except BaseException:
            self.delete_file(stored.relative_path)
            raise
