# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the Acmt001 developer portal and reference endpoints."""

import pytest
from fastapi.testclient import TestClient

from acmt001.api.app import app


@pytest.fixture()
def client():
    return TestClient(app)


class TestMessageTypes:
    def test_list_message_types(self, client):
        response = client.get("/api/message-types")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 34
        assert {"message_type", "name"} <= set(data[0])

    def test_schema_for_valid_type(self, client):
        response = client.get("/api/message-types/acmt.007.001.05/schema")
        assert response.status_code == 200
        data = response.json()
        assert "properties" in data

    def test_schema_for_bad_type(self, client):
        response = client.get("/api/message-types/not.a.type/schema")
        assert response.status_code == 404


class TestValidateIdentifier:
    def test_valid_bic(self, client):
        response = client.post(
            "/api/validate-identifier",
            json={"kind": "bic", "value": "NWBKGB2LXXX"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["kind"] == "bic"

    def test_invalid_value(self, client):
        response = client.post(
            "/api/validate-identifier",
            json={"kind": "bic", "value": "NOT-A-BIC"},
        )
        assert response.status_code == 200
        assert response.json()["valid"] is False

    def test_bad_kind(self, client):
        response = client.post(
            "/api/validate-identifier",
            json={"kind": "swift", "value": "X"},
        )
        assert response.status_code == 400


class TestPortal:
    def test_root_portal(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Developer Portal" in response.text

    def test_scalar_reference(self, client):
        response = client.get("/api/reference")
        assert response.status_code == 200
        body = response.text
        assert "scalar" in body or "api-reference" in body
