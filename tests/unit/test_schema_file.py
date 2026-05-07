from __future__ import annotations

import json

import pytest

from data_extractor.core.exceptions import ConfigurationError
from data_extractor.registry.schema_file import parse_schema_file


def _enc(obj) -> bytes:
    return json.dumps(obj).encode()


# ---------------------------------------------------------------------------
# Simple format
# ---------------------------------------------------------------------------

def test_simple_format_returns_fields():
    result = parse_schema_file(_enc({"invoice_number": "The invoice ID", "amount": "Total amount"}))
    assert result == {"invoice_number": "The invoice ID", "amount": "Total amount"}


def test_simple_format_single_field():
    result = parse_schema_file(_enc({"name": "Full name of person"}))
    assert result == {"name": "Full name of person"}


def test_simple_format_empty_dict():
    result = parse_schema_file(_enc({}))
    assert result == {}


# ---------------------------------------------------------------------------
# Full format (with "fields" key)
# ---------------------------------------------------------------------------

def test_full_format_returns_fields():
    data = {
        "name": "invoice",
        "description": "Standard invoice schema",
        "fields": {"invoice_number": "The unique invoice ID"},
    }
    result = parse_schema_file(_enc(data))
    assert result == {"invoice_number": "The unique invoice ID"}


def test_full_format_without_name_or_description():
    result = parse_schema_file(_enc({"fields": {"amount": "Total due"}}))
    assert result == {"amount": "Total due"}


def test_full_format_ignores_extra_top_level_keys():
    data = {"fields": {"x": "desc"}, "extra_key": "ignored"}
    result = parse_schema_file(_enc(data))
    assert result == {"x": "desc"}


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

def test_invalid_json_raises_configuration_error():
    with pytest.raises(ConfigurationError, match="not valid JSON"):
        parse_schema_file(b"not json at all")


def test_array_input_raises_configuration_error():
    with pytest.raises(ConfigurationError, match="JSON object"):
        parse_schema_file(_enc([1, 2, 3]))


def test_non_string_description_raises_configuration_error():
    with pytest.raises(ConfigurationError, match="must be a string"):
        parse_schema_file(_enc({"invoice_number": 42}))


def test_non_string_description_in_full_format_raises():
    with pytest.raises(ConfigurationError, match="must be a string"):
        parse_schema_file(_enc({"fields": {"invoice_number": True}}))


def test_fields_not_object_raises_configuration_error():
    with pytest.raises(ConfigurationError, match="'fields' must be a JSON object"):
        parse_schema_file(_enc({"fields": ["a", "b"]}))


def test_whitespace_only_key_raises_configuration_error():
    with pytest.raises(ConfigurationError, match="non-empty string"):
        parse_schema_file(_enc({"  ": "ignored", "valid": "kept"}))
