from __future__ import annotations

import json
import logging
from typing import Any

import anthropic

from data_extractor.core.exceptions import ProcessorError
from data_extractor.core.models import ExtractedField

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a structured-data extraction assistant.
Given a document text and a schema of field names with descriptions, extract the
requested fields from the text.

Rules:
- Return ONLY valid JSON – no markdown fences, no commentary.
- Output an array of objects, one per requested field, with these keys:
    "name"        : field name exactly as provided
    "value"       : extracted string value, or null if not found
    "confidence"  : float 0.0–1.0 reflecting certainty
    "source_text" : the verbatim snippet from the document that supports the value
    "page_number" : integer page number (1-based) if determinable, else null
- If a field cannot be found, set value=null and confidence=0.0.
- Never invent data that is not present in the document.
"""

_USER_TEMPLATE = """\
## Schema
{schema_json}

## Document text
{document_text}
"""


class IndexMapper:
    """Maps document text to structured field indexes using the Claude API.

    This component sends the cleaned document text together with a
    user-defined schema to Claude and parses the structured JSON response
    into :class:`~data_extractor.core.models.ExtractedField` objects.
    """

    def __init__(
        self,
        client: anthropic.Anthropic,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 2048,
    ) -> None:
        self._client = client
        self._model = model
        self._max_tokens = max_tokens

    def map(
        self,
        text: str,
        schema_definition: dict[str, Any],
        confidence_threshold: float = 0.0,
    ) -> list[ExtractedField]:
        """Call Claude to extract *schema_definition* fields from *text*.

        Args:
            text: Cleaned document text.
            schema_definition: ``{field_name: description}`` mapping.
            confidence_threshold: Fields below this score are excluded.

        Returns:
            List of :class:`ExtractedField` instances above the threshold.
        """
        if not schema_definition:
            return []

        user_message = _USER_TEMPLATE.format(
            schema_json=json.dumps(schema_definition, ensure_ascii=False, indent=2),
            document_text=text,
        )

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
        except anthropic.APIError as exc:
            raise ProcessorError(f"Anthropic API call failed: {exc}") from exc

        raw_content = response.content[0].text if response.content else ""

        try:
            raw_fields: list[dict[str, Any]] = json.loads(raw_content)
        except json.JSONDecodeError as exc:
            raise ProcessorError(
                f"Claude returned non-JSON output: {raw_content!r}"
            ) from exc

        if not isinstance(raw_fields, list):
            raise ProcessorError(
                f"Expected JSON array from Claude, got {type(raw_fields).__name__}"
            )

        results: list[ExtractedField] = []
        for item in raw_fields:
            try:
                field = ExtractedField(**item)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping malformed field entry %r: %s", item, exc)
                continue

            if field.confidence >= confidence_threshold:
                results.append(field)

        return results
