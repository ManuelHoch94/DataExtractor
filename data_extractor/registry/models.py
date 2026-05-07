from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class SchemaEntry(BaseModel):
    """A named extraction schema stored in the registry."""

    name: str = Field(description="Unique identifier used to reference the schema.")
    description: str = Field(default="", description="Human-readable purpose of the schema.")
    fields: dict[str, str] = Field(
        description="Mapping of field names to extraction hints.",
        examples=[{"invoice_number": "The unique invoice ID", "amount": "Total amount due"}],
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
