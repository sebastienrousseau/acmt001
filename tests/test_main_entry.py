"""Tests for the programmatic entry point in acmt001/__main__.py."""

import shutil
from pathlib import Path

import pytest

from acmt001.__main__ import cli as cli_reexport
from acmt001.__main__ import main
from acmt001.cli.cli import main as cli_main
from acmt001.constants import TEMPLATES_DIR

GOLD = Path(__file__).resolve().parent / "gold_master"
VERSION = "acmt.007.001.05"


def _tpl(version=VERSION):
    return str(TEMPLATES_DIR / version / "template.xml")


def _xsd(version=VERSION):
    return str(TEMPLATES_DIR / version / f"{version}.xsd")


@pytest.fixture()
def staged(tmp_path, monkeypatch):
    """Stage template + xsd + data inside the chdir'd work dir."""
    monkeypatch.chdir(tmp_path)
    tpl = tmp_path / "template.xml"
    xsd = tmp_path / f"{VERSION}.xsd"
    shutil.copy(_tpl(), tpl)
    shutil.copy(_xsd(), xsd)
    data = tmp_path / "accounts.json"
    data.write_text(
        (GOLD / "account_opening_full.json").read_text(), encoding="utf-8"
    )
    return tmp_path, str(tpl), str(xsd), str(data)


class TestReexport:
    """The module re-exports the Click command as ``cli``."""

    def test_cli_is_click_command(self):
        assert cli_reexport is cli_main


class TestMainMissingArgs:
    """Early exits when required arguments are missing."""

    def test_no_message_type(self):
        with pytest.raises(SystemExit) as exc_info:
            main(None, "template.xml", "schema.xsd", "data.csv")
        assert exc_info.value.code == 1

    def test_no_template(self):
        with pytest.raises(SystemExit) as exc_info:
            main(VERSION, None, "schema.xsd", "data.csv")
        assert exc_info.value.code == 1

    def test_no_schema(self):
        with pytest.raises(SystemExit) as exc_info:
            main(VERSION, "template.xml", None, "data.csv")
        assert exc_info.value.code == 1

    def test_no_data(self):
        with pytest.raises(SystemExit) as exc_info:
            main(VERSION, "template.xml", "schema.xsd", None)
        assert exc_info.value.code == 1


class TestMainValidation:
    """Validation-failure exits."""

    def test_invalid_message_type(self, staged):
        _, tpl, xsd, data = staged
        with pytest.raises(SystemExit) as exc_info:
            main("acmt.999.001.99", tpl, xsd, data)
        assert exc_info.value.code == 1

    def test_nonexistent_template(self, staged):
        _, _, xsd, data = staged
        with pytest.raises(SystemExit) as exc_info:
            main(VERSION, "/nonexistent/template.xml", xsd, data)
        assert exc_info.value.code == 1


class TestMainDryRun:
    """Dry-run validates without generating XML."""

    def test_dry_run(self, staged):
        work_dir, tpl, xsd, data = staged
        main(VERSION, tpl, xsd, data, dry_run=True)
        assert not (work_dir / f"{VERSION}.xml").exists()


class TestMainGenerate:
    """Successful generation path."""

    def test_generate_xml(self, staged):
        work_dir, tpl, xsd, data = staged
        main(VERSION, tpl, xsd, data)
        assert (work_dir / f"{VERSION}.xml").exists()


class TestMainGenericException:
    """The broad except handler maps unexpected errors to exit code 1."""

    def test_process_files_raises(self, staged, monkeypatch):
        _, tpl, xsd, data = staged

        def _boom(*_a, **_k):
            raise RuntimeError("boom")

        # Validation passes, then process_files raises -> generic handler.
        monkeypatch.setattr("acmt001.__main__.process_files", _boom)
        with pytest.raises(SystemExit) as exc_info:
            main(VERSION, tpl, xsd, data)
        assert exc_info.value.code == 1
