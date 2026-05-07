from __future__ import annotations

import openai

from data_extractor.core.exceptions import ProcessorError
from data_extractor.llm.base import BaseLLMClient, LLMResponse


class OpenAIClient(BaseLLMClient):
    """LLM client backed by the OpenAI Chat Completions API.

    Compatible with any OpenAI-API-compatible endpoint (e.g. Azure OpenAI,
    local vLLM, LM Studio) by setting a custom *base_url*.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: str | None = None,
    ) -> None:
        self._model = model
        self._client = openai.OpenAI(
            api_key=api_key,
            **({"base_url": base_url} if base_url else {}),
        )

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except openai.OpenAIError as exc:
            raise ProcessorError(f"OpenAI API call failed: {exc}") from exc

        text = response.choices[0].message.content or ""
        usage = response.usage
        return LLMResponse(
            text=text,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )
