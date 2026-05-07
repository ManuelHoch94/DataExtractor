from __future__ import annotations

import anthropic

from data_extractor.core.exceptions import ProcessorError
from data_extractor.llm.base import BaseLLMClient, LLMResponse


class AnthropicClient(BaseLLMClient):
    """LLM client backed by the Anthropic Messages API."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-6",
    ) -> None:
        self._model = model
        self._client = anthropic.Anthropic(api_key=api_key)

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except anthropic.APIError as exc:
            raise ProcessorError(f"Anthropic API call failed: {exc}") from exc

        text = response.content[0].text if response.content else ""
        usage = response.usage
        return LLMResponse(
            text=text,
            input_tokens=usage.input_tokens if usage else 0,
            output_tokens=usage.output_tokens if usage else 0,
        )
