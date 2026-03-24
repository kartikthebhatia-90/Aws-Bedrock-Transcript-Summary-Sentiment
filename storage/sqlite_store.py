from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any

from utils.config import OUTPUT_COLUMNS, SQLITE_DB_PATH, ensure_directories


class SQLiteStore:
    def __init__(self, db_path: str | None = None):
        ensure_directories()
        self.db_path = str(db_path or SQLITE_DB_PATH)
        self._create_table()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _create_table(self) -> None:
        query = """
        CREATE TABLE IF NOT EXISTS transcript_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_chat TEXT NOT NULL,
            predicted_topic TEXT,
            sentiment TEXT,
            priority TEXT,
            formal_summary TEXT,
            recommended_action TEXT,
            status TEXT,
            created_at TEXT NOT NULL
        );
        """

        with self._connect() as conn:
            conn.execute(query)
            conn.commit()

    def insert_result(self, result: dict[str, Any]) -> int:
        missing = [key for key in OUTPUT_COLUMNS if key not in result]
        if missing:
            raise ValueError(f"Missing required keys for DB insert: {missing}")

        query = """
        INSERT INTO transcript_analysis (
            raw_chat,
            predicted_topic,
            sentiment,
            priority,
            formal_summary,
            recommended_action,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """

        values = (
            str(result["raw_chat"]),
            str(result["predicted_topic"]),
            str(result["sentiment"]),
            str(result["priority"]),
            str(result["formal_summary"]),
            str(result["recommended_action"]),
            str(result["status"]),
            datetime.utcnow().isoformat(timespec="seconds"),
        )

        with self._connect() as conn:
            cursor = conn.execute(query, values)
            conn.commit()
            return int(cursor.lastrowid)

    def fetch_all_results(self, limit: int = 100) -> list[dict[str, Any]]:
        query = """
        SELECT
            id,
            raw_chat,
            predicted_topic,
            sentiment,
            priority,
            formal_summary,
            recommended_action,
            status,
            created_at
        FROM transcript_analysis
        ORDER BY id DESC
        LIMIT ?;
        """

        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, (limit,)).fetchall()

        return [dict(row) for row in rows]

    def fetch_result_by_id(self, record_id: int) -> dict[str, Any] | None:
        query = """
        SELECT
            id,
            raw_chat,
            predicted_topic,
            sentiment,
            priority,
            formal_summary,
            recommended_action,
            status,
            created_at
        FROM transcript_analysis
        WHERE id = ?;
        """

        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(query, (record_id,)).fetchone()

        return dict(row) if row else None