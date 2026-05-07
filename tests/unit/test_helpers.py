from pathlib import Path
from unittest.mock import MagicMock

import pytest

from data_extractor.core.exceptions import ReaderError
from data_extractor.readers.base import BaseReader
from data_extractor.utils.helpers import resolve_reader


def _reader(supports: bool) -> BaseReader:
    r = MagicMock(spec=BaseReader)
    r.supports.return_value = supports
    r.__class__.__name__ = "MockReader"
    return r


def test_resolve_reader_returns_first_match(tmp_path: Path):
    path = tmp_path / "file.pdf"
    path.touch()
    r1 = _reader(False)
    r2 = _reader(True)
    result = resolve_reader(path, [r1, r2])
    assert result is r2


def test_resolve_reader_raises_when_no_match(tmp_path: Path):
    path = tmp_path / "file.xyz"
    path.touch()
    with pytest.raises(ReaderError, match="No reader available"):
        resolve_reader(path, [_reader(False), _reader(False)])


def test_resolve_reader_empty_list(tmp_path: Path):
    path = tmp_path / "file.pdf"
    path.touch()
    with pytest.raises(ReaderError):
        resolve_reader(path, [])
