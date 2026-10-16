"""
SQLite audit logging for the IT Support Copilot.

Records each chat request with enough information to review decisions later,
without storing API keys, secrets, or full private document contents.
"""
import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(settings.audit_db_path, check_same_thread=False)


def init_db() -> None:
    """Create the audit table if it does not already exist, and migrate columns if needed."""
    try:
        con = _connect()
        con.execute(
            """CREATE TABLE IF NOT EXISTS query_audit (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id  TEXT NOT NULL DEFAULT '',
                created_at  TEXT NOT NULL,
                question    TEXT NOT NULL,
                source_used TEXT NOT NULL,
                kb_grade    TEXT DEFAULT '',
                web_grade   TEXT DEFAULT '',
                retry_count INTEGER DEFAULT 0,
                status      TEXT DEFAULT 'success',
                trace_json  TEXT NOT NULL DEFAULT '[]',
                duration_ms INTEGER DEFAULT 0
            )"""
        )
        # Check existing columns and alter table if any column is missing
        cursor = con.cursor()
        cursor.execute("PRAGMA table_info(query_audit)")
        existing_cols = {col[1] for col in cursor.fetchall()}
        needed_cols = {
            "request_id": "TEXT NOT NULL DEFAULT ''",
            "kb_grade": "TEXT DEFAULT ''",
            "web_grade": "TEXT DEFAULT ''",
            "retry_count": "INTEGER DEFAULT 0",
            "status": "TEXT DEFAULT 'success'",
            "trace_json": "TEXT NOT NULL DEFAULT '[]'",
            "duration_ms": "INTEGER DEFAULT 0",
        }
        for col_name, col_type in needed_cols.items():
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE query_audit ADD COLUMN {col_name} {col_type}")
        con.commit()
        con.close()
        logger.info("Audit database initialized at %s", settings.audit_db_path)
    except Exception as exc:
        logger.error("Failed to initialize audit database: %s", exc)


def write_audit(
    question: str,
    source_used: str,
    trace: list[str],
    *,
    kb_grade: str = "",
    web_grade: str = "",
    retry_count: int = 0,
    status: str = "success",
    duration_ms: int | None = None,
    request_id: str | None = None,
) -> None:
    """
    Write one audit row. Never raises — log and swallow DB errors so that
    a logging failure does not break the chat endpoint.
    """
    rid = request_id or str(uuid.uuid4())
    try:
        con = _connect()
        con.execute(
            """INSERT INTO query_audit
               (request_id, created_at, question, source_used, kb_grade,
                web_grade, retry_count, status, trace_json, duration_ms)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                rid,
                datetime.now(timezone.utc).isoformat(),
                question[:2000],          # truncate to avoid huge rows
                source_used,
                kb_grade or "",
                web_grade or "",
                retry_count,
                status,
                json.dumps(trace),
                duration_ms,
            ),
        )
        con.commit()
        con.close()
    except Exception as exc:
        logger.error("Audit write failed (request_id=%s): %s", rid, exc)
