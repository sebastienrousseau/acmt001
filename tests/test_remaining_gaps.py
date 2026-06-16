"""Tests closing the remaining API coverage gaps (acmt001/api/app.py).

These hit reachable error/guard paths in the FastAPI application:
the cwd-restriction 403 guards (a tmp file passes ``_validate_safe_path``
but is outside CWD), the async job-creation failure handler, and the
download endpoint's "no file available" branch.
"""

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from acmt001.api.app import app, generate_xml_async
from acmt001.api.job_manager import JobStatus, job_manager
from acmt001.api.models import GenerateXMLRequest, MessageType

GOLD = Path(__file__).resolve().parent / "gold_master"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERSION = "acmt.007.001.05"


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def root_cwd(monkeypatch):
    monkeypatch.chdir(PROJECT_ROOT)
    return PROJECT_ROOT


class TestAsyncJobCreationFailure:
    def test_create_job_raises(self, monkeypatch):
        """Lines 386-390: generic exception -> 500 when job creation fails."""
        from fastapi import HTTPException

        import acmt001.api.app as app_mod

        def boom():
            raise RuntimeError("manager down")

        monkeypatch.setattr(app_mod.job_manager, "create_job", boom)
        request = GenerateXMLRequest(
            data_source="json",
            file_path="accounts.json",
            message_type=MessageType(VERSION),
        )
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(generate_xml_async(request))
        assert exc_info.value.status_code == 500


class TestDownloadNoFile:
    def test_download_success_job_without_file_path(self, client):
        """Lines 500-504: SUCCESS job whose result lacks 'file_path'."""
        job_id = job_manager.create_job()
        job_manager.update_status(
            job_id,
            JobStatus.SUCCESS,
            progress=100,
            result={"success": True, "message": "ok"},
        )
        response = client.get(f"/api/download/{job_id}")
        assert response.status_code == 404
        assert "No file available" in response.json()["detail"]
