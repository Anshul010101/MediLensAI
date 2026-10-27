import datetime
import json
import sqlite3
from typing import List, Optional, Tuple

from backend.app.config import settings
from backend.app.models.report import (
    AIExplanationStatus,
    ReportListItem,
    ReportSummary,
)
from backend.app.utils.logger import log_processing_event, logger


class StorageRepository:
    """
    Privacy-aware SQLite repository for report history.
    Stores only structured summaries; raw uploaded PDFs and full prompts are never stored.
    """

    def __init__(self, db_path: Optional[str] = None, enabled: Optional[bool] = None):
        self.db_path = db_path if db_path is not None else settings.sqlite_db_path
        self.enabled = enabled if enabled is not None else settings.enable_history_persistence
        if self.enabled:
            self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with timeout."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize database table and indexes if not present."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reports (
                        id TEXT PRIMARY KEY,
                        filename TEXT NOT NULL,
                        upload_timestamp TEXT NOT NULL,
                        total_tests INTEGER NOT NULL,
                        in_range_count INTEGER NOT NULL,
                        out_of_range_count INTEGER NOT NULL,
                        inconclusive_count INTEGER NOT NULL,
                        is_synthetic INTEGER NOT NULL,
                        ai_status TEXT NOT NULL,
                        structured_json TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_reports_timestamp 
                    ON reports(upload_timestamp DESC);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_reports_filename 
                    ON reports(filename);
                """)
                conn.commit()
        except Exception as ex:
            logger.error(f"Failed to initialize SQLite storage repository: {str(ex)}")

    def save(self, report: ReportSummary) -> bool:
        """
        Save a structured report summary.
        Does not persist raw PDFs or full prompts.
        """
        if not self.enabled:
            return False

        try:
            # Serialize report summary to JSON
            report_json = report.model_dump_json()

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO reports (
                        id, filename, upload_timestamp, total_tests,
                        in_range_count, out_of_range_count, inconclusive_count,
                        is_synthetic, ai_status, structured_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        report.id,
                        report.filename,
                        report.upload_timestamp.isoformat(),
                        report.total_tests_detected,
                        report.in_range_count,
                        report.out_of_range_count,
                        report.inconclusive_count,
                        1 if report.is_synthetic else 0,
                        report.ai_explanation.status.value,
                        report_json,
                    ),
                )
                conn.commit()

            log_processing_event("report_saved_to_history", {
                "file_name": report.filename,
                "status": "persisted",
            })
            return True
        except Exception as ex:
            logger.error(f"Error persisting report to storage: {str(ex)}")
            return False

    def get(self, report_id: str) -> Optional[ReportSummary]:
        """Retrieve a structured report summary by its unique ID."""
        if not self.enabled or not report_id:
            return None

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT structured_json FROM reports WHERE id = ?",
                    (report_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return None
                return ReportSummary.model_validate_json(row["structured_json"])
        except Exception as ex:
            logger.error(f"Error reading report {report_id} from storage: {str(ex)}")
            return None

    def list_reports(
        self,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
    ) -> Tuple[List[ReportListItem], int]:
        """
        List saved reports with pagination and optional search filter.
        Returns (items, total_count).
        """
        if not self.enabled:
            return ([], 0)

        page_clean = max(1, page)
        limit_clean = min(max(1, limit), 100)
        offset = (page_clean - 1) * limit_clean

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if search and search.strip():
                    search_term = f"%{search.strip()}%"
                    cursor.execute(
                        "SELECT COUNT(*) AS total FROM reports WHERE filename LIKE ? OR id LIKE ?",
                        (search_term, search_term),
                    )
                    total = cursor.fetchone()["total"]

                    cursor.execute(
                        """
                        SELECT id, filename, upload_timestamp, total_tests,
                               in_range_count, out_of_range_count, inconclusive_count,
                               is_synthetic, ai_status
                        FROM reports
                        WHERE filename LIKE ? OR id LIKE ?
                        ORDER BY upload_timestamp DESC
                        LIMIT ? OFFSET ?
                        """,
                        (search_term, search_term, limit_clean, offset),
                    )
                else:
                    cursor.execute("SELECT COUNT(*) AS total FROM reports")
                    total = cursor.fetchone()["total"]

                    cursor.execute(
                        """
                        SELECT id, filename, upload_timestamp, total_tests,
                               in_range_count, out_of_range_count, inconclusive_count,
                               is_synthetic, ai_status
                        FROM reports
                        ORDER BY upload_timestamp DESC
                        LIMIT ? OFFSET ?
                        """,
                        (limit_clean, offset),
                    )

                rows = cursor.fetchall()
                items: List[ReportListItem] = []
                for row in rows:
                    items.append(
                        ReportListItem(
                            id=row["id"],
                            filename=row["filename"],
                            upload_timestamp=datetime.datetime.fromisoformat(row["upload_timestamp"]),
                            total_tests_detected=row["total_tests"],
                            in_range_count=row["in_range_count"],
                            out_of_range_count=row["out_of_range_count"],
                            inconclusive_count=row["inconclusive_count"],
                            is_synthetic=bool(row["is_synthetic"]),
                            ai_status=AIExplanationStatus(row["ai_status"]),
                        )
                    )
                return (items, total)
        except Exception as ex:
            logger.error(f"Error querying report list from storage: {str(ex)}")
            return ([], 0)

    def delete(self, report_id: str) -> bool:
        """
        Delete a saved report from storage.
        Returns True if deleted, False if not found or failed.
        """
        if not self.enabled or not report_id:
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM reports WHERE id = ?",
                    (report_id,),
                )
                conn.commit()
                deleted = cursor.rowcount > 0

            if deleted:
                log_processing_event("report_deleted_from_history", {
                    "status": "deleted",
                })
            return deleted
        except Exception as ex:
            logger.error(f"Error deleting report {report_id} from storage: {str(ex)}")
            return False


storage_repo = StorageRepository()
