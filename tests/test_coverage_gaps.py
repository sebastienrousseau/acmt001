"""Tests to close remaining coverage gaps across non-API modules."""

import builtins
import logging
import os

import pytest

# --- csv/load_csv_data.py gaps (68-69, 79-90, 161-176) ---
from acmt001.csv.load_csv_data import (
    load_csv_data,
    load_csv_data_streaming,
)
from acmt001.exceptions import DataSourceError


class TestCsvLoaderGaps:
    def test_file_not_found_after_path_validation(self, tmp_path, monkeypatch):
        """Lines 68-69: safe_path exists for validation but isfile is False."""
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "ghost.csv"
        target.write_text("col1\nval\n", encoding="utf-8")

        real_isfile = os.path.isfile

        def fake_isfile(path):
            if str(path).endswith("ghost.csv"):
                return False
            return real_isfile(path)

        monkeypatch.setattr(os.path, "isfile", fake_isfile)
        with pytest.raises(FileNotFoundError):
            load_csv_data(str(target))

    def test_oserror_reading_file(self, tmp_path, monkeypatch):
        """Lines 79-84: OSError raised while reading."""
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "data.csv"
        target.write_text("col1\nval\n", encoding="utf-8")

        real_open = builtins.open

        def boom(path, *args, **kwargs):
            if str(path).endswith("data.csv"):
                raise OSError("disk error")
            return real_open(path, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", boom)
        with pytest.raises(OSError):
            load_csv_data(str(target))

    def test_unicode_decode_error_reading_file(self, tmp_path, monkeypatch):
        """Lines 85-90: UnicodeDecodeError raised while reading."""
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "binary.csv"
        target.write_bytes(b"col1\n\x80\x81\xff\n")
        with pytest.raises(UnicodeDecodeError):
            load_csv_data(str(target))

    def test_streaming_file_not_found(self, tmp_path, monkeypatch):
        """Lines 161-164: FileNotFoundError in streaming reader."""
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "ghost.csv"
        target.write_text("col1\nval\n", encoding="utf-8")

        real_open = builtins.open

        def boom(path, *args, **kwargs):
            if str(path).endswith("ghost.csv"):
                raise FileNotFoundError("gone")
            return real_open(path, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", boom)
        with pytest.raises(FileNotFoundError):
            list(load_csv_data_streaming(str(target)))

    def test_streaming_oserror(self, tmp_path, monkeypatch):
        """Lines 165-170: OSError in streaming reader."""
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "data.csv"
        target.write_text("col1\nval\n", encoding="utf-8")

        real_open = builtins.open

        def boom(path, *args, **kwargs):
            if str(path).endswith("data.csv"):
                raise OSError("disk error")
            return real_open(path, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", boom)
        with pytest.raises(OSError):
            list(load_csv_data_streaming(str(target)))

    def test_streaming_unicode_decode_error(self, tmp_path, monkeypatch):
        """Lines 171-176: UnicodeDecodeError in streaming reader."""
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "binary.csv"
        target.write_bytes(b"col1\n\x80\x81\xff\n")
        with pytest.raises(UnicodeDecodeError):
            list(load_csv_data_streaming(str(target)))

    def test_streaming_empty_file(self, tmp_path, monkeypatch):
        """Lines 178-182: DataSourceError when streaming an empty CSV."""
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "empty.csv"
        target.write_text("col1,col2\n", encoding="utf-8")
        with pytest.raises(DataSourceError, match="empty"):
            list(load_csv_data_streaming(str(target)))


# --- json/load_json_data.py gaps (74, 172, 197, 244, 281) ---

from acmt001.json.load_json_data import (
    load_json_data,
    load_jsonl_data,
    load_jsonl_data_streaming,
)


class TestJsonLoaderGaps:
    def test_json_isfile_false_after_validation(self, tmp_path, monkeypatch):
        """Line 74: validated path passes but isfile returns False."""
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "ghost.json"
        target.write_text("{}", encoding="utf-8")

        real_isfile = os.path.isfile

        def fake_isfile(path):
            if str(path).endswith("ghost.json"):
                return False
            return real_isfile(path)

        monkeypatch.setattr(os.path, "isfile", fake_isfile)
        with pytest.raises(FileNotFoundError):
            load_json_data(str(target))

    def test_jsonl_isfile_false_after_validation(self, tmp_path, monkeypatch):
        """Line 172: jsonl validated path passes but isfile returns False."""
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "ghost.jsonl"
        target.write_text('{"a": 1}\n', encoding="utf-8")

        real_isfile = os.path.isfile

        def fake_isfile(path):
            if str(path).endswith("ghost.jsonl"):
                return False
            return real_isfile(path)

        monkeypatch.setattr(os.path, "isfile", fake_isfile)
        with pytest.raises(FileNotFoundError):
            load_jsonl_data(str(target))

    def test_jsonl_generic_read_error(self, tmp_path, monkeypatch):
        """Line 197: generic (non-DataSourceError) error wrapped."""
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "data.jsonl"
        target.write_text('{"a": 1}\n', encoding="utf-8")

        real_open = builtins.open

        def boom(path, *args, **kwargs):
            if str(path).endswith("data.jsonl"):
                raise OSError("disk error")
            return real_open(path, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", boom)
        with pytest.raises(DataSourceError, match="Error reading JSONL"):
            load_jsonl_data(str(target))

    def test_jsonl_streaming_isfile_false(self, tmp_path, monkeypatch):
        """Line 244: streaming validated path passes but isfile False."""
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "ghost.jsonl"
        target.write_text('{"a": 1}\n', encoding="utf-8")

        real_isfile = os.path.isfile

        def fake_isfile(path):
            if str(path).endswith("ghost.jsonl"):
                return False
            return real_isfile(path)

        monkeypatch.setattr(os.path, "isfile", fake_isfile)
        with pytest.raises(FileNotFoundError):
            list(load_jsonl_data_streaming(str(target)))

    def test_jsonl_streaming_generic_read_error(self, tmp_path, monkeypatch):
        """Line 281: streaming generic error wrapped as DataSourceError."""
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "data.jsonl"
        target.write_text('{"a": 1}\n', encoding="utf-8")

        real_open = builtins.open

        def boom(path, *args, **kwargs):
            if str(path).endswith("data.jsonl"):
                raise OSError("disk error")
            return real_open(path, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", boom)
        with pytest.raises(DataSourceError, match="Error reading JSONL"):
            list(load_jsonl_data_streaming(str(target)))


# --- parquet/load_parquet_data.py gaps (45, 157->154, 162) ---

import acmt001.parquet.load_parquet_data as parquet_mod
from acmt001.parquet.load_parquet_data import (
    _check_parquet_support,
    load_parquet_data_streaming,
)


class TestParquetGaps:
    def test_check_parquet_support_missing(self, monkeypatch):
        """Line 45: DataSourceError when pyarrow is unavailable."""
        monkeypatch.setattr(parquet_mod, "HAS_PARQUET_SUPPORT", False)
        with pytest.raises(DataSourceError, match="pyarrow"):
            _check_parquet_support()

    def test_streaming_empty_batches(self, tmp_path, monkeypatch):
        """Branch 157->154: a batch yielding no rows is skipped."""
        pytest.importorskip("pyarrow")
        import pyarrow as pa
        import pyarrow.parquet as pq

        monkeypatch.chdir(tmp_path)
        target = tmp_path / "data.parquet"
        table = pa.table({"id": ["A", "B"], "v": [1, 2]})
        pq.write_table(table, str(target))

        class _EmptyBatch:
            def to_pylist(self):
                return []

        class _FakeParquetFile:
            def __init__(self, *_a, **_k):
                pass

            def iter_batches(self, *_a, **_k):
                yield _EmptyBatch()

        monkeypatch.setattr(parquet_mod.pq, "ParquetFile", _FakeParquetFile)
        chunks = list(load_parquet_data_streaming(str(target)))
        assert chunks == []

    def test_streaming_read_error_wrapped(self, tmp_path, monkeypatch):
        """Line 164: non-DataSourceError wrapped as DataSourceError."""
        pytest.importorskip("pyarrow")
        import pyarrow as pa
        import pyarrow.parquet as pq

        monkeypatch.chdir(tmp_path)
        target = tmp_path / "data.parquet"
        pq.write_table(pa.table({"id": ["A"]}), str(target))

        def boom(*_a, **_k):
            raise RuntimeError("corrupt parquet")

        monkeypatch.setattr(parquet_mod.pq, "ParquetFile", boom)
        with pytest.raises(DataSourceError, match="Error reading Parquet"):
            list(load_parquet_data_streaming(str(target)))

    def test_streaming_reraises_datasource_error(self, tmp_path, monkeypatch):
        """Line 162: a DataSourceError from reading is re-raised as-is."""
        pytest.importorskip("pyarrow")
        import pyarrow as pa
        import pyarrow.parquet as pq

        monkeypatch.chdir(tmp_path)
        target = tmp_path / "data.parquet"
        pq.write_table(pa.table({"id": ["A"]}), str(target))

        def boom(*_a, **_k):
            raise DataSourceError("inner parquet failure")

        monkeypatch.setattr(parquet_mod.pq, "ParquetFile", boom)
        with pytest.raises(DataSourceError, match="inner parquet failure"):
            list(load_parquet_data_streaming(str(target)))


# --- context/context.py gaps (103->exit, 123) ---

from acmt001.context.context import Context


class TestContextGaps:
    def test_set_log_level_without_logger(self):
        """Branch 103->exit: set_log_level when logger is falsy."""
        ctx = Context.get_instance()
        saved = ctx.logger
        try:
            ctx.logger = None  # type: ignore[assignment]
            ctx.set_log_level("INFO")
            assert ctx.log_level is not None
        finally:
            ctx.logger = saved

    def test_init_logger_adds_handler(self):
        """Line 123: init_logger adds a handler to a handler-less logger."""
        ctx = Context.get_instance()
        saved = ctx.logger
        saved_name = ctx.name
        try:
            name = "cov-gap-ctx-fresh-logger"
            fresh = logging.getLogger(name)
            for h in list(fresh.handlers):
                fresh.removeHandler(h)
            ctx.name = name
            ctx.logger = None  # type: ignore[assignment]
            ctx.init_logger()
            assert ctx.logger is not None
            assert len(ctx.logger.handlers) >= 1
        finally:
            ctx.logger = saved
            ctx.name = saved_name


# --- security/path_validator.py gaps (64-65) ---

from acmt001.security.path_validator import (
    PathValidationError,
    _resolve_within_allowed_bases,
)


class TestPathValidatorGaps:
    def test_realpath_raises(self, monkeypatch):
        """Lines 64-65: os.path.realpath raising OSError -> PathValidationError."""
        import acmt001.security.path_validator as pv

        def boom(_path):
            raise OSError("realpath failed")

        monkeypatch.setattr(pv.os.path, "realpath", boom)
        with pytest.raises(PathValidationError, match="Invalid path"):
            _resolve_within_allowed_bases("some/file.csv")


# --- compliance/swift_charset.py gaps (225, 385->404) ---

from acmt001.compliance.swift_charset import (
    _transliterate,
    cleanse_data_with_report,
)


class TestSwiftCharsetGaps:
    def test_transliterate_nfkd_decomposition(self):
        """Line 225: NFKD path returns ASCII for a decomposable accented char."""
        assert _transliterate("ý") == "y"  # 'ý'

    def test_cleanse_data_with_report_charset_disabled(self):
        """Branch 385->404: cleanse_charset=False skips the charset pass."""
        rows = [{"account_name": "Müller"}]
        result, report = cleanse_data_with_report(
            rows, enforce_lengths=False, cleanse_charset=False
        )
        # Unchanged since charset cleansing was skipped.
        assert result[0]["account_name"] == "Müller"
        assert report.violation_count == 0


# --- db/load_db_data.py gap (101) ---

import sqlite3

from acmt001.db.load_db_data import load_db_data


class TestDbLoaderGaps:
    def test_isfile_false_after_validation(self, tmp_path, monkeypatch):
        """Line 101: validated path passes but isfile returns False."""
        monkeypatch.chdir(tmp_path)
        db = tmp_path / "accounts.db"
        conn = sqlite3.connect(str(db))
        conn.execute("CREATE TABLE accounts (id TEXT)")
        conn.commit()
        conn.close()

        real_isfile = os.path.isfile

        def fake_isfile(path):
            if str(path).endswith("accounts.db"):
                return False
            return real_isfile(path)

        monkeypatch.setattr(os.path, "isfile", fake_isfile)
        with pytest.raises(FileNotFoundError):
            load_db_data(str(db))


# --- xml/write_xml_to_file.py gaps (40->42, 42->44, 46->exit) ---

import xml.etree.ElementTree as ET

from acmt001.xml.write_xml_to_file import indent_xml


class TestIndentXmlGaps:
    def test_preformatted_parent_text_and_tail(self):
        """Branches 40->42 and 42->44: existing non-blank text/tail preserved."""
        root = ET.Element("root")
        root.text = "existing"
        child = ET.SubElement(root, "child")
        child.text = "x"
        root.tail = "roottail"
        indent_xml(root)
        # Pre-set non-blank text/tail are not overwritten
        assert root.text == "existing"
        assert root.tail == "roottail"

    def test_leaf_with_existing_tail(self):
        """Branch 46->exit: leaf element with non-blank tail unchanged."""
        root = ET.Element("root")
        child = ET.SubElement(root, "child")
        child.tail = "keepme"
        indent_xml(child, level=1)
        assert child.tail == "keepme"

    def test_leaf_at_level_zero(self):
        """Branch 49 False: level 0 leaf gets no tail added."""
        leaf = ET.Element("leaf")
        indent_xml(leaf, level=0)
        assert leaf.tail is None
