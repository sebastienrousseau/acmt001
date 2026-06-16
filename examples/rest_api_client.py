#!/usr/bin/env python3
"""Example: drive the REST API with the in-process test client.

Usage:
    python examples/rest_api_client.py

Uses FastAPI's TestClient so no separate server process is needed. The same
calls work against a running server (uvicorn acmt001.api.app:app) via httpx or
curl. Runs from the repository root (the API resolves bundled templates and
account files relative to the working directory).
"""

import os
from pathlib import Path

from fastapi.testclient import TestClient

from acmt001.api.app import app

os.chdir(Path(__file__).resolve().parent.parent)
client = TestClient(app)

# 1. Health and discovery -----------------------------------------------------
print("GET /api/health        ->", client.get("/api/health").json())
types = client.get("/api/message-types").json()
print(
    f"GET /api/message-types -> {len(types)} types (first: {types[0]['message_type']})"
)

schema = client.get("/api/message-types/acmt.007.001.05/schema").json()
print("GET …/schema           -> title:", schema["title"])

# 2. Validate a financial identifier -----------------------------------------
resp = client.post(
    "/api/validate-identifier", json={"kind": "bic", "value": "NWBKGB2LXXX"}
)
print("POST /api/validate-identifier ->", resp.json())

# 3. Validate account data ----------------------------------------------------
resp = client.post(
    "/api/validate",
    json={
        "file_path": "examples/accounts.csv",
        "data_source": "csv",
        "message_type": "acmt.007.001.05",
    },
)
print("POST /api/validate     ->", resp.status_code, resp.json().get("valid"))

# 4. Generate XML synchronously ----------------------------------------------
resp = client.post(
    "/api/generate",
    json={
        "file_path": "examples/accounts.csv",
        "data_source": "csv",
        "message_type": "acmt.007.001.05",
        "validate_only": True,  # validate without writing a file
    },
)
print("POST /api/generate     ->", resp.status_code)

# 5. Documentation portals ----------------------------------------------------
for path in ["/", "/api/reference", "/api/docs", "/openapi.json"]:
    print(f"GET {path:16s} -> {client.get(path).status_code}")
