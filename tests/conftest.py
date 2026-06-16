"""Shared fixtures for the acmt001 test suite."""

import json
from pathlib import Path

import pytest

from acmt001.constants import TEMPLATES_DIR

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GOLD = Path(__file__).resolve().parent / "gold_master"


@pytest.fixture
def sample_record() -> dict:
    """A complete account record satisfying every acmt message type."""
    data = json.loads((GOLD / "account_opening_full.json").read_text())
    return dict(data[0])


@pytest.fixture
def sample_records(sample_record) -> list:
    """Two account records (for batch/list scenarios)."""
    second = dict(sample_record)
    second["msg_id"] = "ACMT-MSG-0002"
    second["process_id"] = "ACMT-PRC-0002"
    second["account_id"] = "DE89370400440532013000"
    return [dict(sample_record), second]


@pytest.fixture
def template_path():
    """Return a callable mapping a message type to its template.xml path."""

    def _path(message_type: str) -> str:
        return str(TEMPLATES_DIR / message_type / "template.xml")

    return _path


@pytest.fixture
def schema_path():
    """Return a callable mapping a message type to its XSD path."""

    def _path(message_type: str) -> str:
        return str(TEMPLATES_DIR / message_type / f"{message_type}.xsd")

    return _path


@pytest.fixture
def work_dir(tmp_path, monkeypatch):
    """Chdir into an isolated temp directory (process_files writes to CWD)."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def staged_message(work_dir, template_path, schema_path):
    """Copy a message's template + XSD into the work dir and return paths.

    Returns a callable: stage(message_type) -> (template_name, xsd_name).
    """
    import shutil

    def _stage(message_type: str):
        tpl = work_dir / "template.xml"
        xsd = work_dir / f"{message_type}.xsd"
        shutil.copy(template_path(message_type), tpl)
        shutil.copy(schema_path(message_type), xsd)
        return str(tpl), str(xsd)

    return _stage
