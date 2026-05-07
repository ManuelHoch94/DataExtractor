"""Shared pytest fixtures."""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pypdf
import pytest

from data_extractor.core.models import ExtractionRequest, ExtractedField


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_minimal_pdf(text: str = "Hello World") -> bytes:
    """Return an in-memory PDF containing *text* on one page."""
    writer = pypdf.PdfWriter()
    page = writer.add_blank_page(width=595, height=842)
    # pypdf blank pages have no content stream – we embed a simple one
    from pypdf.generic import DecodedStreamObject, NameObject
    content = f"BT /F1 12 Tf 50 750 Td ({text}) Tj ET".encode()
    stream = DecodedStreamObject()
    stream.set_data(content)
    page[NameObject("/Contents")] = writer._add_object(stream)  # noqa: SLF001
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_pdf(tmp_path: Path) -> Path:
    """A real on-disk PDF file with simple text content."""
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(make_minimal_pdf("Invoice Number: INV-2024-001"))
    return pdf_path


@pytest.fixture()
def empty_pdf(tmp_path: Path) -> Path:
    """A real on-disk PDF with an empty page."""
    pdf_path = tmp_path / "empty.pdf"
    pdf_path.write_bytes(make_minimal_pdf(""))
    return pdf_path


@pytest.fixture()
def sample_schema() -> dict[str, str]:
    return {
        "invoice_number": "The unique invoice identifier",
        "amount": "Total amount due including taxes",
    }


@pytest.fixture()
def sample_fields() -> list[ExtractedField]:
    return [
        ExtractedField(
            name="invoice_number",
            value="INV-2024-001",
            confidence=0.95,
            source_text="Invoice Number: INV-2024-001",
            page_number=1,
        ),
        ExtractedField(
            name="amount",
            value=None,
            confidence=0.0,
            source_text=None,
            page_number=None,
        ),
    ]


@pytest.fixture()
def mock_anthropic_client(sample_fields: list[ExtractedField]) -> MagicMock:
    """Anthropic client whose messages.create returns a valid JSON field list."""
    import json

    client = MagicMock()
    response = MagicMock()
    response.content = [
        MagicMock(
            text=json.dumps([f.model_dump() for f in sample_fields])
        )
    ]
    client.messages.create.return_value = response
    return client


@pytest.fixture()
def mock_settings(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch get_settings() so tests never need a real API key."""
    settings = MagicMock()
    settings.anthropic_api_key.get_secret_value.return_value = "sk-test-key"
    settings.anthropic_model = "claude-sonnet-4-6"
    settings.extraction_max_tokens = 512
    settings.extraction_confidence_threshold = 0.0
    with patch("data_extractor.config.settings.get_settings", return_value=settings):
        yield settings
