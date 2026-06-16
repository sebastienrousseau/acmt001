"""Tests for acmt001.csv.validate_csv_data module."""

from datetime import datetime

import pytest

from acmt001.csv.validate_csv_data import (
    _validate_datetime,
    _validate_field_type,
    validate_csv_data,
)

REQUIRED_COLUMNS = [
    "msg_id",
    "creation_date_time",
    "process_id",
    "account_id",
    "account_currency",
    "account_name",
    "account_type_cd",
    "account_servicer_bic",
    "account_owner_name",
    "account_owner_country",
    "org_full_legal_name",
    "org_id_lei",
]


def _valid_row():
    return {
        "msg_id": "ACMT-MSG-0001",
        "creation_date_time": "2026-01-15T10:30:00",
        "process_id": "ACMT-PRC-0001",
        "account_id": "GB29NWBK60161331926819",
        "account_currency": "EUR",
        "account_name": "Treasury Operating Account",
        "account_type_cd": "CACC",
        "account_servicer_bic": "NWBKGB2LXXX",
        "account_owner_name": "Acme Embedded Finance Ltd",
        "account_owner_country": "GB",
        "org_full_legal_name": "Acme Embedded Finance Limited",
        "org_id_lei": "5493001KJTIIGC8Y1R12",
    }


def test_valid_record_passes():
    assert validate_csv_data([_valid_row()]) is True


def test_empty_data_fails():
    assert validate_csv_data([]) is False


def test_multiple_valid_rows():
    assert validate_csv_data([_valid_row(), _valid_row()]) is True


@pytest.mark.parametrize("column", REQUIRED_COLUMNS)
def test_each_missing_required_column_fails(column):
    row = _valid_row()
    del row[column]
    assert validate_csv_data([row]) is False


def test_none_value_treated_as_missing():
    row = _valid_row()
    row["msg_id"] = None
    assert validate_csv_data([row]) is False


def test_invalid_datetime_fails():
    row = _valid_row()
    row["creation_date_time"] = "not-a-date"
    assert validate_csv_data([row]) is False


def test_whitespace_only_field_fails():
    row = _valid_row()
    row["account_name"] = "   "
    assert validate_csv_data([row]) is False


def test_empty_string_field_fails():
    row = _valid_row()
    row["account_owner_name"] = ""
    assert validate_csv_data([row]) is False


def test_utc_datetime_with_z_passes():
    row = _valid_row()
    row["creation_date_time"] = "2026-01-15T10:30:00Z"
    assert validate_csv_data([row]) is True


def test_date_only_passes():
    row = _valid_row()
    row["creation_date_time"] = "2026-01-15"
    assert validate_csv_data([row]) is True


class TestValidateFieldType:
    """Direct tests for the typed-field helper (non-str/datetime branches)."""

    def test_int_valid(self):
        assert _validate_field_type("42", int) is True

    def test_int_invalid(self):
        assert _validate_field_type("abc", int) is False

    def test_float_valid(self):
        assert _validate_field_type("3.14", float) is True

    def test_float_invalid(self):
        assert _validate_field_type("xyz", float) is False

    def test_bool_valid(self):
        assert _validate_field_type("true", bool) is True
        assert _validate_field_type("FALSE", bool) is True

    def test_bool_invalid(self):
        assert _validate_field_type("maybe", bool) is False

    def test_str_always_valid(self):
        assert _validate_field_type("anything", str) is True

    def test_datetime_branch(self):
        assert _validate_field_type("2026-01-15T10:30:00", datetime) is True
        assert _validate_field_type("nope", datetime) is False


class TestValidateDatetime:
    def test_iso(self):
        assert _validate_datetime("2026-01-15T10:30:00") is True

    def test_z_suffix(self):
        assert _validate_datetime("2026-01-15T10:30:00Z") is True

    def test_date_only(self):
        assert _validate_datetime("2026-01-15") is True

    def test_invalid(self):
        assert _validate_datetime("not-a-date") is False
