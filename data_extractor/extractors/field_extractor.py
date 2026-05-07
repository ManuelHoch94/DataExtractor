from __future__ import annotations

from typing import Any

from data_extractor.core.models import ExtractedField
from data_extractor.extractors.base import BaseExtractor
from data_extractor.processors.index_mapper import IndexMapper


class FieldExtractor(BaseExtractor):
    """Delegates field extraction to :class:`~data_extractor.processors.IndexMapper`.

    This is the primary extractor used by the :class:`Orchestrator`.  It
    acts as a thin adapter between the extractor interface and the AI-powered
    :class:`IndexMapper`, allowing the two concerns to be swapped or extended
    independently.
    """

    def __init__(
        self,
        index_mapper: IndexMapper,
        confidence_threshold: float = 0.0,
    ) -> None:
        self._mapper = index_mapper
        self._confidence_threshold = confidence_threshold

    def extract(
        self,
        text: str,
        schema_definition: dict[str, Any],
    ) -> list[ExtractedField]:
        return self._mapper.map(
            text=text,
            schema_definition=schema_definition,
            confidence_threshold=self._confidence_threshold,
        )
