from __future__ import annotations

from pathlib import Path

import pypdf

from data_extractor.core.exceptions import ReaderError
from data_extractor.readers.base import BaseReader, ReadResult

_SUPPORTED_SUFFIX = ".pdf"


class PdfReader(BaseReader):
    """Reads PDF files using *pypdf* and returns normalised text."""

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() == _SUPPORTED_SUFFIX

    def read(self, path: Path, max_pages: int | None = None) -> ReadResult:
        if not self.supports(path):
            raise ReaderError(f"PdfReader does not support file type '{path.suffix}'")

        try:
            with pypdf.PdfReader(str(path)) as reader:
                total_pages = len(reader.pages)
                limit = min(total_pages, max_pages) if max_pages else total_pages

                pages_text: list[str] = []
                for i in range(limit):
                    page_text = reader.pages[i].extract_text() or ""
                    pages_text.append(page_text)

                metadata = {
                    k: str(v)
                    for k, v in (reader.metadata or {}).items()
                    if v is not None
                }

                return ReadResult(
                    text="\n\n".join(pages_text),
                    page_count=total_pages,
                    metadata=metadata,
                )
        except pypdf.errors.PdfReadError as exc:
            raise ReaderError(f"Failed to read PDF '{path}': {exc}") from exc
        except OSError as exc:
            raise ReaderError(f"Cannot open file '{path}': {exc}") from exc
