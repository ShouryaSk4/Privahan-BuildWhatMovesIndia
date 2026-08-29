"""Tiny SQLite key-value store — journeys must survive a process restart.

In-memory state was the biggest source of demo flakiness (a restart or a second
instance wiped every journey mid-demo). This keeps the storage dependency-free:
one table, JSON values, atomic upserts. Set JOURNEY_DB=:memory: in tests.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent.parent / "data" / "journey.sqlite3"


class KeyValueStore:
    def __init__(self, path: str | None = None) -> None:
        self.path = path or os.environ.get("JOURNEY_DB") or str(DEFAULT_DB)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        self._conn.commit()

    def get(self, key: str) -> dict | None:
        with self._lock:
            row = self._conn.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def all(self, prefix: str = "") -> dict[str, dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT key, value FROM kv WHERE key LIKE ?", (f"{prefix}%",)
            ).fetchall()
        return {k: json.loads(v) for k, v in rows}

    def put(self, key: str, value: dict) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO kv (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, json.dumps(value)),
            )
            self._conn.commit()

    def delete(self, key: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM kv WHERE key = ?", (key,))
            self._conn.commit()
