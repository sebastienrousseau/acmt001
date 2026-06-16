#!/usr/bin/env python3
"""Example: Account-management compliance, validation, and XML generation.

Usage:
    python examples/account_management.py

Demonstrates how to:
  1. Cleanse account-management data containing non-SWIFT characters and
     oversized fields before generating XML.
  2. Validate account identifiers (IBAN), servicer BICs, and owner LEIs.
  3. Generate an acmt.007 Account Opening Request and an acmt.019 Account
     Closing Request from the cleansed record.
"""

from pathlib import Path

from acmt001 import generate_xml_string
from acmt001.compliance import cleanse_data, cleanse_data_with_report
from acmt001.validation import (
    validate_bic_safe,
    validate_iban_safe,
    validate_lei_safe,
)

# Raw account-management data with SWIFT compliance issues.
raw_data = [
    {
        "msg_id": "X" * 50,  # Too long (max 35)
        "creation_date_time": "2026-01-15T10:30:00",
        "process_id": "ACMT-PRC-0001",
        "account_id": "GB29NWBK60161331926819",
        "account_id_other": "VRTL-0001-0001",
        "account_currency": "EUR",
        "account_name": "Müller & Söhne™ Treasury",  # Non-SWIFT chars
        "account_type_cd": "CACC",
        "account_servicer_bic": "NWBKGB2LXXX",
        "account_owner_name": "García Café SL",  # Accented chars
        "account_owner_country": "GB",
        "account_owner_lei": "5493001KJTIIGC8Y1R12",
        "org_full_legal_name": "García Café Sociedad Limitada™",
        "org_country_of_operation": "GB",
        "org_address_country": "GB",
        "org_address_town": "London",
        "org_id_lei": "5493001KJTIIGC8Y1R12",
        "org_id_other": "ACME-ORG-001",
    }
]

# ---------------------------------------------------------------------------
# 1. SWIFT compliance cleansing
# ---------------------------------------------------------------------------
clean = cleanse_data(raw_data)
print("=== Simple Cleanse ===")
print(f"  account_name: {raw_data[0]['account_name']!r}")
print(f"            -> {clean[0]['account_name']!r}")
print(
    f"  msg_id length: {len(raw_data[0]['msg_id'])} "
    f"-> {len(clean[0]['msg_id'])}"
)
print()

clean, report = cleanse_data_with_report(raw_data)
print("=== Cleanse with Report ===")
print(f"  {report.summary()}")
print(f"  Violations: {report.violation_count}")
print(f"  Rows modified: {report.rows_modified}/{report.rows_processed}")
for v in report.violations:
    print(f"    - {v.field}: {v.violation_type} — {v.message}")
print()

# ---------------------------------------------------------------------------
# 2. Identifier validation (IBAN / BIC / LEI)
# ---------------------------------------------------------------------------
record = clean[0]
print("=== Identifier Validation ===")
print(
    f"  account_id (IBAN):     {record['account_id']} -> "
    f"{validate_iban_safe(record['account_id'])}"
)
print(
    f"  account_servicer_bic:  {record['account_servicer_bic']} -> "
    f"{validate_bic_safe(record['account_servicer_bic'])}"
)
print(
    f"  account_owner_lei:     {record['account_owner_lei']} -> "
    f"{validate_lei_safe(record['account_owner_lei'])}"
)
print()

# ---------------------------------------------------------------------------
# 3. Generate acmt.007 (opening) and acmt.019 (closing) messages
# ---------------------------------------------------------------------------
templates_dir = (
    Path(__file__).resolve().parent.parent / "acmt001" / "templates"
)


def _generate(message_type: str) -> str:
    base = templates_dir / message_type
    return generate_xml_string(
        clean,
        message_type,
        str(base / "template.xml"),
        str(base / f"{message_type}.xsd"),
    )


print("=== XML Generation ===")
opening_type = "acmt.007.001.05"
closing_type = "acmt.019.001.04"
opening_xml = _generate(opening_type)
closing_xml = _generate(closing_type)
print(f"  {opening_type} (Account Opening Request): {len(opening_xml)} bytes")
print(f"  {closing_type} (Account Closing Request): {len(closing_xml)} bytes")
