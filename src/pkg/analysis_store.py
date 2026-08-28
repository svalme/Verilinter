from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .rules.rule_selection import RuleSelection
from .semantic.symbol_table import SymbolTable

SCHEMA_VERSION = "1"
ANALYZER_CACHE_VERSION = "2026-08-28"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selection_key(selection: RuleSelection | None) -> str:
    payload = {
        "analyzer_cache_version": ANALYZER_CACHE_VERSION,
        "enabled_codes": sorted(selection.enabled_codes) if selection and selection.enabled_codes else None,
        "enabled_categories": sorted(selection.enabled_categories)
        if selection and selection.enabled_categories
        else None,
        "enabled_profiles": sorted(selection.enabled_profiles) if selection and selection.enabled_profiles else None,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


class AnalysisStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode = WAL;

                CREATE TABLE IF NOT EXISTS schema_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS cached_file_analysis (
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    selection_key TEXT NOT NULL,
                    cached_at TEXT NOT NULL,
                    worker_result_json TEXT NOT NULL,
                    PRIMARY KEY (file_path, file_hash, selection_key)
                );

                CREATE TABLE IF NOT EXISTS analysis_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    cwd TEXT,
                    format TEXT,
                    report_kind TEXT,
                    jobs INTEGER NOT NULL,
                    selection_key TEXT NOT NULL,
                    baseline_path TEXT
                );

                CREATE TABLE IF NOT EXISTS analysis_run_files (
                    run_id INTEGER NOT NULL,
                    ordinal INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    cache_hit INTEGER NOT NULL,
                    PRIMARY KEY (run_id, ordinal),
                    FOREIGN KEY (run_id) REFERENCES analysis_runs(id)
                );

                CREATE TABLE IF NOT EXISTS analysis_run_diagnostics (
                    run_id INTEGER NOT NULL,
                    ordinal INTEGER NOT NULL,
                    code TEXT NOT NULL,
                    category TEXT,
                    severity TEXT,
                    file TEXT,
                    line INTEGER NOT NULL,
                    col INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    PRIMARY KEY (run_id, ordinal),
                    FOREIGN KEY (run_id) REFERENCES analysis_runs(id)
                );

                CREATE TABLE IF NOT EXISTS analysis_run_modules (
                    run_id INTEGER NOT NULL,
                    ordinal INTEGER NOT NULL,
                    module_name TEXT NOT NULL,
                    file TEXT,
                    line INTEGER NOT NULL,
                    col INTEGER NOT NULL,
                    PRIMARY KEY (run_id, ordinal),
                    FOREIGN KEY (run_id) REFERENCES analysis_runs(id)
                );

                CREATE TABLE IF NOT EXISTS analysis_run_instantiations (
                    run_id INTEGER NOT NULL,
                    ordinal INTEGER NOT NULL,
                    parent_module TEXT,
                    child_module TEXT,
                    instance_name TEXT,
                    file TEXT,
                    line INTEGER NOT NULL,
                    col INTEGER NOT NULL,
                    connection_style TEXT,
                    PRIMARY KEY (run_id, ordinal),
                    FOREIGN KEY (run_id) REFERENCES analysis_runs(id)
                );

                CREATE TABLE IF NOT EXISTS analysis_run_connections (
                    run_id INTEGER NOT NULL,
                    instantiation_ordinal INTEGER NOT NULL,
                    ordinal INTEGER NOT NULL,
                    kind TEXT NOT NULL,
                    port_name TEXT,
                    expr_text TEXT,
                    expr_name TEXT,
                    expr_width INTEGER,
                    expr_signed INTEGER,
                    file TEXT,
                    line INTEGER NOT NULL,
                    col INTEGER NOT NULL,
                    PRIMARY KEY (run_id, instantiation_ordinal, ordinal),
                    FOREIGN KEY (run_id) REFERENCES analysis_runs(id)
                );
                """
            )
            existing_version = self._read_schema_version(conn)
            if existing_version is None:
                conn.execute(
                    """
                    INSERT INTO schema_meta(key, value)
                    VALUES ('schema_version', ?)
                    """,
                    (SCHEMA_VERSION,),
                )
                return

            self._migrate_schema(conn, existing_version)

    def _read_schema_version(self, conn: sqlite3.Connection) -> str | None:
        row = conn.execute(
            """
            SELECT value
            FROM schema_meta
            WHERE key = 'schema_version'
            """
        ).fetchone()
        if row is None:
            return None
        return str(row["value"])

    def _migrate_schema(self, conn: sqlite3.Connection, existing_version: str) -> None:
        if existing_version == SCHEMA_VERSION:
            return

        migrations: dict[str, Callable[[sqlite3.Connection], str]] = {
            "0": self._migrate_schema_0_to_1,
        }

        version = existing_version
        while version != SCHEMA_VERSION:
            migration = migrations.get(version)
            if migration is None:
                raise ValueError(
                    "analysis store schema version mismatch: "
                    f"found {existing_version}, expected {SCHEMA_VERSION}. "
                    "No migration path is available. Use a fresh --store path or rebuild the existing store."
                )
            version = migration(conn)

    def _migrate_schema_0_to_1(self, conn: sqlite3.Connection) -> str:
        conn.execute(
            """
            UPDATE schema_meta
            SET value = '1'
            WHERE key = 'schema_version'
            """
        )
        return "1"

    def load_cached_worker_result(
        self,
        *,
        file_path: str,
        file_hash: str,
        rule_selection: RuleSelection | None,
    ) -> dict[str, Any] | None:
        key = selection_key(rule_selection)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT worker_result_json
                FROM cached_file_analysis
                WHERE file_path = ? AND file_hash = ? AND selection_key = ?
                """,
                (file_path, file_hash, key),
            ).fetchone()
        if row is None:
            return None
        return json.loads(str(row["worker_result_json"]))

    def store_cached_worker_result(
        self,
        *,
        file_path: str,
        file_hash: str,
        rule_selection: RuleSelection | None,
        worker_result: dict[str, Any],
    ) -> None:
        key = selection_key(rule_selection)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO cached_file_analysis(file_path, file_hash, selection_key, cached_at, worker_result_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(file_path, file_hash, selection_key) DO UPDATE SET
                    cached_at = excluded.cached_at,
                    worker_result_json = excluded.worker_result_json
                """,
                (
                    file_path,
                    file_hash,
                    key,
                    utc_now_iso(),
                    json.dumps(worker_result, sort_keys=True),
                ),
            )

    def record_run(
        self,
        *,
        cwd: str,
        fmt: str,
        report_kind: str | None,
        jobs: int,
        rule_selection: RuleSelection | None,
        baseline_path: str | None,
        file_records: list[dict[str, Any]],
        diagnostics: list[dict[str, Any]],
        symbol_table: SymbolTable,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO analysis_runs(created_at, cwd, format, report_kind, jobs, selection_key, baseline_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    utc_now_iso(),
                    cwd,
                    fmt,
                    report_kind,
                    jobs,
                    selection_key(rule_selection),
                    baseline_path,
                ),
            )
            run_id = int(cursor.lastrowid)

            for ordinal, record in enumerate(file_records):
                conn.execute(
                    """
                    INSERT INTO analysis_run_files(run_id, ordinal, file_path, file_hash, cache_hit)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        ordinal,
                        record["file_path"],
                        record["file_hash"],
                        1 if record["cache_hit"] else 0,
                    ),
                )

            for ordinal, diagnostic in enumerate(diagnostics):
                conn.execute(
                    """
                    INSERT INTO analysis_run_diagnostics(run_id, ordinal, code, category, severity, file, line, col, message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        ordinal,
                        diagnostic.get("code"),
                        diagnostic.get("category"),
                        diagnostic.get("severity"),
                        diagnostic.get("file"),
                        int(diagnostic.get("line", 0)),
                        int(diagnostic.get("col", 0)),
                        diagnostic.get("message"),
                    ),
                )

            module_ordinal = 0
            for module_name, scopes in symbol_table.modules.items():
                for scope in scopes:
                    loc = scope.location or {"line": 0, "col": 0}
                    conn.execute(
                        """
                        INSERT INTO analysis_run_modules(run_id, ordinal, module_name, file, line, col)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            run_id,
                            module_ordinal,
                            module_name,
                            loc.get("file", scope.file),
                            int(loc.get("line", 0)),
                            int(loc.get("col", 0)),
                        ),
                    )
                    module_ordinal += 1

            for inst_ordinal, inst in enumerate(symbol_table.instantiations):
                loc = dict(inst.get("location", {"line": 0, "col": 0}))
                conn.execute(
                    """
                    INSERT INTO analysis_run_instantiations(
                        run_id, ordinal, parent_module, child_module, instance_name, file, line, col, connection_style
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        inst_ordinal,
                        inst.get("parent_module"),
                        inst.get("child_module"),
                        inst.get("instance_name"),
                        loc.get("file"),
                        int(loc.get("line", 0)),
                        int(loc.get("col", 0)),
                        inst.get("connection_style"),
                    ),
                )
                for conn_ordinal, connection in enumerate(inst.get("connections", [])):
                    conn_loc = dict(connection.get("location", {"line": 0, "col": 0}))
                    conn.execute(
                        """
                        INSERT INTO analysis_run_connections(
                            run_id, instantiation_ordinal, ordinal, kind, port_name, expr_text, expr_name,
                            expr_width, expr_signed, file, line, col
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            run_id,
                            inst_ordinal,
                            conn_ordinal,
                            connection.get("kind"),
                            connection.get("port_name"),
                            connection.get("expr_text"),
                            connection.get("expr_name"),
                            connection.get("expr_width"),
                            1 if connection.get("expr_signed") is True else 0 if connection.get("expr_signed") is False else None,
                            conn_loc.get("file"),
                            int(conn_loc.get("line", 0)),
                            int(conn_loc.get("col", 0)),
                        ),
                    )

        return run_id
