from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from data_extractor.core.exceptions import ProcessorError
from data_extractor.core.models import ExtractedField
from data_extractor.llm.base import BaseLLMClient, LLMResponse
from data_extractor.processors.index_mapper import IndexMapper


def _make_mapper(client: BaseLLMClient) -> IndexMapper:
    return IndexMapper(llm_client=client, max_tokens=512)


def _mock_client(fields: list[dict]) -> MagicMock:
    client = MagicMock(spec=BaseLLMClient)
    client.complete.return_value = LLMResponse(text=json.dumps(fields))
    return client


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_map_returns_extracted_fields(mock_llm_client: MagicMock):
    mapper = _make_mapper(mock_llm_client)
    result = mapper.map(
        text="Invoice Number: INV-001",
        schema_definition={"invoice_number": "The invoice ID"},
    )
    assert isinstance(result, list)
    assert all(isinstance(f, ExtractedField) for f in result)


def test_map_empty_schema_returns_empty(mock_llm_client: MagicMock):
    mapper = _make_mapper(mock_llm_client)
    result = mapper.map(text="some text", schema_definition={})
    assert result == []
    mock_llm_client.complete.assert_not_called()


def test_map_applies_confidence_threshold():
    _f = {"source_text": None, "page_number": None}
    client = _mock_client([
        {"name": "high", "value": "yes", "confidence": 0.9, **_f},
        {"name": "low", "value": "maybe", "confidence": 0.2, **_f},
    ])
    mapper = _make_mapper(client)
    result = mapper.map("text", {"high": "desc", "low": "desc"}, confidence_threshold=0.5)
    assert len(result) == 1
    assert result[0].name == "high"


def test_map_passes_max_tokens_to_client():
    client = _mock_client([])
    mapper = IndexMapper(llm_client=client, max_tokens=1024)
    mapper.map("text", {"field": "desc"})
    _, kwargs = client.complete.call_args
    assert kwargs["max_tokens"] == 1024


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_map_raises_on_non_json_response():
    client = MagicMock(spec=BaseLLMClient)
    client.complete.return_value = LLMResponse(text="not json at all")
    mapper = _make_mapper(client)
    with pytest.raises(ProcessorError, match="non-JSON"):
        mapper.map("text", {"field": "desc"})


def test_map_raises_on_non_array_json():
    client = MagicMock(spec=BaseLLMClient)
    client.complete.return_value = LLMResponse(text='{"key": "value"}')
    mapper = _make_mapper(client)
    with pytest.raises(ProcessorError, match="Expected JSON array"):
        mapper.map("text", {"field": "desc"})


def test_map_skips_malformed_entries(caplog):
    client = _mock_client([
        {"name": "ok", "value": "v", "confidence": 0.8, "source_text": None, "page_number": None},
        {"bad_key": "no name field"},
    ])
    mapper = _make_mapper(client)
    with caplog.at_level("WARNING"):
        result = mapper.map("text", {"ok": "desc", "bad": "desc"})
    assert len(result) == 1
    assert result[0].name == "ok"


def test_map_propagates_processor_error_from_client():
    client = MagicMock(spec=BaseLLMClient)
    client.complete.side_effect = ProcessorError("upstream failure")
    mapper = _make_mapper(client)
    with pytest.raises(ProcessorError, match="upstream failure"):
        mapper.map("text", {"field": "desc"})
