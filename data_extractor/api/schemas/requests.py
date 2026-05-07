from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class ExtractionRequestSchema(BaseModel):
    """JSON body that accompanies the uploaded PDF file.

    Sent as a form field named ``request`` alongside the ``file`` upload.

    **Schema resolution order:**
    1. ``schema_name`` – reference a schema saved in the registry
    2. ``schema_definition`` – inline field map (takes precedence over registry if both provided)

    At least one of the two must be provided when you want to extract fields.
    """

    schema_name: str | None = Field(
        default=None,
        description="Name of a pre-saved schema from the registry (e.g. 'invoice').",
    )
    schema_definition: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Inline mapping of field names to extraction hints. "
            "Takes precedence over schema_name when both are provided. "
            'Example: {"invoice_number": "The unique invoice ID"}'
        ),
        examples=[{"invoice_number": "The unique invoice ID", "amount": "Total amount due"}],
    )
    max_pages: int | None = Field(
        default=None,
        ge=1,
        description="Limit extraction to the first N pages. Omit to process all pages.",
    )
    confidence_threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "Override the default confidence threshold for this request. "
            "Fields below this score are excluded from the response."
        ),
    )
