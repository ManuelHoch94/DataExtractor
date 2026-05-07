import pytest

from data_extractor.registry.models import SchemaEntry
from data_extractor.registry.store import BaseSchemaStore, InMemorySchemaStore


@pytest.fixture()
def store() -> InMemorySchemaStore:
    return InMemorySchemaStore()


@pytest.fixture()
def invoice_entry() -> SchemaEntry:
    return SchemaEntry(
        name="invoice",
        description="Standard invoice fields",
        fields={"invoice_number": "The unique invoice ID", "amount": "Total amount due"},
    )


# ---------------------------------------------------------------------------
# save / get
# ---------------------------------------------------------------------------

def test_save_and_get(store, invoice_entry):
    saved = store.save(invoice_entry)
    assert saved.name == "invoice"
    assert store.get("invoice") == saved


def test_get_returns_none_for_missing(store):
    assert store.get("nonexistent") is None


def test_save_overwrites_existing(store, invoice_entry):
    store.save(invoice_entry)
    updated = SchemaEntry(name="invoice", fields={"vendor": "Vendor name"})
    result = store.save(updated)
    assert store.get("invoice").fields == {"vendor": "Vendor name"}
    assert result.updated_at >= result.created_at


# ---------------------------------------------------------------------------
# list_all
# ---------------------------------------------------------------------------

def test_list_all_empty(store):
    assert store.list_all() == []


def test_list_all_sorted_by_name(store):
    store.save(SchemaEntry(name="zzz", fields={}))
    store.save(SchemaEntry(name="aaa", fields={}))
    store.save(SchemaEntry(name="mmm", fields={}))
    names = [e.name for e in store.list_all()]
    assert names == ["aaa", "mmm", "zzz"]


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

def test_delete_existing(store, invoice_entry):
    store.save(invoice_entry)
    assert store.delete("invoice") is True
    assert store.get("invoice") is None


def test_delete_nonexistent_returns_false(store):
    assert store.delete("ghost") is False


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------

def test_base_store_is_abstract():
    with pytest.raises(TypeError):
        BaseSchemaStore()  # type: ignore[abstract]
