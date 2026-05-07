from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from data_extractor.config.settings import Settings, get_settings
from data_extractor.core.orchestrator import Orchestrator
from data_extractor.registry.store import BaseSchemaStore, InMemorySchemaStore


@lru_cache(maxsize=1)
def get_orchestrator(settings: Settings = Depends(get_settings)) -> Orchestrator:
    """Singleton Orchestrator wired from application settings."""
    return Orchestrator.from_settings(settings)


@lru_cache(maxsize=1)
def get_schema_store() -> BaseSchemaStore:
    """Singleton schema store.

    Replace the returned implementation to swap to a persistent backend
    without touching any router code.
    """
    return InMemorySchemaStore()


SettingsDep = Annotated[Settings, Depends(get_settings)]
OrchestratorDep = Annotated[Orchestrator, Depends(get_orchestrator)]
SchemaStoreDep = Annotated[BaseSchemaStore, Depends(get_schema_store)]
