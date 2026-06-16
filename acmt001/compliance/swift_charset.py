"""SWIFT character set validation and field length enforcement.

Banks reject messages not because they fail XSD validation, but because
they violate SWIFT Usage Guidelines (CBPR+, Target2). This module
prevents "silent rejections" by cleansing data before XML generation.

The SWIFT X Character Set (ISO 15022) allows:
  a-z A-Z 0-9 / - ? : ( ) . , ' + { } CR LF Space

Field length limits follow ISO 20022 acmt.007.001.05 element definitions:
  - Nm (Name): max 140 characters
  - Id (Identifiers): max 35 characters
  - AddtlInf (Additional information): max 350 characters
  - IBAN: max 34 characters
  - BIC: 8 or 11 characters
  - Currency: exactly 3 characters

Example:
    >>> from acmt001.compliance import cleanse_data
    >>> raw = [{"account_owner_name": "Müller & Söhne™", "msg_id": "X" * 50}]
    >>> clean = cleanse_data(raw)
    >>> clean[0]["account_owner_name"]  # non-SWIFT chars replaced
    'Mueller . Soehne.'
    >>> len(clean[0]["msg_id"])  # truncated to 35
    35
"""

import unicodedata
from typing import Any, Optional

# SWIFT X Character Set (ISO 15022 / MT standard)
# Characters allowed in SWIFT FIN messages
SWIFT_X_CHARSET = set(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    "/-?:().,'+{} \r\n"
)

# ISO 20022 acmt.007.001.05 field length limits
FIELD_MAX_LENGTHS: dict[str, int] = {
    "msg_id": 35,
    "process_id": 35,
    "account_id": 34,
    "account_id_other": 34,
    "verification_id": 35,
    "original_id": 35,
    "request_to_be_completed_id": 35,
    "mandate_id": 35,
    "account_name": 70,
    "account_owner_name": 140,
    "org_full_legal_name": 140,
    "party_name": 140,
    "assigner_name": 140,
    "assignee_name": 140,
    "account_servicer_bic": 11,
    "account_currency": 3,
    "account_type_cd": 4,
    "status_cd": 4,
    "reason_cd": 4,
    "request_reason": 4,
    "mandate_channel": 4,
    "account_owner_country": 2,
    "account_owner_lei": 20,
    "org_country_of_operation": 2,
    "org_address_country": 2,
    "org_address_town": 35,
    "org_id_lei": 20,
    "org_id_other": 35,
    "additional_info": 350,
}

# Unicode → ASCII transliteration map for common banking characters
_TRANSLITERATION: dict[str, str] = {
    "ä": "ae",
    "ö": "oe",
    "ü": "ue",
    "ß": "ss",
    "Ä": "Ae",
    "Ö": "Oe",
    "Ü": "Ue",
    "á": "a",
    "à": "a",
    "â": "a",
    "ã": "a",
    "å": "a",
    "é": "e",
    "è": "e",
    "ê": "e",
    "ë": "e",
    "í": "i",
    "ì": "i",
    "î": "i",
    "ï": "i",
    "ó": "o",
    "ò": "o",
    "ô": "o",
    "õ": "o",
    "ú": "u",
    "ù": "u",
    "û": "u",
    "ñ": "n",
    "ç": "c",
    "Á": "A",
    "À": "A",
    "Â": "A",
    "Ã": "A",
    "Å": "A",
    "É": "E",
    "È": "E",
    "Ê": "E",
    "Ë": "E",
    "Í": "I",
    "Ì": "I",
    "Î": "I",
    "Ï": "I",
    "Ó": "O",
    "Ò": "O",
    "Ô": "O",
    "Õ": "O",
    "Ú": "U",
    "Ù": "U",
    "Û": "U",
    "Ñ": "N",
    "Ç": "C",
    "æ": "ae",
    "Æ": "AE",
    "ø": "o",
    "Ø": "O",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "™": ".",
    "©": ".",
    "®": ".",
    "&": ".",
    "@": ".",
    "#": ".",
    "!": ".",
    ";": ".",
    "=": ".",
    "*": ".",
    "~": ".",
    "[": "(",
    "]": ")",
    "{": "(",
    "}": ")",
    "\\": "/",
    "|": "/",
    "^": ".",
    "_": "-",
    '"': "'",
    "`": "'",
}


class ComplianceViolation:
    """Represents a single SWIFT compliance violation."""

    def __init__(
        self,
        field: str,
        violation_type: str,
        original_value: str,
        corrected_value: Optional[str] = None,
        message: str = "",
    ) -> None:
        self.field = field
        self.violation_type = violation_type
        self.original_value = original_value
        self.corrected_value = corrected_value
        self.message = message

    def __repr__(self) -> str:
        return (
            f"ComplianceViolation(field={self.field!r}, "
            f"type={self.violation_type!r})"
        )


class ComplianceReport:
    """Aggregated report of all compliance violations found and corrected."""

    def __init__(self) -> None:
        self.violations: list[ComplianceViolation] = []
        self.rows_processed: int = 0
        self.rows_modified: int = 0

    @property
    def is_clean(self) -> bool:
        """True if no violations were found."""
        return len(self.violations) == 0

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    def add(self, violation: ComplianceViolation) -> None:
        self.violations.append(violation)

    def summary(self) -> str:
        """Human-readable summary."""
        if self.is_clean:
            return f"All {self.rows_processed} rows are SWIFT-compliant."
        return (
            f"{self.violation_count} violations found across "
            f"{self.rows_modified}/{self.rows_processed} rows. "
            f"All auto-corrected."
        )


def _transliterate(char: str) -> str:
    """Transliterate a single character to SWIFT-safe equivalent."""
    if char in SWIFT_X_CHARSET:
        return char

    # Check explicit map first
    if char in _TRANSLITERATION:
        return _TRANSLITERATION[char]

    # Try Unicode NFKD decomposition (strips accents)
    decomposed = unicodedata.normalize("NFKD", char)
    ascii_chars = "".join(c for c in decomposed if c in SWIFT_X_CHARSET)
    if ascii_chars:
        return ascii_chars

    # Last resort: replace with period
    return "."


def validate_swift_charset(value: str) -> list[tuple[int, str]]:
    """Check a string for non-SWIFT characters.

    Args:
        value: String to validate.

    Returns:
        List of (position, character) tuples for invalid characters.
        Empty list means the string is SWIFT-compliant.
    """
    violations = []
    for i, char in enumerate(value):
        if char not in SWIFT_X_CHARSET:
            violations.append((i, char))
    return violations


def cleanse_string(value: str) -> str:
    """Transliterate a string to the SWIFT X Character Set.

    Replaces non-SWIFT characters with their closest ASCII equivalents.
    Characters with no reasonable mapping are replaced with '.'.

    Args:
        value: Input string (may contain Unicode).

    Returns:
        SWIFT-safe string with only X charset characters.
    """
    return "".join(_transliterate(c) for c in value)


def enforce_field_lengths(
    row: dict[str, Any],
    max_lengths: Optional[dict[str, int]] = None,
) -> tuple[dict[str, Any], list[ComplianceViolation]]:
    """Truncate fields that exceed ISO 20022 maximum lengths.

    Args:
        row: Account management data dictionary.
        max_lengths: Custom max lengths. Defaults to ISO 20022
            acmt.007.001.05 limits.

    Returns:
        Tuple of (corrected_row, list_of_violations).
    """
    lengths = max_lengths or FIELD_MAX_LENGTHS
    violations: list[ComplianceViolation] = []
    corrected = dict(row)

    for field, max_len in lengths.items():
        value = corrected.get(field)
        if value is None:
            continue
        str_value = str(value)
        if len(str_value) > max_len:
            truncated = str_value[:max_len]
            violations.append(
                ComplianceViolation(
                    field=field,
                    violation_type="field_length",
                    original_value=str_value,
                    corrected_value=truncated,
                    message=(
                        f"Truncated from {len(str_value)} to "
                        f"{max_len} characters"
                    ),
                )
            )
            corrected[field] = truncated

    return corrected, violations


# Fields that contain free-text and need charset cleansing
_TEXT_FIELDS = {
    "account_name",
    "account_owner_name",
    "org_full_legal_name",
    "org_address_town",
    "party_name",
    "assigner_name",
    "assignee_name",
    "additional_info",
}


def cleanse_data(
    data: list[dict[str, Any]],
    enforce_lengths: bool = True,
    cleanse_charset: bool = True,
) -> list[dict[str, Any]]:
    """Cleanse account management data for SWIFT compliance.

    Applies two passes:
    1. Character set cleansing (transliterate non-SWIFT chars in text fields)
    2. Field length enforcement (truncate to ISO 20022 limits)

    Args:
        data: List of account management data dictionaries.
        enforce_lengths: Whether to truncate oversized fields.
        cleanse_charset: Whether to transliterate non-SWIFT characters.

    Returns:
        Cleansed data ready for XML generation.
    """
    cleansed: list[dict[str, Any]] = []

    for row in data:
        corrected = dict(row)

        # Pass 1: Charset cleansing on text fields
        if cleanse_charset:
            for field in _TEXT_FIELDS:
                value = corrected.get(field)
                if value and isinstance(value, str):
                    corrected[field] = cleanse_string(value)

        # Pass 2: Field length enforcement
        if enforce_lengths:
            corrected, _ = enforce_field_lengths(corrected)

        cleansed.append(corrected)

    return cleansed


def cleanse_data_with_report(
    data: list[dict[str, Any]],
    enforce_lengths: bool = True,
    cleanse_charset: bool = True,
) -> tuple[list[dict[str, Any]], ComplianceReport]:
    """Cleanse account management data and return a compliance report.

    Same as cleanse_data() but also returns a ComplianceReport with
    every violation found and corrected.

    Args:
        data: List of account management data dictionaries.
        enforce_lengths: Whether to truncate oversized fields.
        cleanse_charset: Whether to transliterate non-SWIFT characters.

    Returns:
        Tuple of (cleansed_data, compliance_report).
    """
    report = ComplianceReport()
    report.rows_processed = len(data)
    cleansed: list[dict[str, Any]] = []

    for row in data:
        corrected = dict(row)
        row_modified = False

        # Pass 1: Charset cleansing
        if cleanse_charset:
            for field in _TEXT_FIELDS:
                value = corrected.get(field)
                if value and isinstance(value, str):
                    cleaned = cleanse_string(value)
                    if cleaned != value:
                        report.add(
                            ComplianceViolation(
                                field=field,
                                violation_type="charset",
                                original_value=value,
                                corrected_value=cleaned,
                                message="Non-SWIFT characters replaced",
                            )
                        )
                        corrected[field] = cleaned
                        row_modified = True

        # Pass 2: Field length enforcement
        if enforce_lengths:
            corrected, length_violations = enforce_field_lengths(corrected)
            if length_violations:
                report.violations.extend(length_violations)
                row_modified = True

        if row_modified:
            report.rows_modified += 1

        cleansed.append(corrected)

    return cleansed, report
