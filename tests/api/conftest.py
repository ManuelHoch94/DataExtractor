"""API test fixtures – shared TestClient with mocked orchestrator."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from data_extractor.api.app import create_app
from data_extractor.api.dependencies import get_orchestrator, get_schema_store, get_settings
from data_extractor.api.rate_limit import check_extract_rate_limit
from data_extractor.config.settings import Settings
from data_extractor.core.models import ExtractedField, ExtractionRequest, ExtractionResult
from data_extractor.registry.store import InMemorySchemaStore


def _make_settings(provider: str = "openai") -> Settings:
    if provider == "openai":
        return Settings(openai_api_key="sk-test", llm_provider="openai")
    return Settings(anthropic_api_key="sk-ant-test", llm_provider="anthropic")


def _make_orchestrator_mock(fields: list[ExtractedField], page_count: int = 2) -> MagicMock:
    orch = MagicMock()
    orch._field_extractor._confidence_threshold = 0.0

    def _run(req: ExtractionRequest) -> ExtractionResult:
        return ExtractionResult(
            request=req,
            fields=fields,
            raw_text="Invoice Number: INV-001",
            page_count=page_count,
            metadata={"/Author": "Test"},
        )

    orch.run.side_effect = _run
    return orch


@pytest.fixture()
def sample_fields() -> list[ExtractedField]:
    return [
        ExtractedField(
            name="invoice_number",
            value="INV-001",
            confidence=0.95,
            source_text="Invoice Number: INV-001",
            page_number=1,
        )
    ]


@pytest.fixture()
def schema_store() -> InMemorySchemaStore:
    return InMemorySchemaStore()


@pytest.fixture()
def api_client(
    tmp_pdf: Path, sample_fields: list[ExtractedField], schema_store: InMemorySchemaStore
) -> TestClient:
    """TestClient with mocked settings, orchestrator, and fresh schema store."""
    app = create_app()
    settings = _make_settings()
    orchestrator = _make_orchestrator_mock(sample_fields)

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    app.dependency_overrides[get_schema_store] = lambda: schema_store
    app.dependency_overrides[check_extract_rate_limit] = lambda: None
    return TestClient(app)


@pytest.fixture()
def api_client_empty_result(tmp_pdf: Path, schema_store: InMemorySchemaStore) -> TestClient:
    """TestClient whose orchestrator returns zero fields."""
    app = create_app()
    settings = _make_settings()
    orchestrator = _make_orchestrator_mock(fields=[])

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    app.dependency_overrides[get_schema_store] = lambda: schema_store
    app.dependency_overrides[check_extract_rate_limit] = lambda: None
    return TestClient(app)
