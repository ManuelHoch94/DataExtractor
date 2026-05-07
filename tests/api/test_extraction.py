from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from data_extractor.api.app import create_app
from data_extractor.api.dependencies import get_orchestrator, get_settings
from data_extractor.config.settings import Settings
from data_extractor.core.exceptions import DataExtractorError, ReaderError
from data_extractor.core.models import ExtractedField, ExtractionRequest, ExtractionResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pdf_upload(path: Path, schema: dict | None = None, extra_form: dict | None = None):
    req_body = json.dumps({"schema_definition": schema or {}})
    files = {"file": ("invoice.pdf", path.read_bytes(), "application/pdf")}
    data = {"request": req_body, **(extra_form or {})}
    return files, data


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_extract_returns_200(api_client: TestClient, tmp_pdf: Path):
    files, data = _pdf_upload(tmp_pdf, {"invoice_number": "The invoice ID"})
    r = api_client.post("/api/v1/extract", files=files, data=data)
    assert r.status_code == 200


def test_extract_response_structure(api_client: TestClient, tmp_pdf: Path):
    files, data = _pdf_upload(tmp_pdf, {"invoice_number": "The invoice ID"})
    body = api_client.post("/api/v1/extract", files=files, data=data).json()
    assert "fields" in body
    assert "index" in body
    assert "page_count" in body
    assert "filename" in body


def test_extract_filename_in_response(api_client: TestClient, tmp_pdf: Path):
    files, data = _pdf_upload(tmp_pdf)
    body = api_client.post("/api/v1/extract", files=files, data=data).json()
    assert body["filename"] == "invoice.pdf"


def test_extract_fields_populated(api_client: TestClient, tmp_pdf: Path):
    files, data = _pdf_upload(tmp_pdf, {"invoice_number": "desc"})
    body = api_client.post("/api/v1/extract", files=files, data=data).json()
    assert len(body["fields"]) == 1
    assert body["fields"][0]["name"] == "invoice_number"
    assert body["index"]["invoice_number"] == "INV-001"


def test_extract_empty_schema_returns_no_fields(api_client_empty_result: TestClient, tmp_pdf: Path):
    files, data = _pdf_upload(tmp_pdf, {})
    body = api_client_empty_result.post("/api/v1/extract", files=files, data=data).json()
    assert body["fields"] == []
    assert body["index"] == {}


def test_extract_default_request_when_omitted(api_client: TestClient, tmp_pdf: Path):
    files = {"file": ("doc.pdf", tmp_pdf.read_bytes(), "application/pdf")}
    r = api_client.post("/api/v1/extract", files=files)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

def test_extract_rejects_non_pdf(api_client: TestClient, tmp_path: Path):
    txt = tmp_path / "doc.txt"
    txt.write_text("hello")
    files = {"file": ("doc.txt", txt.read_bytes(), "text/plain")}
    r = api_client.post("/api/v1/extract", files=files)
    assert r.status_code == 400
    assert "Unsupported file type" in r.json()["detail"]


def test_extract_rejects_malformed_request_json(api_client: TestClient, tmp_pdf: Path):
    files = {"file": ("doc.pdf", tmp_pdf.read_bytes(), "application/pdf")}
    r = api_client.post("/api/v1/extract", files=files, data={"request": "not json"})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Domain error mapping
# ---------------------------------------------------------------------------

def test_extract_maps_reader_error_to_400(tmp_pdf: Path):
    app = create_app()
    settings = Settings(openai_api_key="sk-test", llm_provider="openai")
    orch = MagicMock()
    orch._field_extractor._confidence_threshold = 0.0
    orch.run.side_effect = ReaderError("corrupted PDF")

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_orchestrator] = lambda: orch

    files = {"file": ("bad.pdf", tmp_pdf.read_bytes(), "application/pdf")}
    r = TestClient(app).post("/api/v1/extract", files=files)
    assert r.status_code == 400
    assert "corrupted PDF" in r.json()["detail"]


def test_extract_maps_extractor_error_to_500(tmp_pdf: Path):
    app = create_app()
    settings = Settings(openai_api_key="sk-test", llm_provider="openai")
    orch = MagicMock()
    orch._field_extractor._confidence_threshold = 0.0
    orch.run.side_effect = DataExtractorError("LLM timeout")

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_orchestrator] = lambda: orch

    files = {"file": ("doc.pdf", tmp_pdf.read_bytes(), "application/pdf")}
    r = TestClient(app).post("/api/v1/extract", files=files)
    assert r.status_code == 500


# ---------------------------------------------------------------------------
# Swagger / OpenAPI
# ---------------------------------------------------------------------------

def test_openapi_schema_available(api_client: TestClient):
    r = api_client.get("/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    assert schema["info"]["title"] == "DataExtractor API"


def test_swagger_ui_available(api_client: TestClient):
    assert api_client.get("/docs").status_code == 200


def test_redoc_available(api_client: TestClient):
    assert api_client.get("/redoc").status_code == 200
