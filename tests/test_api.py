"""Tests for acmt001.api.app (FastAPI application).

Exercises every route via fastapi.testclient.TestClient. Tests that
generate XML run with the project root as the working directory so the
API can resolve ``acmt001/templates/<type>`` and write under the CWD.
"""

import asyncio
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from acmt001.api.app import (
    _process_generation_job,
    _resolve_generation_paths,
    _validate_safe_path,
    app,
)
from acmt001.api.job_manager import JobStatus, job_manager
from acmt001.api.models import GenerateXMLRequest, MessageType

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GOLD = Path(__file__).resolve().parent / "gold_master"
VERSION = "acmt.007.001.05"


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def root_cwd(monkeypatch):
    """Run with the project root as CWD (API resolves templates from CWD)."""
    monkeypatch.chdir(PROJECT_ROOT)
    return PROJECT_ROOT


@pytest.fixture()
def data_under_root(root_cwd):
    """Write a valid data file under the project root and clean it up."""
    path = PROJECT_ROOT / "_test_api_accounts.json"
    path.write_text(
        (GOLD / "account_opening_full.json").read_text(), encoding="utf-8"
    )
    yield path
    path.unlink(missing_ok=True)
    generated = (
        PROJECT_ROOT / "acmt001" / "templates" / VERSION / f"{VERSION}.xml"
    )
    generated.unlink(missing_ok=True)


class TestHealthEndpoint:
    @pytest.mark.smoke
    def test_health_returns_200(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_health_message(self, client):
        response = client.get("/api/health")
        assert "Acmt001" in response.json()["message"]


class TestDocsEndpoint:
    def test_docs_available(self, client):
        response = client.get("/api/docs")
        assert response.status_code == 200


class TestValidateEndpoint:
    def test_valid_data(self, client, data_under_root):
        response = client.post(
            "/api/validate",
            json={
                "data_source": "json",
                "file_path": str(data_under_root.resolve()),
                "message_type": VERSION,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["total_rows"] == 1
        assert data["valid_rows"] == 1

    def test_invalid_data(self, client, root_cwd):
        # Loads cleanly (all required columns present) but fails the JSON
        # schema: account_currency violates ^[A-Z]{3}$.
        rec = json.loads(
            (GOLD / "account_opening_basic.json").read_text()
        )
        rec[0]["account_currency"] = "euro"
        path = PROJECT_ROOT / "_test_api_invalid.json"
        path.write_text(json.dumps(rec), encoding="utf-8")
        try:
            response = client.post(
                "/api/validate",
                json={
                    "data_source": "json",
                    "file_path": str(path.resolve()),
                    "message_type": VERSION,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is False
            assert len(data["errors"]) > 0
        finally:
            path.unlink(missing_ok=True)

    def test_unloadable_data_returns_400(self, client, root_cwd):
        # Missing required columns -> AccountValidationError -> 400.
        path = PROJECT_ROOT / "_test_api_unloadable.json"
        path.write_text(json.dumps([{"msg_id": "X"}]), encoding="utf-8")
        try:
            response = client.post(
                "/api/validate",
                json={
                    "data_source": "json",
                    "file_path": str(path.resolve()),
                    "message_type": VERSION,
                },
            )
            assert response.status_code in (400, 500)
        finally:
            path.unlink(missing_ok=True)

    def test_missing_file_returns_error(self, client, root_cwd):
        response = client.post(
            "/api/validate",
            json={
                "data_source": "json",
                "file_path": str(PROJECT_ROOT / "nope_missing.json"),
                "message_type": VERSION,
            },
        )
        assert response.status_code in (400, 403, 404)


class TestGenerateEndpoint:
    def test_generate_returns_xml_path(self, client, data_under_root):
        response = client.post(
            "/api/generate",
            json={
                "data_source": "json",
                "file_path": str(data_under_root.resolve()),
                "message_type": VERSION,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["file_path"] is not None
        assert data["file_path"].endswith(".xml")

    def test_validate_only(self, client, data_under_root):
        response = client.post(
            "/api/generate",
            json={
                "data_source": "json",
                "file_path": str(data_under_root.resolve()),
                "message_type": VERSION,
                "validate_only": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["file_path"] is None

    def test_generate_validation_failure(self, client, root_cwd):
        rec = json.loads(
            (GOLD / "account_opening_basic.json").read_text()
        )
        rec[0]["account_currency"] = "euro"
        path = PROJECT_ROOT / "_test_api_gen_invalid.json"
        path.write_text(json.dumps(rec), encoding="utf-8")
        try:
            response = client.post(
                "/api/generate",
                json={
                    "data_source": "json",
                    "file_path": str(path.resolve()),
                    "message_type": VERSION,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert len(data["validation_errors"]) > 0
        finally:
            path.unlink(missing_ok=True)

    def test_missing_file_returns_error(self, client, root_cwd):
        response = client.post(
            "/api/generate",
            json={
                "data_source": "json",
                "file_path": str(PROJECT_ROOT / "nope_missing.json"),
                "message_type": VERSION,
            },
        )
        assert response.status_code in (400, 403, 404)

    def test_generate_unloadable_data_400(self, client, root_cwd):
        path = PROJECT_ROOT / "_test_api_gen_unloadable.json"
        path.write_text(json.dumps([{"msg_id": "X"}]), encoding="utf-8")
        try:
            response = client.post(
                "/api/generate",
                json={
                    "data_source": "json",
                    "file_path": str(path.resolve()),
                    "message_type": VERSION,
                },
            )
            assert response.status_code in (400, 500)
        finally:
            path.unlink(missing_ok=True)


class TestAsyncGenerateAndJobLifecycle:
    def test_async_generate_then_status_download_delete(
        self, client, data_under_root
    ):
        response = client.post(
            "/api/generate/async",
            json={
                "data_source": "json",
                "file_path": str(data_under_root.resolve()),
                "message_type": VERSION,
            },
        )
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        assert job_id

        # Status route.
        status = client.get(f"/api/status/{job_id}")
        assert status.status_code == 200
        assert status.json()["job_id"] == job_id

        # Drive a deterministic SUCCESS state and download.
        xml_file = PROJECT_ROOT / "_test_api_download.xml"
        xml_file.write_text("<Document/>", encoding="utf-8")
        try:
            job_manager.update_status(
                job_id,
                JobStatus.SUCCESS,
                progress=100,
                result={
                    "success": True,
                    "message": "done",
                    "file_path": str(xml_file.resolve()),
                    "validation_errors": [],
                },
            )
            download = client.get(f"/api/download/{job_id}")
            assert download.status_code == 200
            assert download.headers["content-type"] == "application/xml"
        finally:
            xml_file.unlink(missing_ok=True)

        # Cancel/delete route.
        deleted = client.delete(f"/api/jobs/{job_id}")
        assert deleted.status_code == 200

    def test_status_not_found(self, client):
        response = client.get("/api/status/does-not-exist")
        assert response.status_code == 404

    def test_download_not_found(self, client):
        response = client.get("/api/download/does-not-exist")
        assert response.status_code == 404

    def test_delete_not_found(self, client):
        response = client.delete("/api/jobs/does-not-exist")
        assert response.status_code == 404

    def test_download_wrong_status(self, client):
        job_id = job_manager.create_job()
        job_manager.update_status(job_id, JobStatus.PROCESSING, progress=50)
        response = client.get(f"/api/download/{job_id}")
        assert response.status_code == 400

    def test_download_success_missing_file(self, client, root_cwd):
        job_id = job_manager.create_job()
        job_manager.update_status(
            job_id,
            JobStatus.SUCCESS,
            result={"file_path": str(PROJECT_ROOT / "absent_file.xml")},
        )
        response = client.get(f"/api/download/{job_id}")
        assert response.status_code == 404

    def test_download_outside_cwd_rejected(self, client, root_cwd):
        job_id = job_manager.create_job()
        job_manager.update_status(
            job_id,
            JobStatus.SUCCESS,
            result={"file_path": "/etc/passwd"},
        )
        response = client.get(f"/api/download/{job_id}")
        assert response.status_code in (400, 403)


class TestSafePathHelpers:
    """Direct tests of the path-validation and path-resolution helpers."""

    def test_valid_path(self, root_cwd):
        f = PROJECT_ROOT / "_probe_safe.txt"
        f.write_text("x", encoding="utf-8")
        try:
            assert _validate_safe_path(str(f)) == f.resolve()
        finally:
            f.unlink(missing_ok=True)

    def test_traversal_rejected(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            _validate_safe_path("../../etc/passwd")
        assert exc_info.value.status_code in (400, 403)

    def test_outside_cwd_rejected(self, root_cwd):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            _validate_safe_path("/usr/bin/python")
        assert exc_info.value.status_code == 403

    def test_resolve_generation_paths_no_output_dir(self, root_cwd):
        request = GenerateXMLRequest(
            data_source="json",
            file_path="x.json",
            message_type=MessageType.ACMT_007_05,
        )
        output_dir, xsd, tpl = _resolve_generation_paths(request)
        assert output_dir == str(Path.cwd())
        assert xsd.endswith(".xsd")
        assert tpl.endswith("template.xml")

    def test_resolve_generation_paths_with_output_dir(self, root_cwd):
        out = PROJECT_ROOT / "_probe_outdir"
        try:
            request = GenerateXMLRequest(
                data_source="json",
                file_path="x.json",
                message_type=MessageType.ACMT_007_05,
                output_dir=str(out),
            )
            output_dir, _, _ = _resolve_generation_paths(request)
            assert output_dir == str(out.resolve())
        finally:
            if out.exists():
                out.rmdir()


class TestAsyncJobProcessing:
    """Drive the background generation coroutine directly."""

    def test_process_job_success(self, data_under_root):
        job_id = job_manager.create_job()
        request = GenerateXMLRequest(
            data_source="json",
            file_path=str(data_under_root.resolve()),
            message_type=MessageType.ACMT_007_05,
        )
        asyncio.run(_process_generation_job(job_id, request))
        job = job_manager.get_job(job_id)
        assert job.status == JobStatus.SUCCESS
        assert job.result["file_path"].endswith(".xml")

    def test_process_job_file_not_found(self, root_cwd):
        job_id = job_manager.create_job()
        request = GenerateXMLRequest(
            data_source="json",
            file_path=str(PROJECT_ROOT / "absent_async.json"),
            message_type=MessageType.ACMT_007_05,
        )
        asyncio.run(_process_generation_job(job_id, request))
        job = job_manager.get_job(job_id)
        assert job.status == JobStatus.FAILED
        assert job.error == "File not found"

    def test_process_job_validation_failure(self, root_cwd):
        rec = json.loads(
            (GOLD / "account_opening_basic.json").read_text()
        )
        rec[0]["account_currency"] = "euro"
        path = PROJECT_ROOT / "_probe_async_invalid.json"
        path.write_text(json.dumps(rec), encoding="utf-8")
        try:
            job_id = job_manager.create_job()
            request = GenerateXMLRequest(
                data_source="json",
                file_path=str(path.resolve()),
                message_type=MessageType.ACMT_007_05,
            )
            asyncio.run(_process_generation_job(job_id, request))
            job = job_manager.get_job(job_id)
            assert job.status == JobStatus.FAILED
            assert "Validation failed" in job.error
        finally:
            path.unlink(missing_ok=True)

    def test_process_job_unloadable_data_fails(self, root_cwd):
        path = PROJECT_ROOT / "_probe_async_unloadable.json"
        path.write_text(json.dumps([{"msg_id": "X"}]), encoding="utf-8")
        try:
            job_id = job_manager.create_job()
            request = GenerateXMLRequest(
                data_source="json",
                file_path=str(path.resolve()),
                message_type=MessageType.ACMT_007_05,
            )
            asyncio.run(_process_generation_job(job_id, request))
            assert job_manager.get_job(job_id).status == JobStatus.FAILED
        finally:
            path.unlink(missing_ok=True)


class TestSyncInternalError:
    """Unloadable JSON drives the AccountValidationError / 400 path."""

    def test_validate_internal_error(self, client, root_cwd):
        path = PROJECT_ROOT / "_probe_crash.json"
        path.write_text("{invalid", encoding="utf-8")
        try:
            response = client.post(
                "/api/validate",
                json={
                    "data_source": "json",
                    "file_path": str(path.resolve()),
                    "message_type": VERSION,
                },
            )
            assert response.status_code in (400, 500)
        finally:
            path.unlink(missing_ok=True)

    def test_generate_internal_error(self, client, root_cwd):
        path = PROJECT_ROOT / "_probe_crash_gen.json"
        path.write_text("{invalid", encoding="utf-8")
        try:
            response = client.post(
                "/api/generate",
                json={
                    "data_source": "json",
                    "file_path": str(path.resolve()),
                    "message_type": VERSION,
                },
            )
            assert response.status_code in (400, 500)
        finally:
            path.unlink(missing_ok=True)


class TestJobStatusVariants:
    def test_processing_status(self, client):
        job_id = job_manager.create_job()
        job_manager.update_status(job_id, JobStatus.PROCESSING, progress=42)
        data = client.get(f"/api/status/{job_id}").json()
        assert data["status"] == "processing"
        assert data["progress_percent"] == 42

    def test_failed_status(self, client):
        job_id = job_manager.create_job()
        job_manager.update_status(job_id, JobStatus.FAILED, error="boom")
        data = client.get(f"/api/status/{job_id}").json()
        assert data["status"] == "failed"
        assert data["error"] == "boom"

    def test_cancelled_status(self, client):
        job_id = job_manager.create_job()
        job_manager.cancel_job(job_id)
        data = client.get(f"/api/status/{job_id}").json()
        assert data["status"] == "cancelled"

    def test_success_with_result(self, client):
        job_id = job_manager.create_job()
        job_manager.update_status(
            job_id,
            JobStatus.SUCCESS,
            progress=100,
            result={
                "success": True,
                "message": "done",
                "file_path": os.path.join("x", "out.xml"),
                "validation_errors": [],
            },
        )
        data = client.get(f"/api/status/{job_id}").json()
        assert data["status"] == "success"
        assert data["result"] is not None
