"""Tests for validation/service.py — ValidationService orchestrator."""

import csv

import pytest

from acmt001.constants import TEMPLATES_DIR
from acmt001.exceptions import ConfigurationError
from acmt001.validation.service import (
    ValidationConfig,
    ValidationReport,
    ValidationResult,
    ValidationService,
)

VERSION = "acmt.007.001.05"

REQUIRED_FIELDS = [
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


@pytest.fixture()
def service():
    return ValidationService()


@pytest.fixture()
def valid_csv_file(tmp_path, monkeypatch):
    """Create a valid CSV data file inside the CWD (path traversal safe)."""
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "accounts.csv"
    row = {
        "msg_id": "ACMT-MSG-0001",
        "creation_date_time": "2026-01-15T10:30:00",
        "process_id": "ACMT-PRC-0001",
        "account_id": "DE89370400440532013000",
        "account_currency": "EUR",
        "account_name": "Operating Account",
        "account_type_cd": "CACC",
        "account_servicer_bic": "DEUTDEFF",
        "account_owner_name": "Acme Corp",
        "account_owner_country": "DE",
        "org_full_legal_name": "Acme Corporation GmbH",
        "org_id_lei": "5493001KJTIIGC8Y1R12",
    }
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_FIELDS)
        writer.writeheader()
        writer.writerow(row)
    return str(path)


class TestValidateMessageType:
    def test_valid_type(self, service):
        result = service.validate_message_type(VERSION)
        assert result.is_valid

    def test_invalid_type(self, service):
        result = service.validate_message_type("acmt.007.001.99")
        assert not result.is_valid
        assert "Invalid" in result.error
        assert result.details is not None

    def test_empty_type(self, service):
        result = service.validate_message_type("")
        assert not result.is_valid
        assert "required" in result.error.lower()
        assert result.field == "xml_message_type"


class TestValidateTemplate:
    def test_valid_template(self, service):
        tpl = str(TEMPLATES_DIR / VERSION / "template.xml")
        result = service.validate_template(tpl)
        assert result.is_valid

    def test_missing_template(self, service):
        result = service.validate_template("/nonexistent/template.xml")
        assert not result.is_valid
        assert "does not exist" in result.error

    def test_empty_template_path(self, service):
        result = service.validate_template("")
        assert not result.is_valid
        assert "required" in result.error.lower()


class TestValidateSchema:
    def test_valid_schema(self, service):
        xsd = str(TEMPLATES_DIR / VERSION / f"{VERSION}.xsd")
        result = service.validate_schema(xsd)
        assert result.is_valid

    def test_missing_schema(self, service):
        result = service.validate_schema("/nonexistent/schema.xsd")
        assert not result.is_valid
        assert "does not exist" in result.error

    def test_empty_schema_path(self, service):
        result = service.validate_schema("")
        assert not result.is_valid
        assert "required" in result.error.lower()


class TestValidateDataSource:
    def test_valid_data_file(self, service, valid_csv_file):
        result = service.validate_data_source(valid_csv_file)
        assert result.is_valid

    def test_missing_data_file(self, service):
        result = service.validate_data_source("/nonexistent/data.csv")
        assert not result.is_valid
        assert "does not exist" in result.error

    def test_empty_data_path(self, service):
        result = service.validate_data_source("")
        assert not result.is_valid
        assert "required" in result.error.lower()

    def test_directory_instead_of_file(self, service, tmp_path):
        result = service.validate_data_source(str(tmp_path))
        assert not result.is_valid
        assert "directory" in result.error.lower()


class TestValidateTemplateSchemaCompatibility:
    def test_schema_validation_error_branch(self, service, monkeypatch):
        """A SchemaValidationError from validate_via_xsd is surfaced."""
        from acmt001.exceptions import SchemaValidationError
        from acmt001.validation import service as service_module

        def _raise(*_args, **_kwargs):
            raise SchemaValidationError("schema mismatch")

        monkeypatch.setattr(service_module, "validate_via_xsd", _raise)
        result = service.validate_template_schema_compatibility(
            "template.xml", "schema.xsd"
        )
        assert not result.is_valid
        assert "Schema validation failed" in result.error
        assert result.details is not None

    def test_unexpected_error_branch(self, service, monkeypatch):
        """Any other exception is caught by the broad handler."""
        from acmt001.validation import service as service_module

        def _raise(*_args, **_kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(service_module, "validate_via_xsd", _raise)
        result = service.validate_template_schema_compatibility(
            "template.xml", "schema.xsd"
        )
        assert not result.is_valid
        assert "Unexpected schema validation error" in result.error

    def test_valid_compatibility(self, service):
        """A well-formed call returns a valid result."""
        tpl = str(TEMPLATES_DIR / VERSION / "template.xml")
        xsd = str(TEMPLATES_DIR / VERSION / f"{VERSION}.xsd")
        result = service.validate_template_schema_compatibility(tpl, xsd)
        assert result.is_valid


class TestValidateDataContent:
    def test_valid_data_content(self, service, valid_csv_file):
        result = service.validate_data_content(valid_csv_file)
        assert result.is_valid

    def test_nonexistent_file(self, service):
        result = service.validate_data_content("/nonexistent/file.csv")
        assert not result.is_valid

    def test_invalid_content_missing_required(self, service, tmp_path, monkeypatch):
        """A CSV missing required columns fails content validation."""
        monkeypatch.chdir(tmp_path)
        path = tmp_path / "bad.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["foo", "bar"])
            writer.writerow(["1", "2"])
        result = service.validate_data_content(str(path))
        assert not result.is_valid
        assert "data validation" in result.error.lower()

    def test_value_error_branch(self, service, monkeypatch):
        """A ValueError from the loader is reported with the field set."""
        from acmt001.validation import service as service_module

        def _raise(*_args, **_kwargs):
            raise ValueError("bad value")

        monkeypatch.setattr(service_module, "load_account_data", _raise)
        result = service.validate_data_content("data.csv")
        assert not result.is_valid
        assert result.field == "data_file_path"

    def test_data_source_error_branch(self, service, monkeypatch):
        """A DataSourceError from the loader is reported with the field set."""
        from acmt001.exceptions import DataSourceError
        from acmt001.validation import service as service_module

        def _raise(*_args, **_kwargs):
            raise DataSourceError("source unavailable")

        monkeypatch.setattr(service_module, "load_account_data", _raise)
        result = service.validate_data_content("data.csv")
        assert not result.is_valid
        assert result.field == "data_file_path"
        assert "Data source error" in result.error

    def test_unexpected_error_branch(self, service, monkeypatch):
        """An unexpected exception from the loader hits the broad handler."""
        from acmt001.validation import service as service_module

        def _raise(*_args, **_kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(service_module, "load_account_data", _raise)
        result = service.validate_data_content("data.csv")
        assert not result.is_valid
        assert "Unexpected data validation error" in result.error


class TestValidateAll:
    def _config(self, valid_csv_file, **overrides):
        params = {
            "xml_message_type": VERSION,
            "xml_template_file_path": str(
                TEMPLATES_DIR / VERSION / "template.xml"
            ),
            "xsd_schema_file_path": str(
                TEMPLATES_DIR / VERSION / f"{VERSION}.xsd"
            ),
            "data_file_path": valid_csv_file,
        }
        params.update(overrides)
        return ValidationConfig(**params)

    def test_all_valid(self, service, valid_csv_file):
        report = service.validate_all(self._config(valid_csv_file))
        assert report.is_valid
        assert report.errors == []
        assert report.results["data_content"].is_valid

    def test_invalid_message_type(self, service, valid_csv_file):
        config = self._config(
            valid_csv_file, xml_message_type="acmt.007.001.99"
        )
        report = service.validate_all(config)
        assert not report.is_valid
        assert len(report.errors) > 0

    def test_missing_template(self, service, valid_csv_file):
        config = self._config(
            valid_csv_file, xml_template_file_path="/nonexistent/template.xml"
        )
        report = service.validate_all(config)
        assert not report.is_valid

    def test_missing_schema(self, service, valid_csv_file):
        config = self._config(
            valid_csv_file, xsd_schema_file_path="/nonexistent/schema.xsd"
        )
        report = service.validate_all(config)
        assert not report.is_valid

    def test_missing_data_skips_content(self, service):
        config = self._config("/nonexistent/data.csv")
        report = service.validate_all(config)
        assert not report.is_valid
        assert "data_content" not in report.results  # Skipped

    def test_invalid_data_content_fails(self, service, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        path = tmp_path / "bad.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["foo"])
            writer.writerow(["x"])
        report = service.validate_all(self._config(str(path)))
        assert not report.is_valid
        assert "data_content" in report.results
        assert not report.results["data_content"].is_valid

    def test_none_config_raises(self, service):
        with pytest.raises(ConfigurationError):
            service.validate_all(None)


class TestValidationDataclasses:
    def test_validation_result_defaults(self):
        r = ValidationResult(is_valid=True)
        assert r.error is None
        assert r.field is None
        assert r.details is None

    def test_validation_report_defaults(self):
        r = ValidationReport(is_valid=True)
        assert r.errors == []
        assert r.results == {}

    def test_validation_config(self):
        c = ValidationConfig(
            xml_message_type=VERSION,
            xml_template_file_path="t.xml",
            xsd_schema_file_path="s.xsd",
            data_file_path="d.csv",
        )
        assert c.pre_validate is True
