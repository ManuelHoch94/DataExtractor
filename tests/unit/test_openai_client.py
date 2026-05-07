"""Tests for the OpenAI LLM client adapter."""

from unittest.mock import MagicMock, patch

import openai
import pytest

from data_extractor.core.exceptions import ProcessorError
from data_extractor.llm.base import LLMResponse
from data_extractor.llm.openai_client import OpenAIClient


def _make_response(content: str, prompt_tokens: int = 10, completion_tokens: int = 5):
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content
    response.usage = MagicMock()
    response.usage.prompt_tokens = prompt_tokens
    response.usage.completion_tokens = completion_tokens
    return response


@patch("data_extractor.llm.openai_client.openai.OpenAI")
def test_complete_returns_llm_response(mock_openai_cls):
    mock_openai_cls.return_value.chat.completions.create.return_value = _make_response("hello")
    client = OpenAIClient(api_key="sk-test", model="gpt-4o")
    result = client.complete("system", "user")
    assert isinstance(result, LLMResponse)
    assert result.text == "hello"
    assert result.input_tokens == 10
    assert result.output_tokens == 5


@patch("data_extractor.llm.openai_client.openai.OpenAI")
def test_complete_passes_max_tokens(mock_openai_cls):
    mock_create = mock_openai_cls.return_value.chat.completions.create
    mock_create.return_value = _make_response("ok")
    client = OpenAIClient(api_key="sk-test")
    client.complete("sys", "usr", max_tokens=512)
    _, kwargs = mock_create.call_args
    assert kwargs["max_tokens"] == 512


@patch("data_extractor.llm.openai_client.openai.OpenAI")
def test_complete_passes_custom_base_url(mock_openai_cls):
    OpenAIClient(api_key="sk-test", base_url="http://localhost:8000/v1")
    _, kwargs = mock_openai_cls.call_args
    assert kwargs["base_url"] == "http://localhost:8000/v1"


@patch("data_extractor.llm.openai_client.openai.OpenAI")
def test_complete_no_base_url_by_default(mock_openai_cls):
    OpenAIClient(api_key="sk-test")
    _, kwargs = mock_openai_cls.call_args
    assert "base_url" not in kwargs


@patch("data_extractor.llm.openai_client.openai.OpenAI")
def test_complete_raises_processor_error_on_api_failure(mock_openai_cls):
    mock_openai_cls.return_value.chat.completions.create.side_effect = (
        openai.APIConnectionError(request=MagicMock())
    )
    client = OpenAIClient(api_key="sk-test")
    with pytest.raises(ProcessorError, match="OpenAI API call failed"):
        client.complete("sys", "usr")


@patch("data_extractor.llm.openai_client.openai.OpenAI")
def test_complete_handles_none_content(mock_openai_cls):
    mock_openai_cls.return_value.chat.completions.create.return_value = _make_response(None)
    client = OpenAIClient(api_key="sk-test")
    result = client.complete("sys", "usr")
    assert result.text == ""


@patch("data_extractor.llm.openai_client.openai.OpenAI")
def test_complete_handles_none_usage(mock_openai_cls):
    response = _make_response("text")
    response.usage = None
    mock_openai_cls.return_value.chat.completions.create.return_value = response
    client = OpenAIClient(api_key="sk-test")
    result = client.complete("sys", "usr")
    assert result.input_tokens == 0
    assert result.output_tokens == 0
