"""Tests for the high-level service facade (acmt001.services)."""

import json

import pytest

from acmt001 import services
from acmt001.constants import valid_xml_types


class TestListMessageTypes:
    def test_lists_all_thirty_four_types(self):
        result = services.list_message_types()
        assert len(result) == len(valid_xml_types) == 34
        assert {r["message_type"] for r in result} == set(valid_xml_types)

    def test_entries_have_name(self):
        first = services.list_message_types()[0]
        assert first["message_type"] == "acmt.001.001.08"
        assert first["name"] == "Account Opening Instruction"


class TestSchema:
    def test_get_input_schema(self):
        schema = services.get_input_schema("acmt.007.001.05")
        assert schema["type"] == "object"
        assert "msg_id" in schema["properties"]

    def test_get_input_schema_invalid_type(self):
        with pytest.raises(ValueError):
            services.get_input_schema("acmt.999.001.99")

    def test_get_required_fields(self):
        required = services.get_required_fields("acmt.007.001.05")
        assert "msg_id" in required
        assert "account_servicer_bic" in required


class TestValidateIdentifier:
    @pytest.mark.parametrize(
        "kind,value",
        [
            ("iban", "GB29NWBK60161331926819"),
            ("bic", "NWBKGB2LXXX"),
            ("lei", "5493001KJTIIGC8Y1R12"),
            ("IBAN", "GB29NWBK60161331926819"),  # case-insensitive
        ],
    )
    def test_valid(self, kind, value):
        result = services.validate_identifier(kind, value)
        assert result["valid"] is True
        assert result["kind"] == kind.lower()
        assert result["value"] == value

    @pytest.mark.parametrize(
        "kind,value",
        [
            ("iban", "GB00NWBK60161331926819"),
            ("bic", "INVALID"),
            ("lei", "5493001KJTIIGC8Y1R13"),
        ],
    )
    def test_invalid(self, kind, value):
        assert services.validate_identifier(kind, value)["valid"] is False

    def test_unsupported_kind(self):
        with pytest.raises(ValueError):
            services.validate_identifier("swift", "NWBKGB2LXXX")


class TestValidateRecords:
    def test_valid_records(self, sample_record):
        report = services.validate_records("acmt.007.001.05", [sample_record])
        assert report["valid"] is True
        assert report["total"] == 1
        assert report["valid_count"] == 1
        assert report["errors"] == []

    def test_invalid_records(self):
        report = services.validate_records(
            "acmt.007.001.05", [{"msg_id": "X"}]
        )
        assert report["valid"] is False
        assert report["valid_count"] == 0
        assert len(report["errors"]) >= 1
        assert {"row", "path", "message"} <= set(report["errors"][0])


class TestGenerate:
    def test_generate_all_types(self, sample_record):
        for mt in valid_xml_types:
            xml = services.generate(mt, [sample_record])
            assert xml.startswith("<?xml")
            assert mt in xml  # namespace carries the message type

    def test_generate_invalid_type(self, sample_record):
        with pytest.raises(ValueError):
            services.generate("acmt.999.001.99", [sample_record])

    def test_generate_empty(self):
        with pytest.raises(ValueError):
            services.generate("acmt.007.001.05", [])


class TestLoadOpenapi:
    def test_default_app(self):
        doc = json.loads(services.load_openapi())
        assert doc["openapi"].startswith("3.")
        assert "/api/health" in doc["paths"]

    def test_explicit_app(self):
        from acmt001.api.app import app

        doc = json.loads(services.load_openapi(app))
        assert "paths" in doc
