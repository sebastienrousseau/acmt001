"""Full CLI coverage tests for acmt001/cli/cli.py.

Exercises the helper functions and the Click command directly to drive
line + branch coverage of the CLI module.
"""

import configparser
import logging
import os
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from acmt001.cli.cli import (
    _configure_logging,
    _generate_xml_files,
    _load_configuration,
    _validate_account_data,
    _validate_schema,
    _working_directory,
    main,
)
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
def json_data(tmp_path, monkeypatch):
    """A valid account JSON file inside the (chdir'd) work dir."""
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "accounts.json"
    path.write_text(
        (GOLD / "account_opening_full.json").read_text(), encoding="utf-8"
    )
    return str(path)


def _tpl(version=VERSION):
    return str(TEMPLATES_DIR / version / "template.xml")


def _xsd(version=VERSION):
    return str(TEMPLATES_DIR / version / f"{version}.xsd")


class TestConfigureLogging:
    """Logging configuration helper."""

    def test_verbose_sets_debug(self):
        logger = _configure_logging(True)
        assert logger.level == logging.DEBUG

    def test_non_verbose_sets_info(self):
        logger = _configure_logging(False)
        assert logger.level == logging.INFO


class TestValidateSchema:
    """XSD schema load helper."""

    def test_valid_schema_loads(self):
        logger = _configure_logging(False)
        _validate_schema(logger, _tpl(), _xsd(), VERSION)

    def test_invalid_schema_exits(self):
        logger = _configure_logging(False)
        with pytest.raises(SystemExit) as exc_info:
            _validate_schema(
                logger, "template.xml", "/nonexistent/schema.xsd", VERSION
            )
        assert exc_info.value.code == 1


class TestValidateAccountData:
    """Account data validation helper."""

    def test_valid_data(self, json_data):
        logger = _configure_logging(False)
        count = _validate_account_data(logger, json_data, VERSION)
        assert count >= 1

    def test_invalid_data_exits(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        logger = _configure_logging(False)
        with pytest.raises(SystemExit) as exc_info:
            _validate_account_data(
                logger, str(tmp_path / "missing.csv"), VERSION
            )
        assert exc_info.value.code == 1

    def test_parquet_hint(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        logger = _configure_logging(False)
        with pytest.raises(SystemExit):
            _validate_account_data(
                logger, str(tmp_path / "data.parquet"), VERSION
            )

    def test_json_hint(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        logger = _configure_logging(False)
        path = tmp_path / "bad.json"
        path.write_text("{invalid", encoding="utf-8")
        with pytest.raises(SystemExit):
            _validate_account_data(logger, str(path), VERSION)


class TestWorkingDirectory:
    """Working directory context manager."""

    def test_changes_and_restores(self, tmp_path):
        original = os.getcwd()
        with _working_directory(str(tmp_path)):
            assert os.path.realpath(os.getcwd()) == os.path.realpath(
                str(tmp_path)
            )
        assert os.getcwd() == original


class TestGenerateXmlFiles:
    """XML generation helper."""

    def test_generation_success(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        tpl = tmp_path / "template.xml"
        xsd = tmp_path / f"{VERSION}.xsd"
        shutil.copy(_tpl(), tpl)
        shutil.copy(_xsd(), xsd)
        data = tmp_path / "accounts.json"
        data.write_text(
            (GOLD / "account_opening_full.json").read_text(), encoding="utf-8"
        )
        logger = _configure_logging(False)
        _generate_xml_files(
            logger, VERSION, str(tpl), str(xsd), str(data), None, False
        )
        assert (tmp_path / f"{VERSION}.xml").exists()

    def test_generation_failure_exits(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        logger = _configure_logging(False)
        tpl = tmp_path / "bad.xml"
        tpl.write_text("bad", encoding="utf-8")
        xsd = tmp_path / "bad.xsd"
        xsd.write_text("bad", encoding="utf-8")
        data = tmp_path / "accounts.json"
        data.write_text(
            (GOLD / "account_opening_full.json").read_text(), encoding="utf-8"
        )
        with pytest.raises(SystemExit) as exc_info:
            _generate_xml_files(
                logger, VERSION, str(tpl), str(xsd), str(data), None, False
            )
        assert exc_info.value.code == 1

    def test_generation_failure_verbose(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        logger = _configure_logging(True)
        tpl = tmp_path / "bad.xml"
        tpl.write_text("bad", encoding="utf-8")
        xsd = tmp_path / "bad.xsd"
        xsd.write_text("bad", encoding="utf-8")
        data = tmp_path / "accounts.json"
        data.write_text(
            (GOLD / "account_opening_full.json").read_text(), encoding="utf-8"
        )
        with pytest.raises(SystemExit):
            _generate_xml_files(
                logger, VERSION, str(tpl), str(xsd), str(data), None, True
            )

    def test_generation_with_output_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        tpl = out_dir / "template.xml"
        xsd = out_dir / f"{VERSION}.xsd"
        shutil.copy(_tpl(), tpl)
        shutil.copy(_xsd(), xsd)
        data = out_dir / "accounts.json"
        data.write_text(
            (GOLD / "account_opening_full.json").read_text(), encoding="utf-8"
        )
        logger = _configure_logging(False)
        _generate_xml_files(
            logger,
            VERSION,
            str(tpl),
            str(xsd),
            str(data),
            str(out_dir),
            False,
        )
        assert (out_dir / f"{VERSION}.xml").exists()


class TestLoadConfiguration:
    """Configuration file loading helper."""

    def test_no_config_file(self):
        t, s, d = _load_configuration(None, "t.xml", "s.xsd", "d.csv")
        assert (t, s, d) == ("t.xml", "s.xsd", "d.csv")

    def test_with_config_file(self, tmp_path):
        config = configparser.ConfigParser()
        config["Paths"] = {
            "xml_template_file_path": "custom_template.xml",
            "xsd_schema_file_path": "custom_schema.xsd",
            "data_file_path": "custom_data.csv",
        }
        config_path = tmp_path / "config.ini"
        with open(config_path, "w", encoding="utf-8") as f:
            config.write(f)
        t, s, d = _load_configuration(
            str(config_path), "default.xml", "default.xsd", "default.csv"
        )
        assert t == "custom_template.xml"
        assert s == "custom_schema.xsd"
        assert d == "custom_data.csv"

    def test_with_config_no_paths_section(self, tmp_path):
        cfg = tmp_path / "empty.ini"
        cfg.write_text("[Other]\nkey = value\n", encoding="utf-8")
        t, s, d = _load_configuration(str(cfg), "t.xml", "s.xsd", "d.csv")
        assert t == "t.xml"
        assert s == "s.xsd"
        assert d == "d.csv"


class TestMainCli:
    """The Click command, invoked through CliRunner."""

    def test_dry_run_validates_only(self, json_data):
        runner = CliRunner()
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
                json_data,
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert (
            "validations passed" in result.output.lower()
            or "dry" in result.output.lower()
        )

    def test_verbose_dry_run(self, json_data):
        runner = CliRunner()
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
                json_data,
                "--dry-run",
                "--verbose",
            ],
        )
        assert result.exit_code == 0
        assert "Verbose" in result.output

    def test_generate_success(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            shutil.copy(_tpl(), "template.xml")
            shutil.copy(_xsd(), f"{VERSION}.xsd")
            Path("accounts.json").write_text(
                (GOLD / "account_opening_full.json").read_text(),
                encoding="utf-8",
            )
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

    def test_generate_with_output_dir(self):
        runner = CliRunner()
        with runner.isolated_filesystem() as fs:
            out = Path(fs) / "out"
            out.mkdir()
            tpl = out / "template.xml"
            xsd = out / f"{VERSION}.xsd"
            data = out / "accounts.json"
            shutil.copy(_tpl(), tpl)
            shutil.copy(_xsd(), xsd)
            data.write_text(
                (GOLD / "account_opening_full.json").read_text(),
                encoding="utf-8",
            )
            # Absolute paths survive the chdir into the output directory.
            result = runner.invoke(
                main,
                [
                    "-t",
                    VERSION,
                    "-m",
                    str(tpl),
                    "-s",
                    str(xsd),
                    "-d",
                    str(data),
                    "-o",
                    str(out),
                ],
            )
            assert result.exit_code == 0
            assert (out / f"{VERSION}.xml").exists()

    def test_config_override(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            shutil.copy(_tpl(), "template.xml")
            shutil.copy(_xsd(), f"{VERSION}.xsd")
            Path("accounts.json").write_text(
                (GOLD / "account_opening_full.json").read_text(),
                encoding="utf-8",
            )
            config = configparser.ConfigParser()
            config["Paths"] = {
                "xml_template_file_path": "template.xml",
                "xsd_schema_file_path": f"{VERSION}.xsd",
                "data_file_path": "accounts.json",
            }
            with open("config.ini", "w", encoding="utf-8") as f:
                config.write(f)
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
                    "-c",
                    "config.ini",
                    "--dry-run",
                ],
            )
            assert result.exit_code == 0

    def test_schema_load_failure_exits_1(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            shutil.copy(_tpl(), "template.xml")
            # A malformed XSD so _validate_schema fails.
            Path("schema.xsd").write_text("not a schema", encoding="utf-8")
            Path("accounts.json").write_text(
                (GOLD / "account_opening_full.json").read_text(),
                encoding="utf-8",
            )
            result = runner.invoke(
                main,
                [
                    "-t",
                    VERSION,
                    "-m",
                    "template.xml",
                    "-s",
                    "schema.xsd",
                    "-d",
                    "accounts.json",
                ],
            )
            assert result.exit_code == 1


class TestMainCliErrors:
    """Argument / file validation errors."""

    def test_help_flag(self):
        result = CliRunner().invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "acmt" in result.output.lower()

    def test_missing_required_args(self):
        result = CliRunner().invoke(main, [])
        assert result.exit_code == 2

    def test_invalid_message_type_exit_2(self):
        result = CliRunner().invoke(main, ["-t", "acmt.999.001.99"])
        assert result.exit_code == 2

    def test_missing_data_file(self):
        result = CliRunner().invoke(
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

    def test_missing_template_file(self, json_data):
        result = CliRunner().invoke(
            main,
            [
                "-t",
                VERSION,
                "-m",
                "/nonexistent/template.xml",
                "-s",
                _xsd(),
                "-d",
                json_data,
            ],
        )
        assert result.exit_code == 2
