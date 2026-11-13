"""The per-file analysis cache: disposable results reused while a file and its analysis settings are unchanged."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ..rules.rule_selection import RuleSelection
from .connection import StoreConnection
from .keys import MODULE_PORT_SCAN_KEY_FRAGMENT, file_sha256, selection_key
from .timestamps import utc_now_iso

CACHE_DDL = """

    CREATE TABLE IF NOT EXISTS cached_file_analysis (
        file_path TEXT NOT NULL,
        file_hash TEXT NOT NULL,
        selection_key TEXT NOT NULL,
        cached_at TEXT NOT NULL,
        worker_result_json TEXT NOT NULL,
        header_dependencies_json TEXT,
        PRIMARY KEY (file_path, file_hash, selection_key)
    );
"""


class FileAnalysisCache:
    def __init__(self, connection: StoreConnection) -> None:
        self._connection = connection

    def load(
        self,
        *,
        file_path: str,
        file_hash: str,
        rule_selection: RuleSelection | None,
        include_dirs: list[str] | None = None,
        package_registry_fingerprint: str | None = None,
        defines: list[str] | None = None,
    ) -> dict[str, Any] | None:
        key = selection_key(rule_selection, include_dirs, package_registry_fingerprint, defines=defines)
        try:
            with self._connection.transaction() as conn:
                row = conn.execute(
                    """
                    SELECT worker_result_json, header_dependencies_json
                    FROM cached_file_analysis
                    WHERE file_path = ? AND file_hash = ? AND selection_key = ?
                    """,
                    (file_path, file_hash, key),
                ).fetchone()
        except sqlite3.Error:
            return None
        if row is None:
            return None

        # Verify transitive header dependencies
        header_deps_raw = row["header_dependencies_json"]
        if header_deps_raw:
            try:
                deps = json.loads(str(header_deps_raw))
                for dep in deps:
                    dep_path = Path(dep["path"])
                    if not dep_path.is_file() or file_sha256(dep_path) != dep.get("hash"):
                        return None
            except (ValueError, TypeError, KeyError, OSError):
                return None

        try:
            payload = json.loads(str(row["worker_result_json"]))
        except ValueError:
            return None
        return payload if isinstance(payload, dict) else None

    def store(
        self,
        *,
        file_path: str,
        file_hash: str,
        rule_selection: RuleSelection | None,
        worker_result: dict[str, Any],
        include_dirs: list[str] | None = None,
        package_registry_fingerprint: str | None = None,
        defines: list[str] | None = None,
        header_dependencies: list[dict[str, str]] | None = None,
    ) -> None:
        key = selection_key(rule_selection, include_dirs, package_registry_fingerprint, defines=defines)
        header_deps_json = json.dumps(
            header_dependencies
            if header_dependencies is not None
            else worker_result.get("header_dependencies", [])
        )
        with self._connection.transaction() as conn:
            conn.execute(
                """
                INSERT INTO cached_file_analysis(file_path, file_hash, selection_key, cached_at, worker_result_json, header_dependencies_json)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_path, file_hash, selection_key) DO UPDATE SET
                    cached_at = excluded.cached_at,
                    worker_result_json = excluded.worker_result_json,
                    header_dependencies_json = excluded.header_dependencies_json
                """,
                (
                    file_path,
                    file_hash,
                    key,
                    utc_now_iso(),
                    json.dumps(worker_result, sort_keys=True),
                    header_deps_json,
                ),
            )

    def prune(self, *, older_than_days: int) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=older_than_days)).isoformat()
        with self._connection.transaction() as conn:
            removed = int(
                conn.execute(
                    "SELECT count(*) FROM cached_file_analysis WHERE cached_at < ? AND instr(selection_key, ?) = 0",
                    (cutoff, MODULE_PORT_SCAN_KEY_FRAGMENT),
                ).fetchone()[0]
            )
            conn.execute("DELETE FROM cached_file_analysis WHERE cached_at < ?", (cutoff,))
            return removed

    def count(self) -> int:
        with self._connection.transaction() as conn:
            return int(
                conn.execute(
                    "SELECT count(*) FROM cached_file_analysis WHERE instr(selection_key, ?) = 0",
                    (MODULE_PORT_SCAN_KEY_FRAGMENT,),
                ).fetchone()[0]
            )
