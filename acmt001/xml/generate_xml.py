"""XML generator for ISO 20022 acmt Account Management messages."""

import os
from typing import Any

from jinja2 import Environment, FileSystemLoader

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

_ALL_FIELDS = (
    _HEADER_FIELDS
    + _ACCOUNT_FIELDS
    + _ORG_FIELDS
    + _STATUS_FIELDS
    + _IDENTIFICATION_FIELDS
    + _REQUEST_FIELDS
    + _MANDATE_FIELDS
)


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
    "acmt.017.001.05": _prepare_account_maintenance,
    "acmt.019.001.04": _prepare_account_closing,
    "acmt.020.001.04": _prepare_account_amendment,
    "acmt.021.001.04": _prepare_account_additional_info,
    "acmt.022.001.04": _prepare_identification,
    "acmt.023.001.04": _prepare_identification,
    "acmt.024.001.04": _prepare_identification,
}


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
