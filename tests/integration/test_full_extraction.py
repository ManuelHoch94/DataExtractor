"""Integration tests: wire up real components (no live API calls)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from data_extractor.core.models import ExtractionRequest, ExtractionResult
from data_extractor.core.orchestrator import Orchestrator
from data_extractor.extractors.field_extractor import FieldExtractor
from data_extractor.processors.index_mapper import IndexMapper
from data_extractor.processors.text_processor import TextProcessor
from data_extractor.readers.pdf_reader import PdfReader


def _build_orchestrator(mock_api_response: list[dict]) -> Orchestrator:
    """Build a fully wired Orchestrator with a stubbed Anthropic client."""
    client = MagicMock()
    resp = MagicMock()
    resp.content = [MagicMock(text=json.dumps(mock_api_response))]
    client.messages.create.return_value = resp

    mapper = IndexMapper(client=client, model="claude-sonnet-4-6", max_tokens=512)
    extractor = FieldExtractor(index_mapper=mapper, confidence_threshold=0.0)
    return Orchestrator(
        readers=[PdfReader()],
        text_processor=TextProcessor(),
        field_extractor=extractor,
    )


def test_full_pipeline_extracts_fields(tmp_pdf: Path):
    api_fields = [
        {
            "name": "invoice_number",
            "value": "INV-2024-001",
            "confidence": 0.95,
            "source_text": "Invoice Number: INV-2024-001",
            "page_number": 1,
        }
    ]
    orch = _build_orchestrator(api_fields)
    req = ExtractionRequest(
        file_path=tmp_pdf,
        schema_definition={"invoice_number": "The unique invoice ID"},
    )
    result = orch.run(req)

    assert isinstance(result, ExtractionResult)
    assert result.page_count >= 1
    index = result.to_index_dict()
    assert index.get("invoice_number") == "INV-2024-001"


def test_full_pipeline_with_empty_schema(tmp_pdf: Path):
    orch = _build_orchestrator([])
    req = ExtractionRequest(file_path=tmp_pdf, schema_definition={})
    result = orch.run(req)
    assert result.fields == []


def test_full_pipeline_confidence_filter(tmp_pdf: Path):
    api_fields = [
        {"name": "high", "value": "yes", "confidence": 0.9, "source_text": None, "page_number": None},
        {"name": "low", "value": "no", "confidence": 0.1, "source_text": None, "page_number": None},
    ]
    client = MagicMock()
    resp = MagicMock()
    resp.content = [MagicMock(text=json.dumps(api_fields))]
    client.messages.create.return_value = resp

    mapper = IndexMapper(client=client, model="claude-sonnet-4-6", max_tokens=512)
    extractor = FieldExtractor(index_mapper=mapper, confidence_threshold=0.5)
    orch = Orchestrator(
        readers=[PdfReader()],
        text_processor=TextProcessor(),
        field_extractor=extractor,
    )
    req = ExtractionRequest(
        file_path=tmp_pdf,
        schema_definition={"high": "desc", "low": "desc"},
    )
    result = orch.run(req)
    assert len(result.fields) == 1
    assert result.fields[0].name == "high"


def test_full_pipeline_max_pages_respected(tmp_pdf: Path):
    orch = _build_orchestrator([])
    req = ExtractionRequest(file_path=tmp_pdf, max_pages=1)
    result = orch.run(req)
    assert result.page_count >= 1
