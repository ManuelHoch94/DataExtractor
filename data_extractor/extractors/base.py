from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from data_extractor.core.models import ExtractedField


class BaseExtractor(ABC):
    """Abstract contract for all field extractors."""

    @abstractmethod
    def extract(
        self,
        text: str,
        schema_definition: dict[str, Any],
    ) -> list[ExtractedField]:
        """Extract fields from *text* according to *schema_definition*."""
