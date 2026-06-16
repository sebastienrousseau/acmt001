#!/usr/bin/env python3
"""Example: ValidationService and SchemaValidator.

Usage:
    python examples/validation_service.py

`ValidationService` runs the full pre-flight pipeline (message type, template,
schema, data source, and data content). `SchemaValidator` validates flat
records against a message type's input JSON Schema.
"""

import json
from pathlib import Path

from acmt001.validation import ValidationConfig, ValidationService
from acmt001.validation.schema_validator import SchemaValidator

ROOT = Path(__file__).resolve().parent.parent
MT = "acmt.007.001.05"
template = ROOT / "acmt001" / "templates" / MT / "template.xml"
xsd = ROOT / "acmt001" / "templates" / MT / f"{MT}.xsd"

# --- ValidationService: validate everything before generating ---------------
service = ValidationService()
report = service.validate_all(
    ValidationConfig(
        xml_message_type=MT,
        xml_template_file_path=str(template),
        xsd_schema_file_path=str(xsd),
        data_file_path=str(ROOT / "examples" / "accounts.csv"),
    )
)
print(f"ValidationService.validate_all -> is_valid={report.is_valid}")
for name, result in report.results.items():
    print(f"  {name:14s}: {'ok' if result.is_valid else result.error}")

# An invalid message type produces a clear, structured failure.
bad = service.validate_message_type("acmt.999.001.99")
print(f"Invalid type -> is_valid={bad.is_valid}, error={bad.error!r}")

# --- SchemaValidator: per-record JSON Schema validation ---------------------
records = json.loads(
    (ROOT / "tests" / "gold_master" / "account_opening_full.json").read_text()
)
validator = SchemaValidator(MT)
total, valid, errors = validator.validate_batch(records)
print(
    f"SchemaValidator.validate_batch -> {valid}/{total} valid, {len(errors)} bad rows"
)
print(f"  required fields: {validator.get_required_fields()[:4]}…")
print(f"  msg_id description: {validator.get_field_description('msg_id')!r}")

# Show how a missing required field is reported.
is_ok, row_errors = validator.validate_row({"msg_id": "ONLY-ID"})
print(f"  incomplete row valid={is_ok}; first error: {row_errors[0]}")
