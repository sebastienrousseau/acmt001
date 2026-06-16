#!/usr/bin/env python3
"""Example: load account data from every supported source (+ streaming).

Usage:
    python examples/data_sources.py

Acmt001's universal loader reads CSV, JSON, JSONL, SQLite, and Parquet, and
also offers a streaming variant for datasets larger than memory. File-based
sources must live under the current working directory (path traversal is
blocked), so this example runs from the repository root.
"""

import json
import os
import sqlite3
import tempfile
from pathlib import Path

from acmt001.data.loader import load_account_data, load_account_data_streaming

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)  # anchor file-based loads to the project root

# --- File sources: CSV / JSON / JSONL ---------------------------------------
for source in [
    "examples/accounts.csv",
    "examples/accounts.json",
    "examples/accounts.jsonl",
]:
    records = load_account_data(source)
    print(f"{source:24s} -> {len(records)} record(s)")

records = load_account_data("examples/accounts.json")
fieldnames = list(records[0].keys())

# --- SQLite (default table name 'acmt001') ----------------------------------
work = Path(tempfile.mkdtemp(dir=ROOT))  # under CWD so the loader accepts it
try:
    db_path = work / "accounts.db"
    con = sqlite3.connect(db_path)
    cols = ", ".join(f'"{c}" TEXT' for c in fieldnames)
    con.execute(f"CREATE TABLE acmt001 ({cols})")
    con.executemany(
        f"INSERT INTO acmt001 VALUES ({', '.join('?' for _ in fieldnames)})",
        [tuple(str(r.get(c, "")) for c in fieldnames) for r in records],
    )
    con.commit()
    con.close()
    rel_db = db_path.relative_to(ROOT)
    print(
        f"{str(rel_db):24s} -> {len(load_account_data(str(rel_db)))} record(s)"
    )

    # --- Parquet (requires pyarrow) -----------------------------------------
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq

        pq_path = work / "accounts.parquet"
        table = pa.table(
            {c: [str(r.get(c, "")) for r in records] for c in fieldnames}
        )
        pq.write_table(table, pq_path)
        rel_pq = pq_path.relative_to(ROOT)
        print(
            f"{str(rel_pq):24s} -> {len(load_account_data(str(rel_pq)))} record(s)"
        )
    except ImportError:
        print("parquet                  -> pyarrow not installed (skipped)")
finally:
    for f in work.iterdir():
        f.unlink()
    work.rmdir()

# --- Streaming: process large datasets in memory-bounded chunks --------------
big = records * 5  # pretend this is a very large dataset
chunks = list(load_account_data_streaming(big, chunk_size=2))
print(f"streaming {len(big)} records  -> {len(chunks)} chunk(s) of <= 2")

# JSON for reference
print("first record keys:", json.dumps(fieldnames[:5]))
