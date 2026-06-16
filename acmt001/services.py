# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""High-level service facade for Acmt001.

A small, dependency-light layer that exposes the library's core capabilities as
plain functions returning plain data. It is the single shared backend for the
CLI, the REST API, the Model Context Protocol (MCP) server, and the Language
Server Protocol (LSP) server, so every interface behaves identically.

Example:
    >>> from acmt001 import services
    >>> [m["message_type"] for m in services.list_message_types()][:1]
    ['acmt.001.001.08']
    >>> services.validate_identifier("bic", "NWBKGB2LXXX")["valid"]
    True
"""

import json
from typing import Any, Optional

from acmt001.constants import message_names, valid_xml_types
from acmt001.validation.bic_validator import validate_bic_safe
from acmt001.validation.iban_validator import validate_iban_safe
from acmt001.validation.lei_validator import validate_lei_safe
from acmt001.validation.schema_validator import SchemaValidator
from acmt001.xml.generate_xml import generate_message

__all__ = [
    "list_message_types",
    "get_input_schema",
    "get_required_fields",
    "generate",
    "validate_records",
    "validate_identifier",
]

_IDENTIFIER_VALIDATORS = {
    "iban": validate_iban_safe,
    "bic": validate_bic_safe,
    "lei": validate_lei_safe,
}


def list_message_types() -> list[dict[str, str]]:
    """Return every supported message type with its human-readable name.

    Returns:
        A list of ``{"message_type": ..., "name": ...}`` dictionaries.
    """
    return [
        {"message_type": mt, "name": message_names[mt]}
        for mt in valid_xml_types
    ]


def get_input_schema(message_type: str) -> dict[str, Any]:
    """Return the JSON Schema describing the flat input record for a type.

    Args:
        message_type: A supported ISO 20022 acmt message type.

    Returns:
        The parsed JSON Schema document.

    Raises:
        ValueError: If the message type is not supported.
    """
    validator = SchemaValidator(message_type)
    return dict(validator.schema)


def get_required_fields(message_type: str) -> list[str]:
    """Return the required input field names for a message type.

    Args:
        message_type: A supported ISO 20022 acmt message type.

    Returns:
        The list of required field names.

    Raises:
        ValueError: If the message type is not supported.
    """
    return SchemaValidator(message_type).get_required_fields()


def generate(message_type: str, records: list[dict[str, Any]]) -> str:
    """Generate a validated ISO 20022 acmt XML message.

    Uses the template and XSD bundled with the package, so callers only supply
    the message type and the flat records.

    Args:
        message_type: A supported ISO 20022 acmt message type.
        records: One or more flat account records.

    Returns:
        The validated XML document as a string.

    Raises:
        ValueError: If the message type is unsupported or records are empty.
    """
    return generate_message(records, message_type)


def validate_records(
    message_type: str, records: list[dict[str, Any]]
) -> dict[str, Any]:
    """Validate flat records against a message type's input JSON Schema.

    Args:
        message_type: A supported ISO 20022 acmt message type.
        records: One or more flat account records.

    Returns:
        A report dictionary:
        ``{"valid": bool, "total": int, "valid_count": int,
        "errors": [{"row": int, "path": str, "message": str}, ...]}``.

    Raises:
        ValueError: If the message type is not supported.
    """
    validator = SchemaValidator(message_type)
    total, valid_count, row_errors = validator.validate_batch(records)
    errors = [
        {"row": row_idx, "path": err.path, "message": err.message}
        for row_idx, errs in row_errors
        for err in errs
    ]
    return {
        "valid": len(errors) == 0,
        "total": total,
        "valid_count": valid_count,
        "errors": errors,
    }


def validate_identifier(kind: str, value: str) -> dict[str, Any]:
    """Validate a financial identifier (IBAN, BIC, or LEI).

    Args:
        kind: One of ``"iban"``, ``"bic"``, or ``"lei"`` (case-insensitive).
        value: The identifier value to check.

    Returns:
        ``{"kind": str, "value": str, "valid": bool}``.

    Raises:
        ValueError: If ``kind`` is not a supported identifier type.
    """
    key = kind.lower()
    validator = _IDENTIFIER_VALIDATORS.get(key)
    if validator is None:
        supported = ", ".join(sorted(_IDENTIFIER_VALIDATORS))
        raise ValueError(
            f"Unsupported identifier kind: {kind!r}. Expected one of: {supported}."
        )
    return {"kind": key, "value": value, "valid": bool(validator(value))}


def load_openapi(app: Optional[Any] = None) -> str:
    """Return the REST API OpenAPI document as a JSON string.

    Args:
        app: An optional FastAPI app; defaults to the bundled Acmt001 API.

    Returns:
        The OpenAPI schema serialised as JSON.
    """
    if app is None:
        from acmt001.api.app import app as default_app

        app = default_app
    return json.dumps(app.openapi())
