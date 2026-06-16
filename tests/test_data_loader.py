"""Tests for acmt001.data.loader module (unified + streaming loaders)."""

import csv
import json
import sqlite3

import pytest

from acmt001.data.loader import (
    load_account_data,
    load_account_data_streaming,
)
from acmt001.exceptions import AccountValidationError, DataSourceError

REQUIRED_FIELDS = [
    "msg_id",
    "creation_date_time",
    "process_id",
    "account_id",
    "account_currency",
    "account_name",
    "account_type_cd",
    "account_servicer_bic",
    "account_owner_name",
    "account_owner_country",
    "org_full_legal_name",
    "org_id_lei",
]


def _minimal(record):
    """Return a record reduced to the required (flat) fields only."""
    return {k: record[k] for k in REQUIRED_FIELDS}


# --------------------------------------------------------------------------- #
# Direct Python data: list / dict
# --------------------------------------------------------------------------- #
class TestLoadFromList:
    def test_valid_list(self, sample_record):
        data = load_account_data([_minimal(sample_record)])
        assert len(data) == 1
        assert data[0]["msg_id"] == sample_record["msg_id"]

    def test_multiple_rows(self, sample_records):
        data = load_account_data([_minimal(r) for r in sample_records])
        assert len(data) == 2

    def test_empty_list_raises(self):
        with pytest.raises(DataSourceError, match="Empty"):
            load_account_data([])

    def test_non_dict_items_raises(self):
        with pytest.raises(AccountValidationError):
            load_account_data(["not a dict"])

    def test_validation_failure_raises(self, sample_record):
        bad = _minimal(sample_record)
        del bad["account_id"]
        with pytest.raises(AccountValidationError):
            load_account_data([bad])


class TestLoadFromDict:
    def test_valid_dict(self, sample_record):
        data = load_account_data(_minimal(sample_record))
        assert len(data) == 1

    def test_empty_dict_raises(self):
        with pytest.raises(DataSourceError, match="Empty"):
            load_account_data({})

    def test_validation_failure_raises(self, sample_record):
        bad = _minimal(sample_record)
        bad["org_id_lei"] = ""
        with pytest.raises(AccountValidationError):
            load_account_data(bad)


class TestUnsupportedType:
    def test_int_raises(self):
        with pytest.raises(DataSourceError, match="Unsupported data source"):
            load_account_data(42)

    def test_none_raises(self):
        with pytest.raises(DataSourceError, match="Unsupported data source"):
            load_account_data(None)


# --------------------------------------------------------------------------- #
# File-based: CSV / JSON / JSONL / Parquet / SQLite
# --------------------------------------------------------------------------- #
def _write_csv(path, records):
    fields = REQUIRED_FIELDS
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in records:
            writer.writerow(_minimal(r))


def _write_db(path, records, table_name="acmt001"):
    conn = sqlite3.connect(str(path))
    cols = REQUIRED_FIELDS
    col_defs = ", ".join(f"{c} TEXT" for c in cols)
    conn.execute(f"CREATE TABLE {table_name} ({col_defs})")
    placeholders = ", ".join("?" for _ in cols)
    for r in records:
        conn.execute(
            f"INSERT INTO {table_name} VALUES ({placeholders})",
            [r[c] for c in cols],
        )
    conn.commit()
    conn.close()


class TestLoadFromFile:
    def test_load_csv(self, tmp_path, monkeypatch, sample_records):
        monkeypatch.chdir(tmp_path)
        path = tmp_path / "accounts.csv"
        _write_csv(path, sample_records)
        data = load_account_data(str(path))
        assert len(data) == 2

    def test_load_json(self, tmp_path, monkeypatch, sample_records):
        monkeypatch.chdir(tmp_path)
        path = tmp_path / "accounts.json"
        path.write_text(
            json.dumps([_minimal(r) for r in sample_records]),
            encoding="utf-8",
        )
        data = load_account_data(str(path))
        assert len(data) == 2

    def test_load_jsonl(self, tmp_path, monkeypatch, sample_records):
        monkeypatch.chdir(tmp_path)
        path = tmp_path / "accounts.jsonl"
        path.write_text(
            "\n".join(json.dumps(_minimal(r)) for r in sample_records),
            encoding="utf-8",
        )
        data = load_account_data(str(path))
        assert len(data) == 2

    def test_load_db(self, tmp_path, monkeypatch, sample_records):
        monkeypatch.chdir(tmp_path)
        path = tmp_path / "accounts.db"
        _write_db(path, sample_records)
        data = load_account_data(str(path))
        assert len(data) == 2

    def test_load_parquet(self, tmp_path, monkeypatch, sample_records):
        pytest.importorskip("pyarrow")
        import pyarrow as pa
        import pyarrow.parquet as pq

        monkeypatch.chdir(tmp_path)
        path = tmp_path / "accounts.parquet"
        table = pa.Table.from_pylist([_minimal(r) for r in sample_records])
        pq.write_table(table, str(path))
        data = load_account_data(str(path))
        assert len(data) == 2

    def test_unsupported_extension_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(DataSourceError, match="Unsupported file type"):
            load_account_data("data.txt")

    def test_nonexistent_file_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(FileNotFoundError):
            load_account_data(str(tmp_path / "nope.csv"))

    def test_empty_csv_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        path = tmp_path / "empty.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_FIELDS)
            writer.writeheader()
        with pytest.raises(DataSourceError, match="empty"):
            load_account_data(str(path))

    def test_validation_failure_raises(
        self, tmp_path, monkeypatch, sample_record
    ):
        monkeypatch.chdir(tmp_path)
        bad = _minimal(sample_record)
        bad["account_id"] = ""
        path = tmp_path / "bad.csv"
        _write_csv(path, [{**sample_record, "account_id": ""}])
        with pytest.raises(AccountValidationError, match="validation failed"):
            load_account_data(str(path))


# --------------------------------------------------------------------------- #
# Streaming loader
# --------------------------------------------------------------------------- #
class TestLoadAccountDataStreaming:
    def test_stream_from_csv(self, tmp_path, monkeypatch, sample_records):
        monkeypatch.chdir(tmp_path)
        path = tmp_path / "accounts.csv"
        _write_csv(path, sample_records)
        chunks = list(
            load_account_data_streaming(str(path), chunk_size=1)
        )
        assert len(chunks) == 2
        assert all(len(c) == 1 for c in chunks)

    def test_stream_from_list_chunking(self, sample_record):
        records = [_minimal(sample_record) for _ in range(5)]
        chunks = list(
            load_account_data_streaming(records, chunk_size=2)
        )
        assert len(chunks) == 3  # 2+2+1
        assert len(chunks[-1]) == 1

    def test_stream_from_list_single_chunk(self, sample_record):
        records = [_minimal(sample_record) for _ in range(3)]
        chunks = list(load_account_data_streaming(records, chunk_size=100))
        assert len(chunks) == 1
        assert len(chunks[0]) == 3

    def test_stream_validate_false_skips_validation(self, sample_record):
        # Drop a required field; with validate=False this should still stream.
        bad = _minimal(sample_record)
        del bad["msg_id"]
        chunks = list(
            load_account_data_streaming([bad], chunk_size=10, validate=False)
        )
        assert len(chunks) == 1
        assert len(chunks[0]) == 1

    def test_stream_list_validation_failure_raises(self, sample_record):
        bad = _minimal(sample_record)
        bad["account_currency"] = ""
        with pytest.raises(AccountValidationError):
            list(load_account_data_streaming([bad], chunk_size=10))

    def test_stream_file_validation_failure_raises(
        self, tmp_path, monkeypatch, sample_record
    ):
        monkeypatch.chdir(tmp_path)
        path = tmp_path / "bad.csv"
        _write_csv(path, [{**sample_record, "account_name": ""}])
        with pytest.raises(AccountValidationError, match="validation failed"):
            list(load_account_data_streaming(str(path)))

    def test_stream_empty_list_raises(self):
        with pytest.raises(DataSourceError, match="Empty"):
            list(load_account_data_streaming([]))

    def test_stream_non_dict_items_raises(self):
        with pytest.raises(AccountValidationError):
            list(load_account_data_streaming(["not a dict"]))

    def test_stream_unsupported_type_raises(self):
        with pytest.raises(DataSourceError, match="Unsupported data source"):
            list(load_account_data_streaming(42))

    def test_stream_unsupported_file_type_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(DataSourceError, match="Unsupported file type"):
            list(load_account_data_streaming("data.txt"))
