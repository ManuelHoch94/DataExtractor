from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class ReadResult(BaseModel):
    """Raw output produced by any reader."""

    text: str
    page_count: int
    metadata: dict[str, Any] = {}


class BaseReader(ABC):
    """Abstract contract for all document readers.

    Each reader handles exactly one file type and converts it to a
    normalised :class:`ReadResult` for downstream processing.
    """

    @abstractmethod
    def supports(self, path: Path) -> bool:
        """Return True if this reader can handle *path*."""

    @abstractmethod
    def read(self, path: Path, max_pages: int | None = None) -> ReadResult:
        """Read *path* and return a :class:`ReadResult`."""
