from __future__ import annotations

from abc import ABC, abstractmethod


class BaseProcessor(ABC):
    """Abstract contract for all text processors."""

    @abstractmethod
    def process(self, text: str) -> str:
        """Transform *text* and return the processed result."""
