"""Parse schema definition files uploaded by the frontend.

Supported formats
-----------------
**Simple** – flat ``{field_name: description}`` dict:

.. code-block:: json

    {
        "invoice_number": "The unique invoice ID",
        "amount":         "Total amount due including taxes"
    }

**Full** – ``SchemaEntry``-compatible object (name/description optional):

.. code-block:: json

    {
        "name": "invoice",
        "description": "Standard invoice schema",
        "fields": {
            "invoice_number": "The unique invoice ID",
            "amount":         "Total amount due including taxes"
        }
    }
"""

from __future__ import annotations

import json

from data_extractor.core.exceptions import ConfigurationError


def parse_schema_file(content: bytes) -> dict[str, str]:
    """Parse uploaded schema JSON bytes into a ``{field: description}`` dict.

    Accepts both the simple flat format and the full SchemaEntry format.

    Raises:
        ConfigurationError: If the content is not valid JSON or the structure
                            is unrecognisable.
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"Schema file is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigurationError(
            "Schema file must be a JSON object, "
            f"got {type(data).__name__}."
        )

    # Full format: {"fields": {"field_name": "description", ...}, ...}
    if "fields" in data:
        fields = data["fields"]
        if not isinstance(fields, dict):
            raise ConfigurationError(
                "'fields' must be a JSON object mapping field names to descriptions."
            )
        return _validate_fields(fields)

    # Simple format: {"field_name": "description", ...}
    return _validate_fields(data)


def _validate_fields(fields: dict) -> dict[str, str]:
    errors: list[str] = []
    for key, value in fields.items():
        if not isinstance(key, str) or not key.strip():
            errors.append(f"Field name must be a non-empty string, got: {key!r}")
        if not isinstance(value, str):
            errors.append(f"Description for '{key}' must be a string, got {type(value).__name__}")
    if errors:
        raise ConfigurationError("Invalid schema fields:\n" + "\n".join(f"  - {e}" for e in errors))
    return {k: v for k, v in fields.items() if k.strip()}
