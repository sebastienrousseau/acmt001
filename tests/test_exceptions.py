"""Tests for acmt001.exceptions module — full hierarchy and attributes."""

from acmt001.exceptions import (
    AccountValidationError,
    Acmt001Error,
    ConfigurationError,
    DataSourceError,
    InvalidBICError,
    InvalidIBANError,
    InvalidLEIError,
    MissingRequiredFieldError,
    SchemaValidationError,
    XMLGenerationError,
    XSDValidationError,
)


def test_acmt001_error_hierarchy():
    assert issubclass(AccountValidationError, Acmt001Error)
    assert issubclass(XMLGenerationError, Acmt001Error)
    assert issubclass(ConfigurationError, Acmt001Error)
    assert issubclass(DataSourceError, Acmt001Error)
    assert issubclass(SchemaValidationError, Acmt001Error)


def test_account_validation_subclasses():
    assert issubclass(InvalidIBANError, AccountValidationError)
    assert issubclass(InvalidBICError, AccountValidationError)
    assert issubclass(InvalidLEIError, AccountValidationError)
    assert issubclass(MissingRequiredFieldError, AccountValidationError)


def test_base_error_is_exception():
    assert issubclass(Acmt001Error, Exception)


def test_account_validation_error_field():
    e = AccountValidationError("bad field", field="account_id")
    assert e.field == "account_id"
    assert str(e) == "bad field"


def test_account_validation_error_default_field_none():
    e = AccountValidationError("no field")
    assert e.field is None


def test_xml_generation_error_plain():
    e = XMLGenerationError("generation failed")
    assert str(e) == "generation failed"
    assert isinstance(e, Acmt001Error)


def test_configuration_error_plain():
    e = ConfigurationError("bad config")
    assert str(e) == "bad config"


def test_data_source_error_plain():
    e = DataSourceError("cannot read")
    assert str(e) == "cannot read"


def test_schema_validation_error_with_errors():
    e = SchemaValidationError("schema fail", errors=["err1", "err2"])
    assert len(e.errors) == 2
    assert "err1" in e.errors


def test_schema_validation_error_default_errors_empty():
    e = SchemaValidationError("schema fail")
    assert e.errors == []


def test_xsd_validation_error_alias():
    assert XSDValidationError is SchemaValidationError


def test_invalid_iban_error_all_fields():
    e = InvalidIBANError(
        "bad iban", iban="XX00", field="account_id", reason="checksum"
    )
    assert e.iban == "XX00"
    assert e.field == "account_id"
    assert e.reason == "checksum"


def test_invalid_iban_error_defaults():
    e = InvalidIBANError("bad iban", iban="XX00")
    assert e.field is None
    assert e.reason is None


def test_invalid_bic_error_all_fields():
    e = InvalidBICError(
        "bad bic",
        bic="XXXX",
        field="account_servicer_bic",
        reason="format",
    )
    assert e.bic == "XXXX"
    assert e.field == "account_servicer_bic"
    assert e.reason == "format"


def test_invalid_bic_error_defaults():
    e = InvalidBICError("bad bic", bic="XXXX")
    assert e.field is None
    assert e.reason is None


def test_invalid_lei_error_all_fields():
    e = InvalidLEIError(
        "bad lei", lei="INVALIDLEI", field="org_id_lei", reason="length"
    )
    assert e.lei == "INVALIDLEI"
    assert e.field == "org_id_lei"
    assert e.reason == "length"


def test_invalid_lei_error_defaults():
    e = InvalidLEIError("bad lei", lei="INVALIDLEI")
    assert e.field is None
    assert e.reason is None


def test_missing_required_field_error_all_fields():
    e = MissingRequiredFieldError(
        "missing",
        field="account_owner_name",
        row_number=3,
        required_fields=["account_owner_name", "msg_id"],
    )
    assert e.field == "account_owner_name"
    assert e.row_number == 3
    assert "msg_id" in e.required_fields


def test_missing_required_field_error_defaults():
    e = MissingRequiredFieldError("missing", field="msg_id")
    assert e.row_number is None
    assert e.required_fields == []


def test_can_catch_subclass_as_base():
    try:
        raise InvalidIBANError("x", iban="XX")
    except Acmt001Error as caught:
        assert isinstance(caught, InvalidIBANError)
