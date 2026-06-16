#!/usr/bin/env python3
"""Example: Generate an acmt XML file from Python data.

Usage:
    python examples/generate_xml.py

This creates an acmt.007.001.05 (Account Opening Request) XML message from
a single account-management record.
"""

import json
from pathlib import Path

from acmt001 import generate_xml_string

# Account-management data — one dict per account opening request.
# Loaded from the bundled examples/accounts.json data file.
accounts_file = Path(__file__).resolve().parent / "accounts.json"
data = json.loads(accounts_file.read_text(encoding="utf-8"))

# Paths to template and XSD.
message_type = "acmt.007.001.05"
base = (
    Path(__file__).resolve().parent.parent
    / "acmt001"
    / "templates"
    / message_type
)
template = str(base / "template.xml")
xsd = str(base / f"{message_type}.xsd")

# Generate XML.
xml = generate_xml_string(data, message_type, template, xsd)

# Write to file.
output = Path("output_acmt001.xml")
output.write_text(xml, encoding="utf-8")
print(f"Generated: {output.resolve()}")
print(f"Message type: {message_type}")
print(f"Size: {len(xml)} bytes")
