"""Tests for acmt001.constants module."""

from acmt001.constants import (
    APP_DESCRIPTION,
    APP_NAME,
    BASE_DIR,
    SCHEMAS_DIR,
    TEMPLATES_DIR,
    VERSION,
    message_names,
    valid_xml_types,
)


def test_valid_xml_types_has_21_entries():
    assert len(valid_xml_types) == 21


def test_valid_xml_types_format():
    for t in valid_xml_types:
        assert t.startswith("acmt.")


def test_valid_xml_types_unique():
    assert len(set(valid_xml_types)) == len(valid_xml_types)


def test_app_name():
    assert APP_NAME == "Acmt001"


def test_app_description_mentions_iso():
    assert "ISO 20022" in APP_DESCRIPTION


def test_version():
    assert VERSION == "0.0.1"


def test_base_dir_exists():
    assert BASE_DIR.exists()


def test_schemas_dir():
    assert SCHEMAS_DIR == BASE_DIR / "schemas"


def test_templates_dir():
    assert TEMPLATES_DIR == BASE_DIR / "templates"


def test_message_names_cover_every_type():
    assert set(message_names) == set(valid_xml_types)


def test_message_names_are_human_readable():
    for name in message_names.values():
        assert isinstance(name, str) and name
