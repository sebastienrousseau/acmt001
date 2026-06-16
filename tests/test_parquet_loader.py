"""Tests for parquet/load_parquet_data.py."""

import pytest

from acmt001.exceptions import DataSourceError
from acmt001.parquet.load_parquet_data import (
    HAS_PARQUET_SUPPORT,
    _check_parquet_support,
    load_parquet_data,
    load_parquet_data_streaming,
)


def _make_valid_row():
    return {
        "msg_id": "ACMT-MSG-0001",
        "creation_date_time": "2026-01-15T10:30:00",
        "process_id": "ACMT-PRC-0001",
        "account_id": "GB29NWBK60161331926819",
        "account_currency": "EUR",
        "account_name": "Treasury Operating Account",
        "account_type_cd": "CACC",
        "account_servicer_bic": "NWBKGB2LXXX",
        "account_owner_name": "Acme Embedded Finance Ltd",
        "account_owner_country": "GB",
        "org_full_legal_name": "Acme Embedded Finance Limited",
        "org_id_lei": "5493001KJTIIGC8Y1R12",
    }


@pytest.fixture()
def parquet_file(tmp_path, monkeypatch):
    """Create a test parquet file with a single account record."""
    pytest.importorskip("pyarrow")
    import pyarrow as pa
    import pyarrow.parquet as pq

    monkeypatch.chdir(tmp_path)
    path = tmp_path / "accounts.parquet"
    table = pa.Table.from_pylist([_make_valid_row()])
    pq.write_table(table, str(path))
    return str(path)


@pytest.fixture()
def multi_row_parquet(tmp_path, monkeypatch):
    """Create a parquet file with multiple account records."""
    pytest.importorskip("pyarrow")
    import pyarrow as pa
    import pyarrow.parquet as pq

    monkeypatch.chdir(tmp_path)
    path = tmp_path / "multi.parquet"
    rows = [{**_make_valid_row(), "msg_id": f"ACMT-{i}"} for i in range(5)]
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, str(path))
    return str(path)


@pytest.fixture()
def empty_parquet(tmp_path, monkeypatch):
    """Create an empty parquet file (schema only, no rows)."""
    pytest.importorskip("pyarrow")
    import pyarrow as pa
    import pyarrow.parquet as pq

    monkeypatch.chdir(tmp_path)
    path = tmp_path / "empty.parquet"
    table = pa.table({"msg_id": pa.array([], type=pa.string())})
    pq.write_table(table, str(path))
    return str(path)


class TestCheckParquetSupport:
    def test_support_available(self):
        if HAS_PARQUET_SUPPORT:
            _check_parquet_support()  # Should not raise
        else:
            with pytest.raises(DataSourceError, match="pyarrow"):
                _check_parquet_support()


@pytest.mark.skipif(not HAS_PARQUET_SUPPORT, reason="pyarrow not installed")
class TestLoadParquetData:
    def test_load_valid(self, parquet_file):
        data = load_parquet_data(parquet_file)
        assert len(data) == 1
        assert data[0]["msg_id"] == "ACMT-MSG-0001"

    def test_load_multiple(self, multi_row_parquet):
        data = load_parquet_data(multi_row_parquet)
        assert len(data) == 5

    def test_nonexistent_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(FileNotFoundError):
            load_parquet_data(str(tmp_path / "nonexistent.parquet"))

    def test_empty_raises(self, empty_parquet):
        with pytest.raises(DataSourceError, match="empty"):
            load_parquet_data(empty_parquet)

    def test_invalid_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        bad = tmp_path / "bad.parquet"
        bad.write_text("not a parquet file")
        with pytest.raises((DataSourceError, Exception)):
            load_parquet_data(str(bad))

    def test_traversal_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(FileNotFoundError):
            load_parquet_data("../../etc/passwd.parquet")


@pytest.mark.skipif(not HAS_PARQUET_SUPPORT, reason="pyarrow not installed")
class TestLoadParquetDataStreaming:
    def test_stream_valid(self, multi_row_parquet):
        chunks = list(
            load_parquet_data_streaming(multi_row_parquet, chunk_size=2)
        )
        assert len(chunks) >= 1
        assert sum(len(c) for c in chunks) == 5

    def test_stream_single_chunk(self, parquet_file):
        chunks = list(
            load_parquet_data_streaming(parquet_file, chunk_size=100)
        )
        assert len(chunks) == 1

    def test_stream_nonexistent_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(FileNotFoundError):
            list(load_parquet_data_streaming(str(tmp_path / "none.parquet")))

    def test_stream_invalid_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        bad = tmp_path / "bad.parquet"
        bad.write_text("not parquet")
        with pytest.raises((DataSourceError, Exception)):
            list(load_parquet_data_streaming(str(bad)))

    def test_stream_traversal_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(FileNotFoundError):
            list(load_parquet_data_streaming("../../etc/passwd.parquet"))
