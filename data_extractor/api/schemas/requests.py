from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractionRequestSchema(BaseModel):
    """JSON body that accompanies the uploaded PDF file.

    Sent as a form field named ``request`` alongside the ``file`` upload.
    """

    schema_definition: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Mapping of field names to extraction hints. "
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
