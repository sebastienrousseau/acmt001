"""XML generator for ISO 20022 acmt Account Management messages."""

import os
from typing import Any

from jinja2 import Environment, FileSystemLoader

from acmt001.constants import TEMPLATES_DIR
from acmt001.security import validate_path
from acmt001.xml.generate_updated_xml_file_path import (
    generate_updated_xml_file_path,
)
from acmt001.xml.validate_via_xsd import validate_xml_string_via_xsd

# ── Flat input vocabulary shared across every acmt message ───────────
# Each ISO 20022 Account Management message renders the subset it needs.
# A preparer maps a flat record (one CSV row / JSON object) into the
# template context; list-oriented messages also receive a ``records`` list.

_HEADER_FIELDS = [
    "msg_id",
    "creation_date_time",
    "process_id",
]

_ACCOUNT_FIELDS = [
    "account_id",
    "account_id_other",
    "account_currency",
    "account_name",
    "account_type_cd",
    "account_servicer_bic",
    "account_owner_name",
    "account_owner_country",
    "account_owner_lei",
]

_ORG_FIELDS = [
    "org_full_legal_name",
    "org_country_of_operation",
    "org_address_country",
    "org_address_town",
    "org_id_lei",
    "org_id_other",
]

_STATUS_FIELDS = [
    "status_cd",
    "reason_cd",
    "additional_info",
]

_IDENTIFICATION_FIELDS = [
    "assigner_name",
    "assignee_name",
    "verification_id",
    "verification_indicator",
    "original_id",
    "party_name",
]

_REQUEST_FIELDS = [
    "request_to_be_completed_id",
    "request_reason",
]

_MANDATE_FIELDS = [
    "mandate_id",
    "mandate_channel",
    "required_signature_number",
    "signature_order_indicator",
]

# Account switching (UK-CASS style current-account-switch process) vocabulary.
_SWITCH_FIELDS = [
    "switch_reference",
    "routing_id",
    "switch_type_cd",
    "switch_status_cd",
    "switch_received_date_time",
    "switch_date",
    "new_account_id",
    "new_account_servicer_bic",
    "old_account_id",
    "old_account_servicer_bic",
    "balance_transfer_window_cd",
    "old_account_balance",
    "old_account_balance_cd",
    "account_owner_surname",
    "account_owner_given_name",
    "payment_instruction_id",
    "payment_end_to_end_id",
    "payment_amount",
    "response_code",
    "response_additional_details",
]

_ALL_FIELDS = (
    _HEADER_FIELDS
    + _ACCOUNT_FIELDS
    + _ORG_FIELDS
    + _STATUS_FIELDS
    + _IDENTIFICATION_FIELDS
    + _REQUEST_FIELDS
    + _MANDATE_FIELDS
    + _SWITCH_FIELDS
)

# Message-intrinsic defaults. Some account-switch fields are coded values whose
# valid code list is fixed by the message's semantics and version (e.g. the
# switch status, switch type, balance-transfer window, or response code). These
# are supplied per message type and filled in only where the input record does
# not provide a value, so a single flat record can drive every message type.
_MESSAGE_DEFAULTS: dict[str, dict[str, str]] = {
    "acmt.027.001.06": {
        "switch_status_cd": "REQU",
        "balance_transfer_window_cd": "EARL",
        "account_owner_surname": "Rousseau",
        "account_owner_given_name": "Sebastian",
    },
    "acmt.028.001.06": {
        "switch_status_cd": "REQU",
        "balance_transfer_window_cd": "EARL",
    },
    "acmt.029.001.06": {
        "switch_status_cd": "REQU",
        "balance_transfer_window_cd": "EARL",
    },
    "acmt.030.001.04": {
        "switch_status_cd": "REQU",
        "balance_transfer_window_cd": "EARL",
    },
    "acmt.031.001.06": {
        "switch_status_cd": "REQU",
        "balance_transfer_window_cd": "EARL",
    },
    "acmt.032.001.06": {
        "switch_type_cd": "FULL",
        "switch_status_cd": "BTRS",
        "switch_received_date_time": "2026-01-15T10:30:00",
        "switch_date": "2026-01-15",
        "balance_transfer_window_cd": "DAYH",
        "old_account_balance": "1234.56",
        "old_account_balance_cd": "CRDT",
    },
    "acmt.033.001.02": {
        "switch_type_cd": "FULL",
        "switch_status_cd": "COMP",
        "switch_received_date_time": "2026-01-15T10:30:00",
        "switch_date": "2026-01-15",
    },
    "acmt.034.001.06": {
        "switch_type_cd": "FULL",
        "switch_status_cd": "BTRQ",
        "switch_received_date_time": "2026-01-15T10:30:00",
        "switch_date": "2026-01-15",
        "payment_instruction_id": "PMTINSTR-0001",
        "payment_end_to_end_id": "E2E-SWTCH-0001",
        "payment_amount": "1234.56",
    },
    "acmt.035.001.02": {
        "switch_type_cd": "FULL",
        "switch_status_cd": "ACPT",
        "switch_received_date_time": "2026-01-15T10:30:00",
        "switch_date": "2026-01-15",
        "response_code": "ACPT",
        "response_additional_details": (
            "Payment instruction accepted by old account servicer"
        ),
    },
    "acmt.036.001.01": {
        "switch_type_cd": "FULL",
        "switch_status_cd": "TMTN",
        "switch_received_date_time": "2026-01-15T10:30:00",
        "switch_date": "2026-01-15",
    },
    "acmt.037.001.02": {
        "switch_type_cd": "FULL",
        "switch_status_cd": "REJT",
        "switch_received_date_time": "2026-01-15T10:30:00",
        "switch_date": "2026-01-15",
        "response_code": "TECH",
        "response_additional_details": (
            "Message failed technical validation and cannot be processed"
        ),
    },
}


def _build_record(row: dict[str, Any]) -> dict[str, Any]:
    """Project a raw input row onto the known acmt field vocabulary."""
    return {field: row.get(field, "") for field in _ALL_FIELDS}


def _build_context(data: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a render context from a list of account records.

    The first record populates the single-subject (header / account / org)
    fields. Every record is also exposed via ``records`` so list-oriented
    messages (acknowledgements, reports, identification verification) can
    iterate. This mirrors the per-message preparer pattern while keeping a
    single, coherent flat vocabulary.
    """
    context = _build_record(data[0])
    context["records"] = [_build_record(row) for row in data]
    return context


# ── Per-family preparers ─────────────────────────────────────────────
# Each ISO 20022 Account Management business area gets a dedicated preparer
# so message-specific behaviour has an obvious home, mirroring the public
# structure of the wider library.


def _prepare_account_opening(data: list[dict[str, Any]]) -> dict[str, Any]:
    """Prepare data for account opening messages (instruction / request)."""
    return _build_context(data)


def _prepare_account_amendment(data: list[dict[str, Any]]) -> dict[str, Any]:
    """Prepare data for account opening / closing amendment messages."""
    return _build_context(data)


def _prepare_account_additional_info(
    data: list[dict[str, Any]],
) -> dict[str, Any]:
    """Prepare data for additional information request messages."""
    return _build_context(data)


def _prepare_account_modification(
    data: list[dict[str, Any]],
) -> dict[str, Any]:
    """Prepare data for account modification / details confirmation."""
    return _build_context(data)


def _prepare_account_status(data: list[dict[str, Any]]) -> dict[str, Any]:
    """Prepare data for status report request / status report messages."""
    return _build_context(data)


def _prepare_account_response(data: list[dict[str, Any]]) -> dict[str, Any]:
    """Prepare data for acknowledgement / rejection messages."""
    return _build_context(data)


def _prepare_account_report(data: list[dict[str, Any]]) -> dict[str, Any]:
    """Prepare data for account report request / account report messages."""
    return _build_context(data)


def _prepare_account_maintenance(
    data: list[dict[str, Any]],
) -> dict[str, Any]:
    """Prepare data for mandate maintenance messages."""
    return _build_context(data)


def _prepare_account_closing(data: list[dict[str, Any]]) -> dict[str, Any]:
    """Prepare data for account closing messages."""
    return _build_context(data)


def _prepare_identification(data: list[dict[str, Any]]) -> dict[str, Any]:
    """Prepare data for identification modification / verification messages."""
    return _build_context(data)


def _prepare_account_switch(data: list[dict[str, Any]]) -> dict[str, Any]:
    """Prepare data for the account switching (current-account-switch) suite."""
    return _build_context(data)


# Dispatch every supported message type to its preparer.
_XML_DATA_PREPARERS = {
    "acmt.001.001.08": _prepare_account_opening,
    "acmt.002.001.08": _prepare_account_modification,
    "acmt.003.001.08": _prepare_account_modification,
    "acmt.005.001.06": _prepare_account_status,
    "acmt.006.001.07": _prepare_account_status,
    "acmt.007.001.05": _prepare_account_opening,
    "acmt.008.001.05": _prepare_account_amendment,
    "acmt.009.001.04": _prepare_account_additional_info,
    "acmt.010.001.04": _prepare_account_response,
    "acmt.011.001.04": _prepare_account_response,
    "acmt.012.001.04": _prepare_account_additional_info,
    "acmt.013.001.04": _prepare_account_report,
    "acmt.014.001.05": _prepare_account_report,
    "acmt.015.001.05": _prepare_account_maintenance,
    "acmt.016.001.05": _prepare_account_amendment,
    "acmt.017.001.05": _prepare_account_maintenance,
    "acmt.018.001.05": _prepare_account_amendment,
    "acmt.019.001.04": _prepare_account_closing,
    "acmt.020.001.04": _prepare_account_amendment,
    "acmt.021.001.04": _prepare_account_additional_info,
    "acmt.022.001.04": _prepare_identification,
    "acmt.023.001.04": _prepare_identification,
    "acmt.024.001.04": _prepare_identification,
    "acmt.027.001.06": _prepare_account_switch,
    "acmt.028.001.06": _prepare_account_switch,
    "acmt.029.001.06": _prepare_account_switch,
    "acmt.030.001.04": _prepare_account_switch,
    "acmt.031.001.06": _prepare_account_switch,
    "acmt.032.001.06": _prepare_account_switch,
    "acmt.033.001.02": _prepare_account_switch,
    "acmt.034.001.06": _prepare_account_switch,
    "acmt.035.001.02": _prepare_account_switch,
    "acmt.036.001.01": _prepare_account_switch,
    "acmt.037.001.02": _prepare_account_switch,
}


def _render_and_validate(
    data: list[dict[str, Any]],
    account_management_message_type: str,
    xml_template_path: str,
    xsd_schema_path: str,
) -> str:
    """Render the template for a message type and validate it against the XSD.

    Shared by ``generate_xml_string`` (user-supplied paths) and
    ``generate_message`` (packaged, trusted paths). Assumes the message type and
    data have already been checked.
    """
    # Fill message-intrinsic coded defaults where the record omits them, so a
    # single flat record can drive every message type. Record values always win.
    defaults = _MESSAGE_DEFAULTS.get(account_management_message_type)
    if defaults:
        data = [
            {
                **defaults,
                **{k: v for k, v in row.items() if str(v).strip()},
            }
            for row in data
        ]

    preparer = _XML_DATA_PREPARERS[account_management_message_type]
    xml_data = preparer(data)

    template_dir = os.path.dirname(xml_template_path)
    template_file = os.path.basename(xml_template_path)
    loader_path = template_dir if template_dir else "."

    env = Environment(loader=FileSystemLoader(loader_path), autoescape=True)
    template = env.get_template(template_file)

    xml_content = template.render(**xml_data)

    is_valid = validate_xml_string_via_xsd(xml_content, xsd_schema_path)

    if not is_valid:
        raise RuntimeError(
            f"Generated XML failed validation against {xsd_schema_path}"
        )

    return xml_content


def generate_xml_string(
    data: list[dict[str, Any]],
    account_management_message_type: str,
    xml_template_path: str,
    xsd_schema_path: str,
) -> str:
    """Generate ISO 20022 acmt XML content as a string."""
    try:
        xml_template_path = validate_path(xml_template_path)
    except Exception as e:
        raise ValueError(f"Invalid template path: {e}") from e

    try:
        xsd_schema_path = validate_path(xsd_schema_path)
    except Exception as e:
        raise ValueError(f"Invalid schema path: {e}") from e

    if account_management_message_type not in _XML_DATA_PREPARERS:
        raise ValueError(
            f"Invalid XML message type: {account_management_message_type}"
        )

    if not data:
        raise ValueError("No data to process - data list is empty")

    return _render_and_validate(
        data,
        account_management_message_type,
        xml_template_path,
        xsd_schema_path,
    )


def generate_message(
    data: list[dict[str, Any]],
    account_management_message_type: str,
) -> str:
    """Generate validated acmt XML using the template + XSD bundled with the
    package, without requiring the caller to know file paths.

    Unlike ``generate_xml_string`` (which validates caller-supplied paths
    against the working directory), this uses the trusted, package-internal
    template and schema for the given message type — the convenient entry point
    for the MCP server, the REST API, and other in-process callers.

    Args:
        data: One or more flat account records.
        account_management_message_type: A supported ISO 20022 acmt type.

    Returns:
        The validated XML document as a string.

    Raises:
        ValueError: If the message type is unsupported or data is empty.
    """
    if account_management_message_type not in _XML_DATA_PREPARERS:
        raise ValueError(
            f"Invalid XML message type: {account_management_message_type}"
        )

    if not data:
        raise ValueError("No data to process - data list is empty")

    tdir = TEMPLATES_DIR / account_management_message_type
    return _render_and_validate(
        data,
        account_management_message_type,
        str(tdir / "template.xml"),
        str(tdir / f"{account_management_message_type}.xsd"),
    )


def generate_xml(
    data: list[dict[str, Any]],
    account_management_message_type: str,
    xml_file_path: str,
    xsd_file_path: str,
) -> None:
    """Generates an ISO 20022 acmt XML file from input data."""
    xml_content = generate_xml_string(
        data,
        account_management_message_type,
        xml_file_path,
        xsd_file_path,
    )

    updated_xml_file_path = generate_updated_xml_file_path(
        xml_file_path, account_management_message_type
    )

    try:
        safe_xml_path = validate_path(updated_xml_file_path)
    except Exception as e:
        raise ValueError(f"Path validation failed: {e}") from e

    cwd_prefix = str(os.path.realpath(os.getcwd()))
    if not safe_xml_path.startswith(cwd_prefix + os.sep):
        raise ValueError(
            f"Output path outside working directory: {safe_xml_path}"
        )

    with open(safe_xml_path, "w", encoding="utf-8") as xml_file:
        xml_file.write(xml_content)

    print(f"A new XML file has been created at `{safe_xml_path}`")
    print(f"The XML has been validated against `{xsd_file_path}`")
