"""Tests for the Anthropic LLM client adapter."""

from unittest.mock import MagicMock, patch

import anthropic
import pytest

from data_extractor.core.exceptions import ProcessorError
from data_extractor.llm.anthropic_client import AnthropicClient
from data_extractor.llm.base import LLMResponse


def _make_response(text: str, input_tokens: int = 10, output_tokens: int = 5):
    response = MagicMock()
    response.content = [MagicMock(text=text)]
    response.usage = MagicMock()
    response.usage.input_tokens = input_tokens
    response.usage.output_tokens = output_tokens
    return response


@patch("data_extractor.llm.anthropic_client.anthropic.Anthropic")
def test_complete_returns_llm_response(mock_cls):
    mock_cls.return_value.messages.create.return_value = _make_response("result")
    client = AnthropicClient(api_key="sk-test")
    result = client.complete("system", "user")
    assert isinstance(result, LLMResponse)
    assert result.text == "result"
    assert result.input_tokens == 10
    assert result.output_tokens == 5


@patch("data_extractor.llm.anthropic_client.anthropic.Anthropic")
def test_complete_raises_processor_error_on_api_failure(mock_cls):
    mock_cls.return_value.messages.create.side_effect = (
        anthropic.APIConnectionError(request=MagicMock())
    )
    client = AnthropicClient(api_key="sk-test")
    with pytest.raises(ProcessorError, match="Anthropic API call failed"):
        client.complete("sys", "usr")


@patch("data_extractor.llm.anthropic_client.anthropic.Anthropic")
def test_complete_empty_content_returns_empty_string(mock_cls):
    response = MagicMock()
    response.content = []
    response.usage = None
    mock_cls.return_value.messages.create.return_value = response
    client = AnthropicClient(api_key="sk-test")
    result = client.complete("sys", "usr")
    assert result.text == ""
    assert result.input_tokens == 0
    assert result.output_tokens == 0
