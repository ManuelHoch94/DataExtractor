"""Tests for the LLM abstraction layer."""

from unittest.mock import MagicMock

import pytest

from data_extractor.llm.base import BaseLLMClient, LLMResponse


class ConcreteClient(BaseLLMClient):
    """Minimal concrete implementation used only in tests."""

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 2048) -> LLMResponse:
        return LLMResponse(text="ok", input_tokens=1, output_tokens=1)


def test_llm_response_is_immutable():
    r = LLMResponse(text="hello", input_tokens=10, output_tokens=5)
    with pytest.raises(Exception):
        r.text = "changed"  # type: ignore[misc]


def test_llm_response_defaults():
    r = LLMResponse(text="hello")
    assert r.input_tokens == 0
    assert r.output_tokens == 0


def test_concrete_client_satisfies_interface():
    client = ConcreteClient()
    result = client.complete("sys", "usr")
    assert isinstance(result, LLMResponse)
    assert result.text == "ok"


def test_base_client_is_abstract():
    with pytest.raises(TypeError):
        BaseLLMClient()  # type: ignore[abstract]
