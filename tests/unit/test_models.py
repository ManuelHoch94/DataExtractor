from pathlib import Path

import pytest
from pydantic import ValidationError

from data_extractor.core.models import ExtractedField, ExtractionRequest, ExtractionResult


# ---------------------------------------------------------------------------
# ExtractedField
# ---------------------------------------------------------------------------

def test_extracted_field_valid():
    f = ExtractedField(name="foo", value="bar", confidence=0.9)
    assert f.name == "foo"
    assert f.value == "bar"
    assert f.confidence == 0.9


def test_extracted_field_confidence_bounds():
    with pytest.raises(ValidationError):
        ExtractedField(name="x", value="y", confidence=1.5)

    with pytest.raises(ValidationError):
        ExtractedField(name="x", value="y", confidence=-0.1)


def test_extracted_field_null_value():
    f = ExtractedField(name="missing", value=None, confidence=0.0)
    assert f.value is None


# ---------------------------------------------------------------------------
# ExtractionRequest
# ---------------------------------------------------------------------------

def test_extraction_request_rejects_missing_file():
    with pytest.raises(ValidationError, match="does not exist"):
        ExtractionRequest(file_path=Path("/nonexistent/file.pdf"))


def test_extraction_request_rejects_directory(tmp_path: Path):
    with pytest.raises(ValidationError, match="not a file"):
        ExtractionRequest(file_path=tmp_path)


def test_extraction_request_valid(tmp_pdf: Path):
    req = ExtractionRequest(file_path=tmp_pdf, schema_definition={"k": "v"})
    assert req.file_path == tmp_pdf
    assert req.schema_definition == {"k": "v"}


def test_extraction_request_max_pages(tmp_pdf: Path):
    req = ExtractionRequest(file_path=tmp_pdf, max_pages=5)
    assert req.max_pages == 5


def test_extraction_request_max_pages_invalid(tmp_pdf: Path):
    with pytest.raises(ValidationError):
        ExtractionRequest(file_path=tmp_pdf, max_pages=0)


# ---------------------------------------------------------------------------
# ExtractionResult
# ---------------------------------------------------------------------------

def test_extraction_result_to_index_dict(tmp_pdf: Path, sample_fields):
    req = ExtractionRequest(file_path=tmp_pdf)
    result = ExtractionResult(request=req, fields=sample_fields)
    d = result.to_index_dict()
    assert d["invoice_number"] == "INV-2024-001"
    assert d["amount"] is None


def test_extraction_result_defaults(tmp_pdf: Path):
    req = ExtractionRequest(file_path=tmp_pdf)
    result = ExtractionResult(request=req)
    assert result.fields == []
    assert result.raw_text == ""
    assert result.page_count == 0
    assert result.metadata == {}
