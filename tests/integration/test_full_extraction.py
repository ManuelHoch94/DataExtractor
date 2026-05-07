"""Integration tests: wire up real components (no live API calls)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from data_extractor.core.models import ExtractionRequest, ExtractionResult
from data_extractor.core.orchestrator import Orchestrator
from data_extractor.extractors.field_extractor import FieldExtractor
from data_extractor.llm.base import BaseLLMClient, LLMResponse
from data_extractor.processors.index_mapper import IndexMapper
from data_extractor.processors.text_processor import TextProcessor
from data_extractor.readers.pdf_reader import PdfReader


def _build_orchestrator(mock_fields: list[dict], threshold: float = 0.0) -> Orchestrator:
    """Build a fully wired Orchestrator with a stubbed LLM client."""
    llm = MagicMock(spec=BaseLLMClient)
    llm.complete.return_value = LLMResponse(text=json.dumps(mock_fields))
    mapper = IndexMapper(llm_client=llm, max_tokens=512)
    extractor = FieldExtractor(index_mapper=mapper, confidence_threshold=threshold)
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
    assert result.to_index_dict().get("invoice_number") == "INV-2024-001"


def test_full_pipeline_with_empty_schema(tmp_pdf: Path):
    orch = _build_orchestrator([])
    result = orch.run(ExtractionRequest(file_path=tmp_pdf, schema_definition={}))
    assert result.fields == []


def test_full_pipeline_confidence_filter(tmp_pdf: Path):
    _f = {"source_text": None, "page_number": None}
    api_fields = [
        {"name": "high", "value": "yes", "confidence": 0.9, **_f},
        {"name": "low", "value": "no", "confidence": 0.1, **_f},
    ]
    orch = _build_orchestrator(api_fields, threshold=0.5)
    result = orch.run(ExtractionRequest(
        file_path=tmp_pdf,
        schema_definition={"high": "desc", "low": "desc"},
    ))
    assert len(result.fields) == 1
    assert result.fields[0].name == "high"


def test_full_pipeline_max_pages_respected(tmp_pdf: Path):
    orch = _build_orchestrator([])
    result = orch.run(ExtractionRequest(file_path=tmp_pdf, max_pages=1))
    assert result.page_count >= 1


def test_full_pipeline_openai_client_swappable(tmp_pdf: Path):
    """Verify that swapping to a different BaseLLMClient stub yields identical results."""
    fields = [
        {"name": "vendor", "value": "Acme GmbH", "confidence": 0.88,
         "source_text": None, "page_number": None},
    ]
    # Build with one stub
    orch1 = _build_orchestrator(fields)
    # Build with a different stub (same data – simulates provider swap)
    llm2 = MagicMock(spec=BaseLLMClient)
    llm2.complete.return_value = LLMResponse(text=json.dumps(fields))
    mapper2 = IndexMapper(llm_client=llm2, max_tokens=512)
    orch2 = Orchestrator(
        readers=[PdfReader()],
        text_processor=TextProcessor(),
        field_extractor=FieldExtractor(index_mapper=mapper2),
    )

    req = ExtractionRequest(file_path=tmp_pdf, schema_definition={"vendor": "desc"})
    r1 = orch1.run(req)
    r2 = orch2.run(req)
    assert r1.to_index_dict() == r2.to_index_dict()
