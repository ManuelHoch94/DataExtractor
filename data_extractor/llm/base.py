from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMResponse:
    """Normalised response from any LLM backend."""

    text: str
    input_tokens: int = 0
    output_tokens: int = 0


class BaseLLMClient(ABC):
    """Provider-agnostic interface for text completion.

    Implement this class to plug in any LLM backend (OpenAI, Anthropic,
    a self-hosted model, etc.) without touching the extraction logic.
    """

    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Send a completion request and return a normalised response.

        Args:
            system_prompt: Instructions that shape the model's behaviour.
            user_prompt:   The user-facing input (document text + schema).
            max_tokens:    Upper bound on generated tokens.

        Returns:
            :class:`LLMResponse` with the generated text and token counts.
        """
