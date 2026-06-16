"""Tests for acmt001.core.core — process_files orchestration and helpers."""

import json

import pytest

from acmt001.core.core import (
    _determine_data_source_type,
    _validate_inputs,
    process_files,
)
from acmt001.exceptions import XMLGenerationError


class TestDetermineDataSourceType:
    """Data source type detection covers every branch."""

    def test_list_type(self):
        assert _determine_data_source_type([{"a": 1}]) == "list"

    def test_dict_type(self):
        assert _determine_data_source_type({"a": 1}) == "dict"

    def test_csv_file(self):
        assert _determine_data_source_type("accounts.csv") == "csv"

    def test_json_file(self):
        assert _determine_data_source_type("data.json") == "json"

    def test_jsonl_file(self):
        assert _determine_data_source_type("data.jsonl") == "jsonl"

    def test_parquet_file(self):
        assert _determine_data_source_type("data.parquet") == "parquet"

    def test_sqlite_db_extension(self):
        assert _determine_data_source_type("accounts.db") == "sqlite"

    def test_sqlite_uri(self):
        assert _determine_data_source_type("sqlite:///data.db") == "sqlite"

    def test_unknown_file(self):
        assert _determine_data_source_type("file.txt") == "file"

    def test_unknown_type(self):
        assert _determine_data_source_type(42) == "unknown"


class TestValidateInputs:
    """Input validation branches for process_files."""

    def test_invalid_message_type_raises(self):
        with pytest.raises(
            XMLGenerationError, match="Invalid XML message type"
        ):
            _validate_inputs("acmt.999.001.01", "t.xml", "s.xsd")

    def test_missing_template_raises(self, staged_message, work_dir):
        _, xsd = staged_message("acmt.001.001.08")
        with pytest.raises(FileNotFoundError):
            _validate_inputs(
                "acmt.001.001.08", str(work_dir / "missing.xml"), xsd
            )

    def test_missing_schema_raises(self, staged_message, work_dir):
        tpl, _ = staged_message("acmt.001.001.08")
        with pytest.raises(FileNotFoundError):
            _validate_inputs(
                "acmt.001.001.08", tpl, str(work_dir / "missing.xsd")
            )

    def test_valid_inputs(self, staged_message):
        version = "acmt.001.001.08"
        tpl, xsd = staged_message(version)
        safe_tpl, safe_xsd = _validate_inputs(version, tpl, xsd)
        assert "template.xml" in safe_tpl
        assert version in safe_xsd


@pytest.mark.integration
class TestProcessFiles:
    """End-to-end process_files orchestration."""

    @pytest.mark.parametrize(
        "version",
        [
            "acmt.001.001.08",
            "acmt.007.001.05",
            "acmt.013.001.04",
            "acmt.022.001.04",
        ],
    )
    def test_process_files_with_list_data(
        self, version, sample_record, staged_message, work_dir
    ):
        tpl, xsd = staged_message(version)
        process_files(version, tpl, xsd, [sample_record])
        assert (work_dir / f"{version}.xml").exists()

    def test_process_files_with_dict_data(
        self, sample_record, staged_message, work_dir
    ):
        version = "acmt.001.001.08"
        tpl, xsd = staged_message(version)
        process_files(version, tpl, xsd, sample_record)
        assert (work_dir / f"{version}.xml").exists()

    def test_process_files_with_json_file(
        self, sample_record, staged_message, work_dir
    ):
        version = "acmt.001.001.08"
        tpl, xsd = staged_message(version)
        data_file = work_dir / "accounts.json"
        data_file.write_text(json.dumps([sample_record]), encoding="utf-8")
        process_files(version, tpl, xsd, "accounts.json")
        assert (work_dir / f"{version}.xml").exists()

    def test_process_files_invalid_type_raises(self):
        with pytest.raises(XMLGenerationError):
            process_files(
                "acmt.999.001.01",
                "template.xml",
                "schema.xsd",
                [{"msg_id": "X"}],
            )

    def test_process_files_missing_data_file_raises(
        self, staged_message, work_dir
    ):
        version = "acmt.001.001.08"
        tpl, xsd = staged_message(version)
        with pytest.raises((FileNotFoundError, ValueError)):
            process_files(version, tpl, xsd, "does_not_exist.csv")

    def test_process_files_propagates_generation_error(
        self, sample_record, staged_message, work_dir, monkeypatch
    ):
        """A failure inside generation is logged and re-raised (except path)."""
        import acmt001.core.core as core

        version = "acmt.001.001.08"
        tpl, xsd = staged_message(version)

        def boom(*_a, **_k):
            raise RuntimeError("generation exploded")

        monkeypatch.setattr(core.xml_generate, "generate_xml", boom)
        with pytest.raises(RuntimeError, match="generation exploded"):
            process_files(version, tpl, xsd, [sample_record])
