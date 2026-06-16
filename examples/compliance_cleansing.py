#!/usr/bin/env python3
"""Example: SWIFT charset compliance and cleansing.

Usage:
    python examples/compliance_cleansing.py

Account data often contains characters or field lengths that downstream
gateways silently reject. The compliance module validates, transliterates,
and length-enforces fields, with a full audit report.
"""

from acmt001.compliance import (
    cleanse_data,
    cleanse_data_with_report,
    cleanse_string,
    enforce_field_lengths,
    validate_swift_charset,
)

# --- validate_swift_charset: list any non-SWIFT characters (empty == safe) ---
print("charset 'Acme Ltd':       ", validate_swift_charset("Acme Ltd") or "OK")
print("charset 'Müller & Söhne™':", validate_swift_charset("Müller & Söhne™"))

# --- cleanse_string: transliterate a single value ---------------------------
print("cleanse_string:           ", repr(cleanse_string("Müller & Söhne™")))

# --- enforce_field_lengths: clamp to ISO 20022 maximums ---------------------
# Returns the clamped row plus a list of the violations it corrected.
clamped, violations = enforce_field_lengths(
    {"msg_id": "X" * 50, "account_name": "Treasury"}
)
print("enforce_field_lengths:    ", {k: len(v) for k, v in clamped.items()})
print(
    "  violations:             ",
    [(v.field, v.violation_type) for v in violations],
)

# --- cleanse_data: cleanse a batch of records -------------------------------
raw = [{"account_owner_name": "Müller & Söhne™", "msg_id": "X" * 50}]
clean = cleanse_data(raw)
print("cleanse_data owner:       ", repr(clean[0]["account_owner_name"]))
print("cleanse_data msg_id len:  ", len(clean[0]["msg_id"]))

# --- cleanse_data_with_report: cleanse + audit trail ------------------------
cleaned, report = cleanse_data_with_report(raw)
print("compliance report summary:")
print("  ", report.summary().replace("\n", "\n   "))
