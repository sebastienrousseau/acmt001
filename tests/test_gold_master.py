"""End-to-end gold master tests across every acmt message type.

Loads the single complete record from
``tests/gold_master/account_opening_full.json`` and generates XML for all
34 supported acmt message types, asserting each is XSD-valid and carries
the correct ISO 20022 namespace.
"""

import json
from pathlib import Path

import pytest

from acmt001.constants import TEMPLATES_DIR, valid_xml_types
from acmt001.xml.generate_xml import generate_xml_string

GOLD = Path(__file__).resolve().parent / "gold_master"


def _full_record() -> list[dict]:
    return json.loads((GOLD / "account_opening_full.json").read_text())


def _tpl(version: str) -> str:
    return str(TEMPLATES_DIR / version / "template.xml")


def _xsd(version: str) -> str:
    return str(TEMPLATES_DIR / version / f"{version}.xsd")


@pytest.mark.integration
class TestGoldMasterAllTypes:
    """Every acmt type must produce XSD-valid XML from the full record."""

    @pytest.mark.parametrize("version", valid_xml_types)
    def test_generates_valid_xml(self, version):
        xml = generate_xml_string(
            _full_record(), version, _tpl(version), _xsd(version)
        )
        assert xml.strip()

    @pytest.mark.parametrize("version", valid_xml_types)
    def test_contains_namespace(self, version):
        xml = generate_xml_string(
            _full_record(), version, _tpl(version), _xsd(version)
        )
        assert f"urn:iso:std:iso:20022:tech:xsd:{version}" in xml

    @pytest.mark.parametrize("version", valid_xml_types)
    def test_msg_id_propagates(self, version):
        xml = generate_xml_string(
            _full_record(), version, _tpl(version), _xsd(version)
        )
        assert "ACMT-MSG-0001" in xml


@pytest.mark.integration
class TestGoldMasterCoverage:
    """Sanity checks on the gold master corpus."""

    def test_all_34_types_present(self):
        assert len(valid_xml_types) == 34

    def test_full_record_is_single_dict(self):
        data = _full_record()
        assert isinstance(data, list)
        assert len(data) == 1
        assert isinstance(data[0], dict)

    def test_account_opening_request(self):
        version = "acmt.007.001.05"
        xml = generate_xml_string(
            _full_record(), version, _tpl(version), _xsd(version)
        )
        assert f"urn:iso:std:iso:20022:tech:xsd:{version}" in xml
