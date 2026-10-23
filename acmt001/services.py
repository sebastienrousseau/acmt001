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
from typing import Any

# acmt001-mcp 0.0.11 reads the identifier kinds from
# services._IDENTIFIER_VALIDATORS at import time, so the name stays here.
from acmt001._service_ops import (
    _IDENTIFIER_VALIDATORS as _IDENTIFIER_VALIDATORS,
)
from acmt001._service_ops import (
    generate,
    get_input_schema,
    get_required_fields,
    list_message_types,
    validate_identifier,
    validate_records,
)

__all__ = [
    "list_message_types",
    "get_input_schema",
    "get_required_fields",
    "generate",
    "validate_records",
    "validate_identifier",
]


def load_openapi(app: Any | None = None) -> str:
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
