"""Tests for validation/schema_validator.py — JSON Schema validation."""

import json

import pytest

from acmt001.validation.schema_validator import (
    SchemaValidator,
    ValidationError,
)

VERSION = "acmt.007.001.05"

GOLD = (
    __import__("pathlib").Path(__file__).resolve().parent
    / "gold_master"
    / "account_opening_full.json"
)


@pytest.fixture()
def validator():
    return SchemaValidator(VERSION)


@pytest.fixture()
def valid_record():
    return dict(json.loads(GOLD.read_text())[0])


class TestSchemaValidatorInit:
    def test_valid_message_type(self):
        v = SchemaValidator(VERSION)
        assert v.schema is not None
        assert v.schema_path.endswith(f"{VERSION}.schema.json")

    def test_invalid_message_type_raises(self):
        with pytest.raises(ValueError):
            SchemaValidator("acmt.999.001.99")

    def test_missing_schema_dir(self, tmp_path):
        # Valid type, but the schema file does not exist in the given dir
        with pytest.raises(FileNotFoundError):
            SchemaValidator(VERSION, schema_dir=tmp_path)

    def test_invalid_json_schema_file(self, tmp_path):
        # A schema file that exists but contains malformed JSON
        schema_file = tmp_path / f"{VERSION}.schema.json"
        schema_file.write_text("{ this is not valid json ")
        with pytest.raises(json.JSONDecodeError):
            SchemaValidator(VERSION, schema_dir=tmp_path)


class TestValidateData:
    def test_valid_data_passes(self, validator, valid_record):
        errors = validator.validate_data(valid_record)
        assert errors == []

    def test_missing_required_field(self, validator, valid_record):
        bad = dict(valid_record)
        del bad["msg_id"]
        errors = validator.validate_data(bad)
        assert len(errors) >= 1
        assert isinstance(errors[0], ValidationError)

    def test_pattern_violation(self, validator, valid_record):
        bad = dict(valid_record)
        bad["account_currency"] = "euro"  # must match ^[A-Z]{3}$
        errors = validator.validate_data(bad)
        assert len(errors) >= 1
        assert errors[0].rule in ("pattern", "maxLength")

    def test_error_path_formatting(self, validator, valid_record):
        bad = dict(valid_record)
        bad["account_owner_country"] = "X"  # must be ^[A-Z]{2}$
        errors = validator.validate_data(bad)
        assert errors
        assert errors[0].path.startswith("$")

    def test_schema_error_raises_value_error(self, validator):
        """A structurally invalid schema raises ValueError on validation."""
        validator.schema = {"type": "not-a-real-type"}
        with pytest.raises(ValueError):
            validator.validate_data({"x": 1})


class TestValidateRow:
    def test_valid_row(self, validator, valid_record):
        ok, errors = validator.validate_row(valid_record)
        assert ok
        assert errors == []

    def test_invalid_row(self, validator, valid_record):
        bad = dict(valid_record)
        del bad["account_id"]
        ok, errors = validator.validate_row(bad)
        assert not ok
        assert errors


class TestValidateBatch:
    def test_all_valid(self, validator, valid_record):
        rows = [dict(valid_record), dict(valid_record)]
        total, valid, errors = validator.validate_batch(rows)
        assert total == 2
        assert valid == 2
        assert errors == []

    def test_mixed_batch(self, validator, valid_record):
        bad = dict(valid_record)
        del bad["msg_id"]
        rows = [dict(valid_record), bad]
        total, valid, errors = validator.validate_batch(rows)
        assert total == 2
        assert valid == 1
        assert len(errors) == 1
        idx, errlist = errors[0]
        assert idx == 1
        assert errlist

    def test_empty_batch(self, validator):
        total, valid, errors = validator.validate_batch([])
        assert total == 0
        assert valid == 0
        assert errors == []


class TestSchemaIntrospection:
    def test_get_required_fields(self, validator):
        required = validator.get_required_fields()
        assert "msg_id" in required
        assert "org_id_lei" in required

    def test_get_field_schema(self, validator):
        schema = validator.get_field_schema("msg_id")
        assert schema is not None
        assert schema["type"] == "string"

    def test_get_field_schema_unknown(self, validator):
        assert validator.get_field_schema("does_not_exist") is None

    def test_get_field_description(self, validator):
        desc = validator.get_field_description("msg_id")
        assert desc is not None
        assert "identification" in desc.lower()

    def test_get_field_description_unknown(self, validator):
        assert validator.get_field_description("does_not_exist") is None


class TestValidationErrorClass:
    def test_str_and_repr(self):
        err = ValidationError(
            message="is required", path="$.msg_id", value=None, rule="required"
        )
        assert str(err) == "$.msg_id: is required"
        assert "msg_id" in repr(err)
        assert "required" in repr(err)
