from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from data_extractor.core.models import ExtractionRequest, ExtractionResult
from data_extractor.core.orchestrator import Orchestrator
from data_extractor.extractors.field_extractor import FieldExtractor
from data_extractor.processors.text_processor import TextProcessor
from data_extractor.readers.pdf_reader import PdfReader


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_orchestrator(extractor_fields=None):
    """Return an Orchestrator with mocked extractor."""
    if extractor_fields is None:
        extractor_fields = []

    reader = MagicMock(spec=PdfReader)
    reader.supports.return_value = True
    read_result = MagicMock()
    read_result.text = "Invoice Number: INV-001"
    read_result.page_count = 1
    read_result.metadata = {}
    reader.read.return_value = read_result

    extractor = MagicMock(spec=FieldExtractor)
    extractor.extract.return_value = extractor_fields

    processor = TextProcessor()

    return Orchestrator(
        readers=[reader],
        text_processor=processor,
        field_extractor=extractor,
    ), reader, extractor


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------

def test_run_returns_extraction_result(tmp_pdf: Path, sample_fields):
    orch, reader, extractor = _make_orchestrator(sample_fields)
    req = ExtractionRequest(file_path=tmp_pdf, schema_definition={"invoice_number": "desc"})
    result = orch.run(req)
    assert isinstance(result, ExtractionResult)
    assert result.fields == sample_fields


def test_run_calls_reader_with_max_pages(tmp_pdf: Path):
    orch, reader, extractor = _make_orchestrator()
    req = ExtractionRequest(file_path=tmp_pdf, max_pages=2)
    orch.run(req)
    reader.read.assert_called_once_with(tmp_pdf, max_pages=2)


def test_run_calls_extractor_with_clean_text(tmp_pdf: Path):
    orch, reader, extractor = _make_orchestrator()
    req = ExtractionRequest(file_path=tmp_pdf, schema_definition={"field": "desc"})
    orch.run(req)
    extractor.extract.assert_called_once()
    call_kwargs = extractor.extract.call_args.kwargs
    assert "text" in call_kwargs
    assert "schema_definition" in call_kwargs


def test_run_result_page_count(tmp_pdf: Path):
    orch, reader, extractor = _make_orchestrator()
    reader.read.return_value.page_count = 3
    req = ExtractionRequest(file_path=tmp_pdf)
    result = orch.run(req)
    assert result.page_count == 3


# ---------------------------------------------------------------------------
# from_settings()
# ---------------------------------------------------------------------------

def test_from_settings_creates_orchestrator():
    settings = MagicMock()
    settings.anthropic_api_key.get_secret_value.return_value = "sk-test"
    settings.anthropic_model = "claude-sonnet-4-6"
    settings.extraction_max_tokens = 512
    settings.extraction_confidence_threshold = 0.5

    with patch("data_extractor.core.orchestrator.anthropic.Anthropic"):
        orch = Orchestrator.from_settings(settings)

    assert isinstance(orch, Orchestrator)
    assert len(orch._readers) == 1
    assert isinstance(orch._text_processor, TextProcessor)
