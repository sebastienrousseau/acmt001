"""Tests for acmt001.api.models (Pydantic request/response models)."""

import os
import tempfile

import pytest
from pydantic import ValidationError as PydanticValidationError

from acmt001.api.models import (
    DataSourceType,
    GenerateXMLRequest,
    GenerateXMLResponse,
    HealthResponse,
    JobStatusResponse,
    MessageType,
    ValidationError,
    ValidationRequest,
    ValidationResponse,
)

_TMPDIR = tempfile.gettempdir()


class TestMessageType:
    def test_has_21_members(self):
        assert len(MessageType) == 21

    def test_values_format(self):
        for mt in MessageType:
            assert mt.value.startswith("acmt.")

    def test_account_opening_request(self):
        assert MessageType.ACMT_007_05.value == "acmt.007.001.05"

    def test_identification_report(self):
        assert MessageType.ACMT_024_04.value == "acmt.024.001.04"


class TestDataSourceType:
    def test_csv(self):
        assert DataSourceType.CSV.value == "csv"

    def test_sqlite(self):
        assert DataSourceType.SQLITE.value == "sqlite"

    def test_json(self):
        assert DataSourceType.JSON.value == "json"

    def test_jsonl(self):
        assert DataSourceType.JSONL.value == "jsonl"

    def test_parquet(self):
        assert DataSourceType.PARQUET.value == "parquet"


class TestValidationRequest:
    def test_create(self):
        fp = os.path.join(_TMPDIR, "data.csv")
        req = ValidationRequest(
            data_source=DataSourceType.CSV,
            file_path=fp,
            message_type=MessageType.ACMT_007_05,
        )
        assert req.file_path == fp
        assert req.message_type == MessageType.ACMT_007_05

    def test_default_message_type(self):
        req = ValidationRequest(
            data_source=DataSourceType.JSON,
            file_path=os.path.join(_TMPDIR, "data.json"),
        )
        assert req.message_type == MessageType.ACMT_007_05

    def test_invalid_data_source_rejected(self):
        with pytest.raises(PydanticValidationError):
            ValidationRequest(data_source="bogus", file_path="x")


class TestGenerateXMLRequest:
    def test_create_with_defaults(self):
        fp = os.path.join(_TMPDIR, "data.csv")
        req = GenerateXMLRequest(data_source=DataSourceType.CSV, file_path=fp)
        assert req.validate_only is False
        assert req.output_dir is None

    def test_validate_only(self):
        fp = os.path.join(_TMPDIR, "data.csv")
        req = GenerateXMLRequest(
            data_source=DataSourceType.CSV,
            file_path=fp,
            validate_only=True,
            output_dir=_TMPDIR,
        )
        assert req.validate_only is True
        assert req.output_dir == _TMPDIR


class TestValidationError:
    def test_create(self):
        err = ValidationError(
            field="$.account_id", message="bad", value="X"
        )
        assert err.field == "$.account_id"
        assert err.message == "bad"
        assert err.value == "X"


class TestValidationResponse:
    def test_invalid_rows_computed_when_provided(self):
        # The after-validator recomputes invalid_rows from total - valid
        # when the field is supplied explicitly.
        resp = ValidationResponse(
            is_valid=False, total_rows=10, valid_rows=7, invalid_rows=0
        )
        assert resp.invalid_rows == 3

    def test_invalid_rows_default(self):
        resp = ValidationResponse(
            is_valid=False, total_rows=10, valid_rows=7
        )
        assert resp.invalid_rows == 0

    def test_all_valid(self):
        resp = ValidationResponse(
            is_valid=True, total_rows=5, valid_rows=5, invalid_rows=0
        )
        assert resp.invalid_rows == 0


class TestGenerateXMLResponse:
    def test_success(self):
        fp = os.path.join(_TMPDIR, "out.xml")
        resp = GenerateXMLResponse(success=True, message="OK", file_path=fp)
        assert resp.success
        assert resp.file_path == fp
        assert resp.validation_errors == []

    def test_failure_with_errors(self):
        resp = GenerateXMLResponse(
            success=False,
            message="bad",
            validation_errors=[
                ValidationError(field="$.x", message="m", value=None)
            ],
        )
        assert resp.success is False
        assert len(resp.validation_errors) == 1


class TestJobStatusResponse:
    def test_create(self):
        resp = JobStatusResponse(
            job_id="abc",
            status="pending",
            message="Job is pending",
            progress_percent=0,
        )
        assert resp.job_id == "abc"
        assert resp.status == "pending"
        assert resp.result is None


class TestHealthResponse:
    def test_create(self):
        resp = HealthResponse(
            status="healthy", version="0.0.1", message="running"
        )
        assert resp.status == "healthy"
        assert resp.version == "0.0.1"
