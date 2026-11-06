"""Run history: a durable record of each lint run, its files, findings and cross-file summaries."""
from __future__ import annotations

from typing import Any

from ..rules.rule_selection import RuleSelection
from ..semantic.symbol_table import SymbolTable
from .connection import StoreConnection
from .keys import selection_key
from .timestamps import utc_now_iso

HISTORY_DDL = """

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
        FOREIGN KEY (run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
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
        FOREIGN KEY (run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
    );


    CREATE TABLE IF NOT EXISTS analysis_run_modules (
        run_id INTEGER NOT NULL,
        ordinal INTEGER NOT NULL,
        module_name TEXT NOT NULL,
        file TEXT,
        line INTEGER NOT NULL,
        col INTEGER NOT NULL,
        PRIMARY KEY (run_id, ordinal),
        FOREIGN KEY (run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
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
        FOREIGN KEY (run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
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
        FOREIGN KEY (run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
    );
"""


class RunHistory:
    def __init__(self, connection: StoreConnection) -> None:
        self._connection = connection

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
        with self._connection.transaction() as conn:
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
                    loc = scope.location or {}
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
                loc = dict(inst.get("location") or {})
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
                    conn_loc = dict(connection.get("location") or {})
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

    def prune(self, *, keep_last: int) -> int:
        with self._connection.transaction() as conn:
            rows = conn.execute(
                "SELECT id FROM analysis_runs ORDER BY id DESC LIMIT -1 OFFSET ?",
                (keep_last,),
            ).fetchall()
            run_ids = [int(row["id"]) for row in rows]
            for run_id in run_ids:
                # ON DELETE CASCADE on the analysis_run_* child tables removes
                # their rows for this run automatically.
                conn.execute("DELETE FROM analysis_runs WHERE id = ?", (run_id,))
            return len(run_ids)

    def count(self) -> int:
        with self._connection.transaction() as conn:
            return int(conn.execute("SELECT count(*) FROM analysis_runs").fetchone()[0])
