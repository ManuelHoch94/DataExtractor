from __future__ import annotations

from pathlib import Path

from data_extractor.core.exceptions import ReaderError
from data_extractor.readers.base import BaseReader


def resolve_reader(path: Path, readers: list[BaseReader]) -> BaseReader:
    """Return the first reader in *readers* that supports *path*.

    Raises:
        ReaderError: If no registered reader supports the file type.
    """
    for reader in readers:
        if reader.supports(path):
            return reader
    raise ReaderError(
        f"No reader available for file type '{path.suffix}'. "
        f"Registered readers: {[type(r).__name__ for r in readers]}"
    )
