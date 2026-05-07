from pathlib import Path

import pytest

from data_extractor.core.exceptions import ReaderError
from data_extractor.readers.pdf_reader import PdfReader


@pytest.fixture()
def reader() -> PdfReader:
    return PdfReader()


# ---------------------------------------------------------------------------
# supports()
# ---------------------------------------------------------------------------

def test_supports_pdf(reader: PdfReader, tmp_path: Path):
    p = tmp_path / "doc.pdf"
    p.touch()
    assert reader.supports(p) is True


def test_supports_case_insensitive(reader: PdfReader, tmp_path: Path):
    p = tmp_path / "doc.PDF"
    p.touch()
    assert reader.supports(p) is True


def test_does_not_support_txt(reader: PdfReader, tmp_path: Path):
    p = tmp_path / "doc.txt"
    p.touch()
    assert reader.supports(p) is False


# ---------------------------------------------------------------------------
# read()
# ---------------------------------------------------------------------------

def test_read_raises_for_unsupported_type(reader: PdfReader, tmp_path: Path):
    p = tmp_path / "file.docx"
    p.touch()
    with pytest.raises(ReaderError, match="does not support"):
        reader.read(p)


def test_read_raises_for_invalid_pdf(reader: PdfReader, tmp_path: Path):
    p = tmp_path / "bad.pdf"
    p.write_bytes(b"not a pdf at all")
    with pytest.raises(ReaderError):
        reader.read(p)


def test_read_returns_result(reader: PdfReader, tmp_pdf: Path):
    result = reader.read(tmp_pdf)
    assert isinstance(result.text, str)
    assert result.page_count >= 1


def test_read_respects_max_pages(reader: PdfReader, tmp_pdf: Path):
    result = reader.read(tmp_pdf, max_pages=1)
    assert result.page_count >= 1


def test_read_max_pages_larger_than_total(reader: PdfReader, tmp_pdf: Path):
    result_full = reader.read(tmp_pdf)
    result_limited = reader.read(tmp_pdf, max_pages=999)
    assert result_full.text == result_limited.text


def test_read_raises_for_missing_file(reader: PdfReader, tmp_path: Path):
    p = tmp_path / "ghost.pdf"
    with pytest.raises(ReaderError):
        reader.read(p)
