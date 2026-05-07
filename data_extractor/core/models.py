from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ExtractionRequest(BaseModel):
    """Input for a single extraction job."""

    file_path: Path
    schema_definition: dict[str, Any] = Field(
        default_factory=dict,
        description="Mapping of field names to their descriptions / extraction hints.",
    )
    max_pages: int | None = Field(default=None, ge=1)

    @field_validator("file_path")
    @classmethod
    def file_must_exist(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"File does not exist: {v}")
        if not v.is_file():
            raise ValueError(f"Path is not a file: {v}")
        return v


class ExtractedField(BaseModel):
    """A single extracted field with its value and confidence score."""

    name: str
    value: str | None
    confidence: float = Field(ge=0.0, le=1.0)
    source_text: str | None = None
    page_number: int | None = None


class ExtractionResult(BaseModel):
    """Complete result of one extraction run."""

    request: ExtractionRequest
    fields: list[ExtractedField] = Field(default_factory=list)
    raw_text: str = ""
    page_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_index_dict(self) -> dict[str, str | None]:
        """Return {field_name: value} mapping for downstream index ingestion."""
        return {f.name: f.value for f in self.fields}
