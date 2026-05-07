from fastapi.testclient import TestClient

import data_extractor


def test_health_returns_200(api_client: TestClient):
    r = api_client.get("/api/v1/health")
    assert r.status_code == 200


def test_health_response_body(api_client: TestClient):
    body = api_client.get("/api/v1/health").json()
    assert body["status"] == "ok"
    assert body["version"] == data_extractor.__version__
    assert body["llm_provider"] == "openai"


def test_health_not_found_on_wrong_path(api_client: TestClient):
    assert api_client.get("/health").status_code == 404
