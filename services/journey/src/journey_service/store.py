"""Key-value store with pluggable backends — journeys must survive restarts AND serverless cold starts.

Default is the dependency-free SQLite file (JOURNEY_DB; ":memory:" in tests).
When the deployment has a database attached, the store binds to it instead so
state survives serverless cold starts and scale-out:
  - POSTGRES_URL / DATABASE_URL          -> Postgres (pg8000, pure Python)
  - KV_REST_API_URL + KV_REST_API_TOKEN  -> Upstash-compatible Redis REST
    (UPSTASH_REDIS_REST_URL/_TOKEN also accepted)
A ":memory:" path always stays SQLite so tests remain hermetic.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import ssl
import threading
import urllib.parse
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_DB = Path(__file__).resolve().parent.parent.parent / "data" / "journey.sqlite3"
_TABLE = "kv_journey"
_NS = "journey:"


class _SqliteBackend:
    def __init__(self, path: str) -> None:
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
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

    def next_seq(self, name: str) -> int:
        """Atomic incrementing counter (application / booking numbers)."""
        with self._lock:
            row = self._conn.execute(
                "SELECT value FROM kv WHERE key = ?", (f"seq:{name}",)
            ).fetchone()
            current = json.loads(row[0])["n"] if row else 0
            self._conn.execute(
                "INSERT INTO kv (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (f"seq:{name}", json.dumps({"n": current + 1})),
            )
            self._conn.commit()
        return current + 1


class _PostgresBackend:
    """Postgres over pg8000 (pure Python; in requirements.txt for Vercel)."""

    def __init__(self, url: str) -> None:
        import pg8000.dbapi  # deliberate late import — optional dependency

        u = urllib.parse.urlsplit(url)
        self._connect = lambda: pg8000.dbapi.connect(
            user=urllib.parse.unquote(u.username or "postgres"),
            password=urllib.parse.unquote(u.password or ""),
            host=u.hostname or "localhost",
            port=u.port or 5432,
            database=(u.path or "").lstrip("/") or "postgres",
            ssl_context=ssl.create_default_context(),
        )
        self._lock = threading.Lock()
        self._conn = self._connect()
        self._conn.autocommit = True
        self._exec(
            f"CREATE TABLE IF NOT EXISTS {_TABLE} (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )

    def _exec(self, sql: str, params: tuple = ()) -> list:
        with self._lock:
            for attempt in (1, 2):
                try:
                    cur = self._conn.cursor()
                    cur.execute(sql, params)
                    return cur.fetchall() if cur.description else []
                except Exception:
                    if attempt == 2:
                        raise
                    self._conn = self._connect()  # one reconnect on a dropped link
                    self._conn.autocommit = True
        return []

    def get(self, key: str) -> dict | None:
        rows = self._exec(f"SELECT value FROM {_TABLE} WHERE key = %s", (key,))
        return json.loads(rows[0][0]) if rows else None

    def all(self, prefix: str = "") -> dict[str, dict]:
        rows = self._exec(
            f"SELECT key, value FROM {_TABLE} WHERE key LIKE %s", (f"{prefix}%",)
        )
        return {k: json.loads(v) for k, v in rows}

    def put(self, key: str, value: dict) -> None:
        self._exec(
            f"INSERT INTO {_TABLE} (key, value) VALUES (%s, %s) "
            "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
            (key, json.dumps(value)),
        )

    def delete(self, key: str) -> None:
        self._exec(f"DELETE FROM {_TABLE} WHERE key = %s", (key,))

    def next_seq(self, name: str) -> int:
        rows = self._exec(
            f"INSERT INTO {_TABLE} (key, value) VALUES (%s, %s) "
            f"ON CONFLICT (key) DO UPDATE SET value = json_build_object("
            f"'n', ((({_TABLE}.value)::json->>'n')::int + 1))::text "
            f"RETURNING (value)::json->>'n'",
            (f"seq:{name}", '{"n": 1}'),
        )
        return int(rows[0][0])


class _UpstashBackend:
    """Upstash-compatible Redis over REST (plain HTTPS; httpx is already a dep)."""

    def __init__(self, url: str, token: str) -> None:
        import httpx  # late import keeps this file usable without httpx

        self._httpx = httpx
        self._url = url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {token}"}
        self._cmd("PING")

    def _cmd(self, *parts: str) -> object:
        resp = self._httpx.post(
            self._url, headers=self._headers, json=[str(p) for p in parts], timeout=8.0
        )
        resp.raise_for_status()
        return resp.json().get("result")

    def get(self, key: str) -> dict | None:
        raw = self._cmd("GET", _NS + key)
        return json.loads(raw) if raw else None

    def all(self, prefix: str = "") -> dict[str, dict]:
        keys: list[str] = []
        cursor = "0"
        while True:
            cursor, batch = self._cmd("SCAN", cursor, "MATCH", f"{_NS}{prefix}*", "COUNT", "200")
            keys.extend(batch)
            if str(cursor) == "0":
                break
        out: dict[str, dict] = {}
        for i in range(0, len(keys), 100):
            chunk = keys[i : i + 100]
            values = self._cmd("MGET", *chunk)
            for k, v in zip(chunk, values):
                if v is not None:
                    out[k[len(_NS) :]] = json.loads(v)
        return out

    def put(self, key: str, value: dict) -> None:
        self._cmd("SET", _NS + key, json.dumps(value))

    def delete(self, key: str) -> None:
        self._cmd("DEL", _NS + key)

    def next_seq(self, name: str) -> int:
        return int(self._cmd("INCR", f"{_NS}seq:{name}"))


def _external_backend():
    pg_url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    if not pg_url:
        # Supabase-style env (the attached hackathon DB): synthesize a URL.
        host = os.environ.get("SUPABASE_HOST")
        user = os.environ.get("SUPABASE_USER")
        password = os.environ.get("SUPABASE_PASSWORD")
        if host and user and password:
            port = os.environ.get("SUPABASE_PORT", "5432")
            name = os.environ.get("SUPABASE_DBNAME", "postgres")
            pg_url = (
                f"postgres://{urllib.parse.quote(user)}:{urllib.parse.quote(password)}"
                f"@{host}:{port}/{name}"
            )
    if pg_url:
        try:
            backend = _PostgresBackend(pg_url)
            logger.info("%s store bound to Postgres", _NS)
            return backend
        except Exception as exc:  # noqa: BLE001 — any driver failure must fall back
            logger.warning("Postgres store unavailable (%s); falling back", exc)
    rest_url = os.environ.get("KV_REST_API_URL") or os.environ.get("UPSTASH_REDIS_REST_URL")
    rest_token = os.environ.get("KV_REST_API_TOKEN") or os.environ.get("UPSTASH_REDIS_REST_TOKEN")
    if rest_url and rest_token:
        try:
            backend = _UpstashBackend(rest_url, rest_token)
            logger.info("%s store bound to Redis REST", _NS)
            return backend
        except Exception as exc:  # noqa: BLE001 — any driver failure must fall back
            logger.warning("Redis REST store unavailable (%s); falling back", exc)
    return None


class KeyValueStore:
    def __init__(self, path: str | None = None) -> None:
        self.path = path or os.environ.get("JOURNEY_DB") or str(DEFAULT_DB)
        backend = None
        if self.path != ":memory:":  # tests always stay on local SQLite
            backend = _external_backend()
        self._backend = backend or _SqliteBackend(self.path)
        self.backend_name = type(self._backend).__name__.lstrip("_")

    def get(self, key: str) -> dict | None:
        return self._backend.get(key)

    def all(self, prefix: str = "") -> dict[str, dict]:
        return self._backend.all(prefix)

    def put(self, key: str, value: dict) -> None:
        self._backend.put(key, value)

    def delete(self, key: str) -> None:
        self._backend.delete(key)

    def next_seq(self, name: str) -> int:
        """Atomic incrementing counter (application / booking numbers)."""
        return self._backend.next_seq(name)
