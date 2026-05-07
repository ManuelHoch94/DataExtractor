from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Anthropic
    anthropic_api_key: SecretStr = Field(
        description="Anthropic API key for AI-powered extraction."
    )
    anthropic_model: str = Field(
        default="claude-sonnet-4-6",
        description="Claude model used for index mapping.",
    )

    # Extraction behaviour
    extraction_confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence to include a field in results.",
    )
    extraction_max_tokens: int = Field(
        default=2048,
        ge=1,
        description="Max tokens for Claude responses.",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
