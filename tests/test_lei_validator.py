"""Tests for LEI validation (ISO 17442 + ISO 7064 mod-97-10).

The reference valid LEI used throughout is ``5493001KJTIIGC8Y1R12`` — a
real, checksum-valid Legal Entity Identifier.
"""

import pytest

from acmt001.exceptions import InvalidLEIError
from acmt001.validation.lei_validator import (
    LEI_LENGTH,
    validate_lei,
    validate_lei_checksum,
    validate_lei_format,
    validate_lei_safe,
)

VALID_LEI = "5493001KJTIIGC8Y1R12"


class TestValidateLeiFormat:
    """Test LEI format validation."""

    def test_valid_lei(self):
        ok, err = validate_lei_format(VALID_LEI)
        assert ok
        assert err == ""

    def test_valid_lei_with_spaces(self):
        ok, err = validate_lei_format("5493 001K JTII GC8Y 1R12")
        assert ok

    def test_valid_lowercase_lei(self):
        ok, err = validate_lei_format(VALID_LEI.lower())
        assert ok

    def test_empty_lei(self):
        ok, err = validate_lei_format("")
        assert not ok
        assert "empty" in err.lower()

    def test_too_short(self):
        ok, err = validate_lei_format("5493001KJTII")
        assert not ok
        assert str(LEI_LENGTH) in err

    def test_too_long(self):
        ok, err = validate_lei_format(VALID_LEI + "99")
        assert not ok
        assert str(LEI_LENGTH) in err

    def test_non_alphanumeric_identifier(self):
        # 20 chars but a '!' in the identifier portion
        ok, err = validate_lei_format("5493001KJTIIGC8Y1R!2")
        assert not ok
        assert "alphanumeric" in err.lower() or "check digits" in err.lower()

    def test_non_digit_check_digits(self):
        # last two characters must be digits
        ok, err = validate_lei_format("5493001KJTIIGC8Y1RAB")
        assert not ok
        assert "check digits" in err.lower()

    def test_non_alphanumeric_identifier_only(self):
        # 18-char identifier contains '!' but the last 2 are digits
        ok, err = validate_lei_format("5493001KJTII!C8Y1R12")
        assert not ok
        assert "alphanumeric" in err.lower()


class TestValidateLeiChecksum:
    """Test ISO 7064 mod-97-10 checksum validation (no rearrangement)."""

    def test_valid_checksum(self):
        ok, err = validate_lei_checksum(VALID_LEI)
        assert ok
        assert err == ""

    def test_corrupted_checksum(self):
        ok, err = validate_lei_checksum("5493001KJTIIGC8Y1R99")
        assert not ok
        assert "checksum" in err.lower()

    def test_checksum_with_spaces(self):
        ok, err = validate_lei_checksum("5493 001K JTII GC8Y 1R12")
        assert ok

    def test_invalid_character(self):
        ok, err = validate_lei_checksum("5493001KJTIIGC8Y1R!2")
        assert not ok
        assert "Invalid character" in err


class TestValidateLei:
    """Test the main validate_lei entry point."""

    def test_valid_lei_strict(self):
        ok, err = validate_lei(VALID_LEI)
        assert ok
        assert err == ""

    def test_valid_lei_non_strict(self):
        ok, err = validate_lei(VALID_LEI, strict=False)
        assert ok

    def test_invalid_format_strict_raises(self):
        with pytest.raises(InvalidLEIError) as exc_info:
            validate_lei("", field="org_id_lei")
        assert exc_info.value.field == "org_id_lei"
        assert exc_info.value.lei == ""
        assert exc_info.value.reason == "Invalid LEI format"

    def test_invalid_format_non_strict(self):
        ok, err = validate_lei("", strict=False)
        assert not ok

    def test_corrupted_checksum_strict_raises(self):
        with pytest.raises(InvalidLEIError) as exc_info:
            validate_lei("5493001KJTIIGC8Y1R99", field="account_owner_lei")
        assert "checksum" in exc_info.value.reason.lower()

    def test_corrupted_checksum_non_strict(self):
        ok, err = validate_lei("5493001KJTIIGC8Y1R99", strict=False)
        assert not ok
        assert "checksum" in err.lower()


class TestValidateLeiSafe:
    """Test the safe (no-exception) wrapper."""

    def test_valid_lei(self):
        assert validate_lei_safe(VALID_LEI)

    def test_invalid_format(self):
        assert not validate_lei_safe("")

    def test_corrupted_checksum(self):
        assert not validate_lei_safe("5493001KJTIIGC8Y1R99")

    def test_with_field_name(self):
        assert validate_lei_safe(VALID_LEI, field="org_id_lei")


class TestLeiConstants:
    def test_lei_length_is_20(self):
        assert LEI_LENGTH == 20
