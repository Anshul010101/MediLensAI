import datetime
import os
import sqlite3
import pytest

from backend.app.models.report import (
    AIExplanation,
    AIExplanationStatus,
    ExtractionMetadata,
    FlagStatus,
    ReferenceInterval,
    ReportSummary,
    TestResult,
)
from backend.app.services.storage import StorageRepository


@pytest.fixture
def temp_db_path(tmp_path):
    return str(tmp_path / "test_history.db")


@pytest.fixture
def sample_report():
    return ReportSummary(
        id="rep-test-12345",
        filename="test_lab_report.pdf",
        upload_timestamp=datetime.datetime(2026, 10, 27, 10, 30, 0),
        metadata=ExtractionMetadata(
            page_count=1,
            extracted_character_count=350,
            is_scanned=False,
            ocr_applied=False,
            ocr_available=False,
            is_synthetic=False,
        ),
        tests=[
            TestResult(
                name="Hemoglobin",
                canonical_name="Hemoglobin",
                category="Complete Blood Count",
                value_text="14.5",
                value_numeric=14.5,
                unit="g/dL",
                reference_interval=ReferenceInterval(raw_text="13.5 - 17.5", low=13.5, high=17.5, is_numeric=True),
                flag=FlagStatus.NORMAL,
                source_page=1,
            ),
            TestResult(
                name="Glucose",
                canonical_name="Glucose",
                category="Metabolic Panel",
                value_text="106*",
                value_numeric=106.0,
                unit="mg/dL",
                reference_interval=ReferenceInterval(raw_text="70 - 99", low=70.0, high=99.0, is_numeric=True),
                flag=FlagStatus.HIGH,
                source_page=1,
            ),
        ],
        educational_notes=[],
        ai_explanation=AIExplanation(
            status=AIExplanationStatus.AI_UNAVAILABLE,
            status_reason="Gemini unconfigured for test.",
        ),
        total_tests_detected=2,
        in_range_count=1,
        out_of_range_count=1,
        inconclusive_count=0,
        is_synthetic=False,
    )


def test_storage_save_and_retrieve(temp_db_path, sample_report):
    repo = StorageRepository(db_path=temp_db_path, enabled=True)
    assert repo.save(sample_report) is True

    retrieved = repo.get(sample_report.id)
    assert retrieved is not None
    assert retrieved.id == sample_report.id
    assert retrieved.filename == "test_lab_report.pdf"
    assert len(retrieved.tests) == 2
    assert retrieved.tests[0].canonical_name == "Hemoglobin"
    assert retrieved.tests[1].flag == FlagStatus.HIGH


def test_storage_persistence_across_instances(temp_db_path, sample_report):
    repo1 = StorageRepository(db_path=temp_db_path, enabled=True)
    repo1.save(sample_report)

    # Re-instantiate repository pointing to the same SQLite file
    repo2 = StorageRepository(db_path=temp_db_path, enabled=True)
    retrieved = repo2.get(sample_report.id)
    assert retrieved is not None
    assert retrieved.id == sample_report.id


def test_storage_list_pagination_and_search(temp_db_path):
    repo = StorageRepository(db_path=temp_db_path, enabled=True)

    # Save 3 distinct reports
    for i in range(1, 4):
        report = ReportSummary(
            id=f"rep-item-{i}",
            filename=f"patient_report_{i}.pdf" if i != 2 else "special_cbc_report.pdf",
            upload_timestamp=datetime.datetime(2026, 10, 27, 10, i, 0),
            metadata=ExtractionMetadata(page_count=1, extracted_character_count=100),
            tests=[],
            total_tests_detected=i,
            in_range_count=i,
            out_of_range_count=0,
            inconclusive_count=0,
            is_synthetic=False,
        )
        repo.save(report)

    # Test list without filter
    items, total = repo.list_reports(page=1, limit=2)
    assert total == 3
    assert len(items) == 2
    # Verify ordering (newest first: item 3, then item 2)
    assert items[0].id == "rep-item-3"

    # Test page 2
    items_p2, total_p2 = repo.list_reports(page=2, limit=2)
    assert len(items_p2) == 1
    assert items_p2[0].id == "rep-item-1"

    # Test search filter
    search_items, search_total = repo.list_reports(search="special")
    assert search_total == 1
    assert len(search_items) == 1
    assert search_items[0].filename == "special_cbc_report.pdf"


def test_storage_delete(temp_db_path, sample_report):
    repo = StorageRepository(db_path=temp_db_path, enabled=True)
    repo.save(sample_report)

    # Verify present
    assert repo.get(sample_report.id) is not None

    # Delete
    assert repo.delete(sample_report.id) is True
    # Verify no longer present
    assert repo.get(sample_report.id) is None

    # Deleting already-deleted report returns False
    assert repo.delete(sample_report.id) is False


def test_storage_disabled_behavior(temp_db_path, sample_report):
    repo = StorageRepository(db_path=temp_db_path, enabled=False)

    assert repo.save(sample_report) is False
    assert repo.get(sample_report.id) is None
    items, total = repo.list_reports()
    assert items == []
    assert total == 0
    assert repo.delete(sample_report.id) is False


def test_storage_does_not_persist_raw_pdfs(temp_db_path, sample_report):
    repo = StorageRepository(db_path=temp_db_path, enabled=True)
    repo.save(sample_report)

    # Direct inspection of SQLite database rows
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT structured_json FROM reports WHERE id = ?", (sample_report.id,))
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    json_content = row[0]
    # Ensure binary PDF magic bytes and raw PDFs are completely absent
    assert "%PDF-" not in json_content
    assert "stream" not in json_content
