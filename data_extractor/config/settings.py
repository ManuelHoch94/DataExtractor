from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProvider = Literal["openai", "anthropic"]


class Settings(BaseSettings):
    """Application-wide settings loaded from environment / .env file.

    Set ``LLM_PROVIDER=openai`` (default) or ``LLM_PROVIDER=anthropic``
    to switch the active LLM backend.  Only the corresponding API key
    is required; the other may be omitted.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Provider selector
    llm_provider: LLMProvider = Field(
        default="openai",
        description="Which LLM backend to use: 'openai' or 'anthropic'.",
    )

    # OpenAI
    openai_api_key: SecretStr | None = Field(
        default=None,
        description="OpenAI API key (required when llm_provider='openai').",
    )
    openai_model: str = Field(default="gpt-4o")
    openai_base_url: str | None = Field(
        default=None,
        description="Custom base URL for OpenAI-compatible endpoints (Azure, vLLM, …).",
    )

    # Anthropic
    anthropic_api_key: SecretStr | None = Field(
        default=None,
        description="Anthropic API key (required when llm_provider='anthropic').",
    )
    anthropic_model: str = Field(default="claude-sonnet-4-6")

    # Shared extraction behaviour
    extraction_confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    extraction_max_tokens: int = Field(default=2048, ge=1)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @model_validator(mode="after")
    def _require_active_provider_key(self) -> "Settings":
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError(
                "openai_api_key is required when llm_provider='openai'."
            )
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError(
                "anthropic_api_key is required when llm_provider='anthropic'."
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
