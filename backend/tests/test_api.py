import os
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


from backend.app.config import settings
from backend.app.core.security import validate_pdf_signature
from backend.app.services.storage import storage_repo

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_storage(tmp_path):
    """Ensure every test uses a clean temporary database and restore settings."""
    original_db = storage_repo.db_path
    original_enabled = storage_repo.enabled
    original_config_enabled = settings.enable_history_persistence
    original_gemini_key = settings.gemini_api_key

    temp_db = str(tmp_path / "test_api_history.db")
    storage_repo.db_path = temp_db
    storage_repo.enabled = True
    settings.enable_history_persistence = True
    settings.gemini_api_key = ""
    storage_repo._init_db()

    yield

    storage_repo.db_path = original_db
    storage_repo.enabled = original_enabled
    settings.enable_history_persistence = original_config_enabled
    settings.gemini_api_key = original_gemini_key


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "ocr_status" in data
    assert "ocr_available" in data["ocr_status"]


def test_synthetic_sample_endpoint():
    # Valid sample type
    resp_cbc = client.post("/api/v1/reports/sample", json={"sample_type": "cbc"})
    assert resp_cbc.status_code == 200
    cbc_data = resp_cbc.json()
    assert cbc_data["is_synthetic"] is True
    assert len(cbc_data["tests"]) >= 5
    assert any(t["canonical_name"] == "Hemoglobin" for t in cbc_data["tests"])

    resp_cmp = client.post("/api/v1/reports/sample", json={"sample_type": "cmp"})
    assert resp_cmp.status_code == 200
    cmp_data = resp_cmp.json()
    assert cmp_data["is_synthetic"] is True
    assert cmp_data["out_of_range_count"] == 1  # Elevated Glucose

    # Invalid sample type
    resp_invalid = client.post("/api/v1/reports/sample", json={"sample_type": "unknown_type"})
    assert resp_invalid.status_code == 404


def test_upload_valid_synthetic_pdf():
    pdf_path = os.path.join(os.path.dirname(__file__), "..", "sample_reports", "synthetic_cbc_report.pdf")
    with open(pdf_path, "rb") as f:
        response = client.post(
            "/api/v1/reports/upload",
            files={"file": ("synthetic_cbc_report.pdf", f, "application/pdf")},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "synthetic_cbc_report.pdf"
    assert data["total_tests_detected"] >= 5
    assert len(data["educational_notes"]) >= 1
    assert "ai_explanation" in data
    assert data["ai_explanation"]["status"] == "ai_unavailable"
    assert "not configured" in data["ai_explanation"]["status_reason"].lower()


def test_upload_invalid_file_signature():
    response = client.post(
        "/api/v1/reports/upload",
        files={"file": ("fake.pdf", b"This is plain text not a pdf", "application/pdf")},
    )
    assert response.status_code == 400
    assert "Invalid document signature" in response.json()["detail"]


def test_list_reports_pagination_and_search():
    # Initially empty
    res_empty = client.get("/api/v1/reports")
    assert res_empty.status_code == 200
    empty_data = res_empty.json()
    assert empty_data["total"] == 0
    assert empty_data["items"] == []
    assert empty_data["history_enabled"] is True

    # Create two reports via sample endpoint
    client.post("/api/v1/reports/sample", json={"sample_type": "cbc"})
    client.post("/api/v1/reports/sample", json={"sample_type": "cmp"})

    # Check total
    res_list = client.get("/api/v1/reports")
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["total"] == 2
    assert len(list_data["items"]) == 2

    # Check pagination limit=1
    res_p1 = client.get("/api/v1/reports?page=1&limit=1")
    assert res_p1.status_code == 200
    data_p1 = res_p1.json()
    assert len(data_p1["items"]) == 1
    assert data_p1["has_more"] is True

    res_p2 = client.get("/api/v1/reports?page=2&limit=1")
    assert res_p2.status_code == 200
    data_p2 = res_p2.json()
    assert len(data_p2["items"]) == 1
    assert data_p2["has_more"] is False

    # Check search filter
    res_search = client.get("/api/v1/reports?search=cbc")
    assert res_search.status_code == 200
    data_search = res_search.json()
    assert data_search["total"] == 1
    assert "cbc" in data_search["items"][0]["filename"].lower()


def test_get_report_by_id_and_not_found():
    # Create sample report
    resp = client.post("/api/v1/reports/sample", json={"sample_type": "lipid"})
    assert resp.status_code == 200
    created = resp.json()
    report_id = created["id"]

    # Retrieve valid report
    get_resp = client.get(f"/api/v1/reports/{report_id}")
    assert get_resp.status_code == 200
    retrieved = get_resp.json()
    assert retrieved["id"] == report_id
    assert retrieved["filename"] == created["filename"]
    assert len(retrieved["tests"]) == len(created["tests"])

    # Retrieve unknown report
    missing_resp = client.get("/api/v1/reports/rep-unknown-uuid-12345")
    assert missing_resp.status_code == 404
    assert "not found" in missing_resp.json()["detail"].lower()


def test_delete_report_lifecycle():
    resp = client.post("/api/v1/reports/sample", json={"sample_type": "glucose"})
    assert resp.status_code == 200
    report_id = resp.json()["id"]

    # Verify present in get and export
    assert client.get(f"/api/v1/reports/{report_id}").status_code == 200
    assert client.get(f"/api/v1/reports/{report_id}/export?format=pdf").status_code == 200

    # Delete
    del_resp = client.delete(f"/api/v1/reports/{report_id}")
    assert del_resp.status_code == 204

    # Subsequent GET must return 404
    assert client.get(f"/api/v1/reports/{report_id}").status_code == 404

    # Subsequent export must return 404
    assert client.get(f"/api/v1/reports/{report_id}/export?format=pdf").status_code == 404

    # Deleting already-deleted report returns 404
    assert client.delete(f"/api/v1/reports/{report_id}").status_code == 404


def test_export_report_pdf_and_json():
    resp = client.post("/api/v1/reports/sample", json={"sample_type": "cbc"})
    assert resp.status_code == 200
    report_id = resp.json()["id"]

    # Export PDF
    pdf_resp = client.get(f"/api/v1/reports/{report_id}/export?format=pdf")
    assert pdf_resp.status_code == 200
    assert "application/pdf" in pdf_resp.headers["content-type"]
    assert f'filename="medilens_{report_id}.pdf"' in pdf_resp.headers["content-disposition"]
    assert validate_pdf_signature(pdf_resp.content) is True

    # Export JSON
    json_resp = client.get(f"/api/v1/reports/{report_id}/export?format=json")
    assert json_resp.status_code == 200
    assert "application/json" in json_resp.headers["content-type"]
    assert f'filename="medilens_{report_id}.json"' in json_resp.headers["content-disposition"]
    json_data = json_resp.json()
    assert json_data["id"] == report_id
    assert json_data["is_synthetic"] is True
    assert len(json_data["tests"]) >= 5


def test_export_report_invalid_format_and_missing_id():
    resp = client.post("/api/v1/reports/sample", json={"sample_type": "cbc"})
    report_id = resp.json()["id"]

    # Invalid format
    bad_fmt_resp = client.get(f"/api/v1/reports/{report_id}/export?format=docx")
    assert bad_fmt_resp.status_code == 400
    assert "unsupported export format" in bad_fmt_resp.json()["detail"].lower()

    # Missing ID
    missing_export = client.get("/api/v1/reports/rep-missing-999/export?format=pdf")
    assert missing_export.status_code == 404
    assert "not found" in missing_export.json()["detail"].lower()


def test_history_disabled_behavior():
    # Disable history persistence
    settings.enable_history_persistence = False
    storage_repo.enabled = False

    try:
        # Uploading/sample generation still works seamlessly
        resp = client.post("/api/v1/reports/sample", json={"sample_type": "cbc"})
        assert resp.status_code == 200
        sample_data = resp.json()
        report_id = sample_data["id"]

        # History list shows history_enabled = False and total = 0
        list_resp = client.get("/api/v1/reports")
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert list_data["history_enabled"] is False
        assert list_data["total"] == 0

        # Direct retrieval returns 404 because not persisted
        assert client.get(f"/api/v1/reports/{report_id}").status_code == 404
    finally:
        # Restore
        settings.enable_history_persistence = True
        storage_repo.enabled = True

