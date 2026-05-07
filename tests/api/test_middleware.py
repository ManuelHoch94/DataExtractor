from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from data_extractor.api.app import create_app
from data_extractor.api.dependencies import get_orchestrator, get_settings
from data_extractor.config.settings import Settings


def _client() -> TestClient:
    app = create_app()
    settings = Settings(openai_api_key="sk-test", llm_provider="openai")
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_orchestrator] = lambda: MagicMock()
    return TestClient(app)


def test_request_id_header_present():
    r = _client().get("/api/v1/health")
    assert "x-request-id" in r.headers


def test_cors_headers_present():
    r = _client().options(
        "/api/v1/health",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )
    assert r.headers.get("access-control-allow-origin") is not None
