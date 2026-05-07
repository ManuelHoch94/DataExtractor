from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

import data_extractor


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = Field(default_factory=lambda: data_extractor.__version__)
    llm_provider: str


class ExtractionFieldSchema(BaseModel):
    """Single extracted field as returned by the API."""

    name: str
    value: str | None
    confidence: float = Field(ge=0.0, le=1.0)
    source_text: str | None = None
    page_number: int | None = None


class ExtractionResponse(BaseModel):
    """Full extraction result returned by POST /api/v1/extract."""

    filename: str
    page_count: int
    fields: list[ExtractionFieldSchema]
    index: dict[str, str | None] = Field(
        description="Flat {field_name: value} dict ready for index ingestion."
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standardised error envelope."""

    detail: str
    code: str = "error"
