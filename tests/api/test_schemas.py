from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from data_extractor.api.app import create_app
from data_extractor.api.dependencies import get_schema_store, get_settings
from data_extractor.config.settings import Settings
from data_extractor.registry.store import InMemorySchemaStore

_INVOICE_PAYLOAD = {
    "name": "invoice",
    "description": "Standard invoice fields",
    "fields": {
        "invoice_number": "The unique invoice ID",
        "amount": "Total amount due",
    },
}


@pytest.fixture()
def schema_client() -> TestClient:
    app = create_app()
    store = InMemorySchemaStore()
    settings = Settings(openai_api_key="sk-test", llm_provider="openai")
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_schema_store] = lambda: store
    return TestClient(app)


# ---------------------------------------------------------------------------
# POST /api/v1/schemas
# ---------------------------------------------------------------------------

def test_create_schema_returns_201(schema_client):
    r = schema_client.post("/api/v1/schemas", json=_INVOICE_PAYLOAD)
    assert r.status_code == 201


def test_create_schema_body(schema_client):
    body = schema_client.post("/api/v1/schemas", json=_INVOICE_PAYLOAD).json()
    assert body["name"] == "invoice"
    assert body["fields"]["invoice_number"] == "The unique invoice ID"
    assert "created_at" in body


def test_create_schema_overwrites_existing(schema_client):
    schema_client.post("/api/v1/schemas", json=_INVOICE_PAYLOAD)
    updated = {**_INVOICE_PAYLOAD, "fields": {"vendor": "Vendor name"}}
    r = schema_client.post("/api/v1/schemas", json=updated)
    assert r.status_code == 201
    assert r.json()["fields"] == {"vendor": "Vendor name"}


# ---------------------------------------------------------------------------
# GET /api/v1/schemas
# ---------------------------------------------------------------------------

def test_list_schemas_empty(schema_client):
    assert schema_client.get("/api/v1/schemas").json() == []


def test_list_schemas_returns_all(schema_client):
    schema_client.post("/api/v1/schemas", json=_INVOICE_PAYLOAD)
    schema_client.post("/api/v1/schemas", json={**_INVOICE_PAYLOAD, "name": "contract"})
    names = [s["name"] for s in schema_client.get("/api/v1/schemas").json()]
    assert set(names) == {"invoice", "contract"}


# ---------------------------------------------------------------------------
# GET /api/v1/schemas/{name}
# ---------------------------------------------------------------------------

def test_get_schema_by_name(schema_client):
    schema_client.post("/api/v1/schemas", json=_INVOICE_PAYLOAD)
    r = schema_client.get("/api/v1/schemas/invoice")
    assert r.status_code == 200
    assert r.json()["name"] == "invoice"


def test_get_schema_not_found(schema_client):
    assert schema_client.get("/api/v1/schemas/ghost").status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/v1/schemas/{name}
# ---------------------------------------------------------------------------

def test_delete_schema(schema_client):
    schema_client.post("/api/v1/schemas", json=_INVOICE_PAYLOAD)
    assert schema_client.delete("/api/v1/schemas/invoice").status_code == 204
    assert schema_client.get("/api/v1/schemas/invoice").status_code == 404


def test_delete_nonexistent_returns_404(schema_client):
    assert schema_client.delete("/api/v1/schemas/ghost").status_code == 404
