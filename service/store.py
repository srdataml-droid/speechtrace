"""SQLite report store for explicit opt-in retention; never stores raw recordings.

The default TTL is one hour. Reports can contain personal transcript text, and should
not be persisted without consent. An unpredictable ID is NOT a substitute for auth.
"""
from __future__ import annotations

import json
import os
import secrets
import sqlite3
import time
from pathlib import Path


def default_store_path() -> str:
    return os.getenv("SPEECHTRACE_REPORT_DB", "").strip() or str(Path.home() / ".speechtrace" / "reports.sqlite")


class ReportStore:
    def __init__(self, path: str | Path | None = None, ttl_seconds: int | None = None):
        self.path = str(path or default_store_path())
        self.ttl_seconds = int(ttl_seconds or os.getenv("SPEECHTRACE_REPORT_TTL", "3600"))
        if self.ttl_seconds < 60 or self.ttl_seconds > 86400:
            raise ValueError("Report TTL must be from 60 seconds to 24 hours.")
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _db(self):
        return sqlite3.connect(self.path, timeout=8)

    def _init(self):
        with self._db() as con:
            con.execute("CREATE TABLE IF NOT EXISTS reports "
                        "(id TEXT PRIMARY KEY, content TEXT NOT NULL, expires_at INTEGER NOT NULL)")
            con.execute("CREATE INDEX IF NOT EXISTS reports_expiry ON reports (expires_at)")

    def save(self, report: dict) -> str:
        token = secrets.token_urlsafe(24)
        expiry = int(time.time()) + self.ttl_seconds
        with self._db() as con:
            con.execute("DELETE FROM reports WHERE expires_at <= ?", (int(time.time()),))
            con.execute("INSERT INTO reports (id, content, expires_at) VALUES (?, ?, ?)",
                        (token, json.dumps(report, allow_nan=False), expiry))
        return token

    def get(self, report_id: str) -> dict | None:
        if not isinstance(report_id, str) or len(report_id) > 100:
            return None
        with self._db() as con:
            row = con.execute("SELECT content FROM reports WHERE id=? AND expires_at>?",
                              (report_id, int(time.time()))).fetchone()
        return json.loads(row[0]) if row else None

    def delete(self, report_id: str) -> bool:
        with self._db() as con:
            cur = con.execute("DELETE FROM reports WHERE id=?", (report_id,))
        return cur.rowcount > 0
