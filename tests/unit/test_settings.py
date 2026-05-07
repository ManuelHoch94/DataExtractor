import pytest
from pydantic import ValidationError

from data_extractor.config.settings import Settings


def _base_env(monkeypatch: pytest.MonkeyPatch, **extra: str) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    for k, v in extra.items():
        monkeypatch.setenv(k, v)


# ---------------------------------------------------------------------------
# Provider: openai (default)
# ---------------------------------------------------------------------------

def test_openai_provider_requires_api_key():
    # Test the model_validator logic directly, bypassing env/file loading
    instance = Settings.model_construct(
        llm_provider="openai",
        openai_api_key=None,
        anthropic_api_key=None,
        openai_model="gpt-4o",
        openai_base_url=None,
        anthropic_model="claude-sonnet-4-6",
        extraction_confidence_threshold=0.5,
        extraction_max_tokens=2048,
        log_level="INFO",
    )
    with pytest.raises(ValueError, match="openai_api_key is required"):
        instance._require_active_provider_key()


def test_openai_provider_valid(monkeypatch: pytest.MonkeyPatch):
    _base_env(monkeypatch, OPENAI_API_KEY="sk-test")
    s = Settings()
    assert s.llm_provider == "openai"
    assert s.openai_api_key.get_secret_value() == "sk-test"


def test_openai_custom_model(monkeypatch: pytest.MonkeyPatch):
    _base_env(monkeypatch, OPENAI_API_KEY="sk-x", OPENAI_MODEL="gpt-4o-mini")
    s = Settings()
    assert s.openai_model == "gpt-4o-mini"


def test_openai_custom_base_url(monkeypatch: pytest.MonkeyPatch):
    _base_env(monkeypatch, OPENAI_API_KEY="sk-x", OPENAI_BASE_URL="http://localhost:8000/v1")
    s = Settings()
    assert s.openai_base_url == "http://localhost:8000/v1"


# ---------------------------------------------------------------------------
# Provider: anthropic
# ---------------------------------------------------------------------------

def test_anthropic_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch):
    _base_env(monkeypatch, LLM_PROVIDER="anthropic")
    with pytest.raises((ValidationError, ValueError)):
        Settings()


def test_anthropic_provider_valid(monkeypatch: pytest.MonkeyPatch):
    _base_env(monkeypatch, LLM_PROVIDER="anthropic", ANTHROPIC_API_KEY="sk-ant-test")
    s = Settings()
    assert s.llm_provider == "anthropic"
    assert s.anthropic_api_key.get_secret_value() == "sk-ant-test"


def test_anthropic_custom_model(monkeypatch: pytest.MonkeyPatch):
    _base_env(monkeypatch, LLM_PROVIDER="anthropic", ANTHROPIC_API_KEY="sk-x", ANTHROPIC_MODEL="claude-opus-4-7")
    s = Settings()
    assert s.anthropic_model == "claude-opus-4-7"


# ---------------------------------------------------------------------------
# Shared settings
# ---------------------------------------------------------------------------

def test_invalid_provider(monkeypatch: pytest.MonkeyPatch):
    _base_env(monkeypatch, LLM_PROVIDER="gemini", OPENAI_API_KEY="sk-x")
    with pytest.raises(ValidationError):
        Settings()


def test_confidence_threshold_defaults(monkeypatch: pytest.MonkeyPatch):
    _base_env(monkeypatch, OPENAI_API_KEY="sk-x")
    s = Settings()
    assert 0.0 <= s.extraction_confidence_threshold <= 1.0


def test_confidence_out_of_range(monkeypatch: pytest.MonkeyPatch):
    _base_env(monkeypatch, OPENAI_API_KEY="sk-x", EXTRACTION_CONFIDENCE_THRESHOLD="2.0")
    with pytest.raises(ValidationError):
        Settings()


def test_invalid_log_level(monkeypatch: pytest.MonkeyPatch):
    _base_env(monkeypatch, OPENAI_API_KEY="sk-x", LOG_LEVEL="VERBOSE")
    with pytest.raises(ValidationError):
        Settings()
