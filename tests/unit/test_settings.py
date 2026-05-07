import pytest
from pydantic import ValidationError

from data_extractor.config.settings import Settings


def test_settings_require_api_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises((ValidationError, Exception)):
        Settings()


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123")
    s = Settings()
    assert s.anthropic_api_key.get_secret_value() == "sk-test-123"
    assert s.anthropic_model == "claude-sonnet-4-6"
    assert 0.0 <= s.extraction_confidence_threshold <= 1.0


def test_settings_custom_model(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-x")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-opus-4-7")
    s = Settings()
    assert s.anthropic_model == "claude-opus-4-7"


def test_settings_invalid_log_level(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-x")
    monkeypatch.setenv("LOG_LEVEL", "VERBOSE")
    with pytest.raises(ValidationError):
        Settings()


def test_settings_confidence_out_of_range(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-x")
    monkeypatch.setenv("EXTRACTION_CONFIDENCE_THRESHOLD", "2.0")
    with pytest.raises(ValidationError):
        Settings()
