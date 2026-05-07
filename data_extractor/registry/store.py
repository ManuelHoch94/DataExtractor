from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

from data_extractor.registry.models import SchemaEntry


class BaseSchemaStore(ABC):
    """Abstract storage backend for named extraction schemas.

    Implement this interface to swap the in-memory default for a
    persistent store (PostgreSQL, Redis, DynamoDB, …) without touching
    any router or business logic.
    """

    @abstractmethod
    def save(self, entry: SchemaEntry) -> SchemaEntry:
        """Create or overwrite a schema entry. Returns the saved entry."""

    @abstractmethod
    def get(self, name: str) -> SchemaEntry | None:
        """Return the entry for *name*, or ``None`` if not found."""

    @abstractmethod
    def list_all(self) -> list[SchemaEntry]:
        """Return all stored entries ordered by name."""

    @abstractmethod
    def delete(self, name: str) -> bool:
        """Delete the entry for *name*. Returns ``True`` if it existed."""


class InMemorySchemaStore(BaseSchemaStore):
    """Thread-safe in-memory implementation – suitable for single-process deployments.

    Replace with a database-backed implementation for multi-instance or
    persistent use cases.
    """

    def __init__(self) -> None:
        self._store: dict[str, SchemaEntry] = {}

    def save(self, entry: SchemaEntry) -> SchemaEntry:
        existing = self._store.get(entry.name)
        if existing:
            entry = entry.model_copy(
                update={"updated_at": datetime.now(timezone.utc)}
            )
        self._store[entry.name] = entry
        return entry

    def get(self, name: str) -> SchemaEntry | None:
        return self._store.get(name)

    def list_all(self) -> list[SchemaEntry]:
        return sorted(self._store.values(), key=lambda e: e.name)

    def delete(self, name: str) -> bool:
        if name in self._store:
            del self._store[name]
            return True
        return False
