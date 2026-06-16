"""CLI integration tests using Click's CliRunner.

End-to-end exercises of the ``acmt001`` command with template, XSD, and
data staged inside an isolated filesystem.
"""

import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from acmt001.cli.cli import main
from acmt001.constants import TEMPLATES_DIR
from acmt001.context.context import Context

GOLD = Path(__file__).resolve().parent / "gold_master"
VERSION = "acmt.007.001.05"


@pytest.fixture(autouse=True)
def reset_context():
    """Reset the Context singleton between CLI tests."""
    Context.instance = None
    yield
    Context.instance = None


@pytest.fixture()
def runner():
    return CliRunner()


def _tpl(version=VERSION):
    return str(TEMPLATES_DIR / version / "template.xml")


def _xsd(version=VERSION):
    return str(TEMPLATES_DIR / version / f"{version}.xsd")


def _stage(version=VERSION):
    """Stage template + xsd + data into the current isolated filesystem."""
    shutil.copy(_tpl(version), "template.xml")
    shutil.copy(_xsd(version), f"{version}.xsd")
    Path("accounts.json").write_text(
        (GOLD / "account_opening_full.json").read_text(), encoding="utf-8"
    )


class TestCliHelp:
    """Help output."""

    def test_help_flag(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "acmt" in result.output.lower() or "ISO 20022" in result.output

    def test_short_help(self, runner):
        result = runner.invoke(main, ["-h"])
        assert result.exit_code == 0


@pytest.mark.integration
class TestCliDryRun:
    """Dry-run mode."""

    def test_dry_run_validates_only(self, runner):
        with runner.isolated_filesystem():
            _stage()
            result = runner.invoke(
                main,
                [
                    "-t",
                    VERSION,
                    "-m",
                    "template.xml",
                    "-s",
                    f"{VERSION}.xsd",
                    "-d",
                    "accounts.json",
                    "--dry-run",
                ],
            )
            assert result.exit_code == 0
            assert "validations passed" in result.output.lower()
            assert not Path(f"{VERSION}.xml").exists()


@pytest.mark.integration
class TestCliGenerate:
    """XML generation."""

    def test_generate_xml(self, runner):
        with runner.isolated_filesystem():
            _stage()
            result = runner.invoke(
                main,
                [
                    "-t",
                    VERSION,
                    "-m",
                    "template.xml",
                    "-s",
                    f"{VERSION}.xsd",
                    "-d",
                    "accounts.json",
                ],
            )
            assert result.exit_code == 0
            assert Path(f"{VERSION}.xml").exists()

    def test_generate_verbose(self, runner):
        with runner.isolated_filesystem():
            _stage()
            result = runner.invoke(
                main,
                [
                    "-t",
                    VERSION,
                    "-m",
                    "template.xml",
                    "-s",
                    f"{VERSION}.xsd",
                    "-d",
                    "accounts.json",
                    "--verbose",
                ],
            )
            assert result.exit_code == 0


class TestCliErrors:
    """Error handling."""

    def test_missing_required_args(self, runner):
        result = runner.invoke(main, [])
        assert result.exit_code == 2

    def test_invalid_message_type(self, runner):
        result = runner.invoke(main, ["-t", "acmt.008.001.99"])
        assert result.exit_code == 2

    def test_missing_data_file(self, runner):
        result = runner.invoke(
            main,
            [
                "-t",
                VERSION,
                "-m",
                _tpl(),
                "-s",
                _xsd(),
                "-d",
                "/nonexistent/file.csv",
            ],
        )
        assert result.exit_code == 2
