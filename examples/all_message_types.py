#!/usr/bin/env python3
"""Example: generate every supported acmt message type.

Usage:
    python examples/all_message_types.py

A single flat record drives all 34 message types — message-intrinsic coded
values (switch status/type, response codes, …) are supplied per message type
automatically. Each output is validated against its real ISO 20022 XSD.
"""

import json
from pathlib import Path

from acmt001 import services
from acmt001.constants import valid_xml_types

record = json.loads(
    (
        Path(__file__).resolve().parent.parent
        / "tests"
        / "gold_master"
        / "account_opening_full.json"
    ).read_text()
)

names = {m["message_type"]: m["name"] for m in services.list_message_types()}

ok = 0
for message_type in valid_xml_types:
    xml = services.generate(
        message_type, record
    )  # XSD-validated on the way out
    assert xml.startswith("<?xml")
    ok += 1
    print(f"  ✓ {message_type}  {names[message_type]}  ({len(xml)} bytes)")

print(f"\nGenerated and validated {ok}/{len(valid_xml_types)} message types.")
