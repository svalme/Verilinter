"""The elaboration cache: the elaborated width record of one file set, reused while none of its inputs changed."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

import json

from .connection import StoreConnection
from .timestamps import utc_now_iso

ELABORATION_DDL = """

    CREATE TABLE IF NOT EXISTS cached_elaboration (
        set_id TEXT PRIMARY KEY,
        input_key TEXT NOT NULL,
        cached_at TEXT NOT NULL,
        record_json TEXT NOT NULL
    );
"""


class ElaborationCache:
    """One row per file set (`set_id`: the paths, include directories and defines). The row holds the record built
    from one state of the inputs (`input_key`); a changed input replaces the row, so a project that is edited
    repeatedly keeps one record, not one per edit."""

    def __init__(self, connection: StoreConnection) -> None:
        self._connection = connection

    def load(self, *, set_id: str, input_key: str) -> dict[str, Any] | None:
        try:
            with self._connection.transaction() as conn:
                row = conn.execute(
                    "SELECT record_json FROM cached_elaboration WHERE set_id = ? AND input_key = ?",
                    (set_id, input_key),
                ).fetchone()
        except sqlite3.Error:
            return None
        if row is None:
            return None
        try:
            payload = json.loads(str(row["record_json"]))
        except ValueError:
            return None
        return payload if isinstance(payload, dict) else None

    def store(self, *, set_id: str, input_key: str, payload: dict[str, Any]) -> None:
        with self._connection.transaction() as conn:
            conn.execute(
                """
                INSERT INTO cached_elaboration(set_id, input_key, cached_at, record_json)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(set_id) DO UPDATE SET
                    input_key = excluded.input_key,
                    cached_at = excluded.cached_at,
                    record_json = excluded.record_json
                """,
                (set_id, input_key, utc_now_iso(), json.dumps(payload, separators=(",", ":"))),
            )

    def prune(self, *, older_than_days: int) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=older_than_days)).isoformat()
        with self._connection.transaction() as conn:
            return int(conn.execute("DELETE FROM cached_elaboration WHERE cached_at < ?", (cutoff,)).rowcount)

    def count(self) -> int:
        with self._connection.transaction() as conn:
            return int(conn.execute("SELECT count(*) FROM cached_elaboration").fetchone()[0])
