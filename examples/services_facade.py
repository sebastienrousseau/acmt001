#!/usr/bin/env python3
"""Example: the unified service facade (acmt001.services).

Usage:
    python examples/services_facade.py

`acmt001.services` is the single backend shared by the CLI, REST API, MCP
server, and LSP server. Every function returns plain data (dicts/lists/str),
so it is the easiest way to drive the library programmatically.
"""

import json
from pathlib import Path

from acmt001 import services

# A complete account record (the bundled gold-master example).
record = json.loads(
    (
        Path(__file__).resolve().parent.parent
        / "tests"
        / "gold_master"
        / "account_opening_full.json"
    ).read_text()
)

# 1. Discover what the library can produce.
types = services.list_message_types()
print(f"Supported message types: {len(types)}")
print(f"  first: {types[0]['message_type']} — {types[0]['name']}")

# 2. Inspect the input contract for a message type.
required = services.get_required_fields("acmt.007.001.05")
print(
    f"Required fields for acmt.007.001.05: {len(required)} -> {required[:3]}…"
)

schema = services.get_input_schema("acmt.007.001.05")
print(f"Input JSON Schema title: {schema['title']}")

# 3. Validate records before generating.
report = services.validate_records("acmt.007.001.05", record)
print(
    f"Validation: valid={report['valid']} ({report['valid_count']}/{report['total']})"
)

# 4. Validate a financial identifier.
print("BIC check:", services.validate_identifier("bic", "NWBKGB2LXXX"))

# 5. Generate a validated ISO 20022 message (no file paths needed — the
#    packaged template + XSD are used and the output is XSD-validated).
xml = services.generate("acmt.007.001.05", record)
print(f"Generated acmt.007.001.05: {len(xml)} bytes, starts with {xml[:38]!r}")
