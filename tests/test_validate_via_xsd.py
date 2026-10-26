"""Tests for acmt001.xml.validate_via_xsd (file + string variants, cache)."""

import pytest

from acmt001.xml.generate_xml import generate_xml_string
from acmt001.xml.validate_via_xsd import (
    _get_cached_schema,
    validate_via_xsd,
    validate_xml_string_via_xsd,
)

ENTITY_DOCUMENT = '<!DOCTYPE a [<!ENTITY e "x">]><a>&e;</a>'
# A year the XSD date types cannot hold: elementpath raises OverflowError
# for it instead of an XMLSchemaException (found by acmt001-mcp's fuzzer).
OVERFLOW_YEAR = "222222222026-01-15T10:30:00"


@pytest.fixture
def valid_xml(sample_record, template_path, schema_path):
    """Return (xml_string, xsd_path) for a valid acmt.001 document."""
    version = "acmt.001.001.08"
    xsd = schema_path(version)
    xml = generate_xml_string(
        [sample_record], version, template_path(version), xsd
    )
    return xml, xsd


@pytest.fixture
def overflow_xml(valid_xml):
    """Return (xml_string, xsd_path) whose CreDtTm year overflows."""
    xml, xsd = valid_xml
    start = xml.index("<CreDtTm>") + len("<CreDtTm>")
    end = xml.index("</CreDtTm>", start)
    return xml[:start] + OVERFLOW_YEAR + xml[end:], xsd


class TestValidateXmlStringViaXsd:
    def test_valid_xml_string(self, valid_xml):
        xml, xsd = valid_xml
        assert validate_xml_string_via_xsd(xml, xsd) is True

    def test_invalid_xml_string(self, schema_path):
        xsd = schema_path("acmt.001.001.08")
        assert (
            validate_xml_string_via_xsd("<invalid>xml</invalid>", xsd) is False
        )

    def test_malformed_xml_string(self, schema_path):
        xsd = schema_path("acmt.001.001.08")
        assert validate_xml_string_via_xsd("not xml at all <<<", xsd) is False

    def test_entity_declaration_is_invalid_not_raised(self, schema_path):
        """defusedxml refuses entity declarations; the answer is False."""
        xsd = schema_path("acmt.001.001.08")
        assert validate_xml_string_via_xsd(ENTITY_DOCUMENT, xsd) is False

    def test_invalid_xsd_path(self):
        assert (
            validate_xml_string_via_xsd("<root/>", "/nonexistent/schema.xsd")
            is False
        )

    def test_year_overflow_is_invalid_not_raised(self, overflow_xml):
        xml, xsd = overflow_xml
        assert validate_xml_string_via_xsd(xml, xsd) is False


class TestValidateViaXsd:
    def test_valid_xml_file(self, valid_xml, tmp_path):
        xml, xsd = valid_xml
        xml_file = tmp_path / "doc.xml"
        xml_file.write_text(xml, encoding="utf-8")
        assert validate_via_xsd(str(xml_file), xsd) is True

    def test_invalid_xml_file(self, schema_path, tmp_path):
        xsd = schema_path("acmt.001.001.08")
        xml_file = tmp_path / "bad.xml"
        xml_file.write_text("<invalid>not valid</invalid>", encoding="utf-8")
        assert validate_via_xsd(str(xml_file), xsd) is False

    def test_nonexistent_xml_file(self, schema_path):
        xsd = schema_path("acmt.001.001.08")
        assert validate_via_xsd("/nonexistent/file.xml", xsd) is False

    def test_nonexistent_xsd_file(self, tmp_path):
        xml_file = tmp_path / "doc.xml"
        xml_file.write_text("<root/>", encoding="utf-8")
        assert validate_via_xsd(str(xml_file), "/nonexistent/schema.xsd") is (
            False
        )

    def test_malformed_xml_file(self, schema_path, tmp_path):
        xsd = schema_path("acmt.001.001.08")
        xml_file = tmp_path / "malformed.xml"
        xml_file.write_text("not xml <<<", encoding="utf-8")
        assert validate_via_xsd(str(xml_file), xsd) is False

    def test_entity_declaration_in_file_is_invalid(
        self, schema_path, tmp_path
    ):
        xsd = schema_path("acmt.001.001.08")
        xml_file = tmp_path / "entity.xml"
        xml_file.write_text(ENTITY_DOCUMENT, encoding="utf-8")
        assert validate_via_xsd(str(xml_file), xsd) is False

    def test_year_overflow_in_file_is_invalid(self, overflow_xml, tmp_path):
        xml, xsd = overflow_xml
        xml_file = tmp_path / "overflow.xml"
        xml_file.write_text(xml, encoding="utf-8")
        assert validate_via_xsd(str(xml_file), xsd) is False


def test_generate_reports_year_overflow_as_validation_failure(
    sample_record, template_path, schema_path
):
    """The generator raises its usual RuntimeError, not OverflowError."""
    version = "acmt.001.001.08"
    record = dict(sample_record, creation_date_time=OVERFLOW_YEAR)
    with pytest.raises(RuntimeError, match="failed validation"):
        generate_xml_string(
            [record], version, template_path(version), schema_path(version)
        )


class TestSchemaCache:
    def test_cached_schema_returns_same_instance(self, schema_path):
        xsd = schema_path("acmt.001.001.08")
        first = _get_cached_schema(xsd)
        second = _get_cached_schema(xsd)
        assert first is second

    def test_cache_speeds_repeat_validation(self, valid_xml):
        xml, xsd = valid_xml
        # Prime the cache then validate again; both should succeed.
        assert validate_xml_string_via_xsd(xml, xsd) is True
        assert validate_xml_string_via_xsd(xml, xsd) is True
