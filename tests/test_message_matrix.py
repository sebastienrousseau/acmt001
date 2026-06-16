"""Schema-driven matrix tests across all 34 acmt message types.

Parametrized over ``acmt001.constants.valid_xml_types``: asserts each type
ships a template, an XSD, and a JSON schema, and that generation succeeds
from the gold master full record.
"""

import json
from pathlib import Path

import pytest

from acmt001.constants import SCHEMAS_DIR, TEMPLATES_DIR, valid_xml_types
from acmt001.xml.generate_xml import generate_xml_string

GOLD = Path(__file__).resolve().parent / "gold_master"


def _full_record() -> list[dict]:
    return json.loads((GOLD / "account_opening_full.json").read_text())


def _tpl(version: str) -> Path:
    return TEMPLATES_DIR / version / "template.xml"


def _xsd(version: str) -> Path:
    return TEMPLATES_DIR / version / f"{version}.xsd"


def _schema(version: str) -> Path:
    return SCHEMAS_DIR / f"{version}.schema.json"


@pytest.mark.message_compat
class TestMessageMatrixFiles:
    """Each message type must ship its template, XSD, and JSON schema."""

    @pytest.mark.parametrize("version", valid_xml_types)
    def test_template_exists(self, version):
        assert _tpl(version).is_file(), f"missing template for {version}"

    @pytest.mark.parametrize("version", valid_xml_types)
    def test_xsd_exists(self, version):
        assert _xsd(version).is_file(), f"missing xsd for {version}"

    @pytest.mark.parametrize("version", valid_xml_types)
    def test_schema_exists(self, version):
        assert _schema(version).is_file(), f"missing schema for {version}"

    @pytest.mark.parametrize("version", valid_xml_types)
    def test_schema_is_valid_json(self, version):
        data = json.loads(_schema(version).read_text())
        assert isinstance(data, dict)


@pytest.mark.message_compat
class TestMessageMatrixGeneration:
    """Each message type must generate XSD-valid XML."""

    @pytest.mark.parametrize("version", valid_xml_types)
    def test_generation_succeeds(self, version):
        xml = generate_xml_string(
            _full_record(), version, str(_tpl(version)), str(_xsd(version))
        )
        assert xml.strip().startswith("<")
        assert f"urn:iso:std:iso:20022:tech:xsd:{version}" in xml
