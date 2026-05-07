from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from data_extractor.config.settings import Settings, get_settings
from data_extractor.core.orchestrator import Orchestrator


@lru_cache(maxsize=1)
def get_orchestrator(settings: Settings = Depends(get_settings)) -> Orchestrator:
    """Singleton Orchestrator wired from application settings.

    FastAPI calls this once and caches it for the application lifetime.
    Override in tests by replacing the dependency in the app.
    """
    return Orchestrator.from_settings(settings)


SettingsDep = Annotated[Settings, Depends(get_settings)]
OrchestratorDep = Annotated[Orchestrator, Depends(get_orchestrator)]
