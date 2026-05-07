from __future__ import annotations

import json
from unittest.mock import MagicMock

import anthropic
import pytest

from data_extractor.core.exceptions import ProcessorError
from data_extractor.core.models import ExtractedField
from data_extractor.processors.index_mapper import IndexMapper


def _make_mapper(client: MagicMock) -> IndexMapper:
    return IndexMapper(client=client, model="claude-sonnet-4-6", max_tokens=512)


def _mock_response(fields: list[dict]) -> MagicMock:
    resp = MagicMock()
    resp.content = [MagicMock(text=json.dumps(fields))]
    return resp


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_map_returns_extracted_fields(mock_anthropic_client: MagicMock):
    mapper = _make_mapper(mock_anthropic_client)
    result = mapper.map(
        text="Invoice Number: INV-001",
        schema_definition={"invoice_number": "The invoice ID"},
    )
    assert isinstance(result, list)
    assert all(isinstance(f, ExtractedField) for f in result)


def test_map_empty_schema_returns_empty(mock_anthropic_client: MagicMock):
    mapper = _make_mapper(mock_anthropic_client)
    result = mapper.map(text="some text", schema_definition={})
    assert result == []
    mock_anthropic_client.messages.create.assert_not_called()


def test_map_applies_confidence_threshold():
    client = MagicMock()
    client.messages.create.return_value = _mock_response([
        {"name": "high", "value": "yes", "confidence": 0.9, "source_text": None, "page_number": None},
        {"name": "low", "value": "maybe", "confidence": 0.2, "source_text": None, "page_number": None},
    ])
    mapper = _make_mapper(client)
    result = mapper.map("text", {"high": "desc", "low": "desc"}, confidence_threshold=0.5)
    assert len(result) == 1
    assert result[0].name == "high"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_map_raises_processor_error_on_api_failure():
    client = MagicMock()
    client.messages.create.side_effect = anthropic.APIConnectionError(request=MagicMock())
    mapper = _make_mapper(client)
    with pytest.raises(ProcessorError, match="Anthropic API call failed"):
        mapper.map("text", {"field": "desc"})


def test_map_raises_on_non_json_response():
    client = MagicMock()
    resp = MagicMock()
    resp.content = [MagicMock(text="not json at all")]
    client.messages.create.return_value = resp
    mapper = _make_mapper(client)
    with pytest.raises(ProcessorError, match="non-JSON"):
        mapper.map("text", {"field": "desc"})


def test_map_raises_on_non_array_json():
    client = MagicMock()
    resp = MagicMock()
    resp.content = [MagicMock(text='{"key": "value"}')]
    client.messages.create.return_value = resp
    mapper = _make_mapper(client)
    with pytest.raises(ProcessorError, match="Expected JSON array"):
        mapper.map("text", {"field": "desc"})


def test_map_skips_malformed_entries(caplog):
    client = MagicMock()
    client.messages.create.return_value = _mock_response([
        {"name": "ok", "value": "v", "confidence": 0.8, "source_text": None, "page_number": None},
        {"bad_key": "no name field"},
    ])
    mapper = _make_mapper(client)
    with caplog.at_level("WARNING"):
        result = mapper.map("text", {"ok": "desc", "bad": "desc"})
    assert len(result) == 1
    assert result[0].name == "ok"


def test_map_empty_content_raises():
    client = MagicMock()
    resp = MagicMock()
    resp.content = []
    client.messages.create.return_value = resp
    mapper = _make_mapper(client)
    with pytest.raises(ProcessorError):
        mapper.map("text", {"field": "desc"})
