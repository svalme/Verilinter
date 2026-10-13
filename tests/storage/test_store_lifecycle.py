from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.pkg.analysis_store import AnalysisStore, SCHEMA_VERSION
from src.run_lint import analyze, main
from tests.support.scratch import make_scratch

PORT_DATA = Path(__file__).resolve().parents[1] / "data" / "port_connection_issues.sv"

_RUN_CHILD_COLUMNS = {
    "analysis_run_files": (
        "run_id INTEGER NOT NULL, ordinal INTEGER NOT NULL, file_path TEXT NOT NULL, "
        "file_hash TEXT NOT NULL, cache_hit INTEGER NOT NULL, PRIMARY KEY (run_id, ordinal)"
    ),
    "analysis_run_diagnostics": (
        "run_id INTEGER NOT NULL, ordinal INTEGER NOT NULL, code TEXT NOT NULL, category TEXT, "
        "severity TEXT, file TEXT, line INTEGER NOT NULL, col INTEGER NOT NULL, message TEXT NOT NULL, "
        "PRIMARY KEY (run_id, ordinal)"
    ),
    "analysis_run_modules": (
        "run_id INTEGER NOT NULL, ordinal INTEGER NOT NULL, module_name TEXT NOT NULL, file TEXT, "
        "line INTEGER NOT NULL, col INTEGER NOT NULL, PRIMARY KEY (run_id, ordinal)"
    ),
    "analysis_run_instantiations": (
        "run_id INTEGER NOT NULL, ordinal INTEGER NOT NULL, parent_module TEXT, child_module TEXT, "
        "instance_name TEXT, file TEXT, line INTEGER NOT NULL, col INTEGER NOT NULL, "
        "connection_style TEXT, PRIMARY KEY (run_id, ordinal)"
    ),
    "analysis_run_connections": (
        "run_id INTEGER NOT NULL, instantiation_ordinal INTEGER NOT NULL, ordinal INTEGER NOT NULL, "
        "kind TEXT NOT NULL, port_name TEXT, expr_text TEXT, expr_name TEXT, expr_width INTEGER, "
        "expr_signed INTEGER, file TEXT, line INTEGER NOT NULL, col INTEGER NOT NULL, "
        "PRIMARY KEY (run_id, instantiation_ordinal, ordinal)"
    ),
}

_RUN_CHILD_ROWS = {
    "analysis_run_files": "(1, 0, 'a.sv', 'h', 0)",
    "analysis_run_diagnostics": "(1, 0, 'X', 'c', 'warning', 'a.sv', 1, 1, 'm')",
    "analysis_run_modules": "(1, 0, 'top', 'a.sv', 1, 1)",
    "analysis_run_instantiations": "(1, 0, 'top', 'sub', 'u0', 'a.sv', 2, 1, 'named')",
    "analysis_run_connections": "(1, 0, 0, 'named', 'p', 'w', 'w', 1, 0, 'a.sv', 2, 1)",
}


def _build_historical_store(path: Path, version: str, *, cascade: bool) -> None:
    """Create a store using the table layout shipped with schema `version`."""
    fk = ", FOREIGN KEY (run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE" if cascade else ""
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO schema_meta VALUES ('schema_version', ?)", (version,))
        conn.execute(
            """
            CREATE TABLE cached_file_analysis (
                file_path TEXT NOT NULL, file_hash TEXT NOT NULL, selection_key TEXT NOT NULL,
                cached_at TEXT NOT NULL, worker_result_json TEXT NOT NULL,
                PRIMARY KEY (file_path, file_hash, selection_key)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE analysis_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, cwd TEXT, format TEXT,
                report_kind TEXT, jobs INTEGER NOT NULL, selection_key TEXT NOT NULL, baseline_path TEXT
            )
            """
        )
        for table, columns in _RUN_CHILD_COLUMNS.items():
            conn.execute(f"CREATE TABLE {table} ({columns}{fk})")
        conn.execute(
            "INSERT INTO cached_file_analysis VALUES (?, ?, ?, ?, ?)",
            ("a.sv", "h", "k", "2026-01-01T00:00:00+00:00", '{"diagnostics": []}'),
        )
        conn.execute(
            "INSERT INTO analysis_runs VALUES (1, '2026-01-01T00:00:00+00:00', '.', 'text', NULL, 1, 'k', NULL)"
        )
        for table, row in _RUN_CHILD_ROWS.items():
            conn.execute(f"INSERT INTO {table} VALUES {row}")
        conn.commit()
    finally:
        conn.close()


@pytest.mark.parametrize(
    ("version", "cascade"),
    [("0", False), ("1", False), ("2", True)],
)
def test_historical_store_migrates_to_current_and_stays_usable(version: str, cascade: bool) -> None:
    store_path = make_scratch("_tmp_store_lifecycle", f"history_v{version}") / "verilinter.sqlite"
    _build_historical_store(store_path, version, cascade=cascade)

    store = AnalysisStore(store_path)

    conn = sqlite3.connect(store_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        assert (
            conn.execute("SELECT value FROM schema_meta WHERE key = 'schema_version'").fetchone()[0]
            == SCHEMA_VERSION
        )
        columns = [row[1] for row in conn.execute("PRAGMA table_info(cached_file_analysis)").fetchall()]
        assert "header_dependencies_json" in columns
        assert conn.execute("SELECT header_dependencies_json FROM cached_file_analysis").fetchone()[0] == "[]"
        for table in _RUN_CHILD_ROWS:
            assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 1

        conn.execute("DELETE FROM analysis_runs WHERE id = 1")
        conn.commit()
        for table in _RUN_CHILD_ROWS:
            assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0, table
    finally:
        conn.close()

    result = analyze([PORT_DATA], store_path=store_path)
    assert result.cache_stats == {"hits": 0, "misses": 1}
    assert store.status()["recorded_runs"] == 1


def test_migration_is_idempotent_on_reopen() -> None:
    store_path = make_scratch("_tmp_store_lifecycle", "idempotent") / "verilinter.sqlite"
    _build_historical_store(store_path, "1", cascade=False)

    AnalysisStore(store_path)
    AnalysisStore(store_path)

    conn = sqlite3.connect(store_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM cached_file_analysis").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM analysis_run_files").fetchone()[0] == 1
    finally:
        conn.close()


def test_full_lifecycle_create_use_prune_vacuum_reuse() -> None:
    store_path = make_scratch("_tmp_store_lifecycle", "full") / "nested" / "dir" / "verilinter.sqlite"

    first = analyze([PORT_DATA], store_path=store_path)
    second = analyze([PORT_DATA], store_path=store_path)
    assert first.cache_stats == {"hits": 0, "misses": 1}
    assert second.cache_stats == {"hits": 1, "misses": 0}

    store = AnalysisStore(store_path)
    assert store.status()["cached_files"] == 1
    assert store.status()["recorded_runs"] == 2

    conn = sqlite3.connect(store_path)
    try:
        conn.execute(
            "UPDATE cached_file_analysis SET cached_at = ?",
            ((datetime.now(timezone.utc) - timedelta(days=40)).isoformat(),),
        )
        conn.commit()
    finally:
        conn.close()

    assert store.prune_cache(older_than_days=30) == 1
    assert store.prune_runs(keep_last=1) == 1
    store.vacuum()
    assert store.status()["cached_files"] == 0
    assert store.status()["recorded_runs"] == 1

    third = analyze([PORT_DATA], store_path=store_path)
    assert third.cache_stats == {"hits": 0, "misses": 1}
    assert [d["code"] for d in third.diagnostics] == [d["code"] for d in first.diagnostics]


def test_cache_rows_grow_per_edit_and_pruning_bounds_them() -> None:
    tmp = make_scratch("_tmp_store_lifecycle", "growth")
    source = tmp / "design.v"
    store_path = tmp / "verilinter.sqlite"

    for i in range(4):
        source.write_text(f"module m{i}; endmodule\n", encoding="utf-8")
        analyze([source], store_path=store_path)

    store = AnalysisStore(store_path)
    assert store.status()["cached_files"] == 4

    conn = sqlite3.connect(store_path)
    try:
        conn.execute(
            "UPDATE cached_file_analysis SET cached_at = ?",
            ((datetime.now(timezone.utc) - timedelta(days=90)).isoformat(),),
        )
        conn.commit()
    finally:
        conn.close()
    assert store.prune_cache(older_than_days=30) == 4
    assert store.status()["cached_files"] == 0


def test_combined_maintenance_flags_run_together(capsys: pytest.CaptureFixture) -> None:
    store_path = make_scratch("_tmp_store_lifecycle", "combined") / "verilinter.sqlite"
    for _ in range(3):
        analyze([PORT_DATA], store_path=store_path)

    code = main(
        ["--store", str(store_path), "--prune-cache-days", "0", "--prune-runs-keep", "1", "--vacuum-store"]
    )
    out = capsys.readouterr().out

    assert code == 0
    assert out.index("cached file result") < out.index("run(s)") < out.index("Vacuumed")
    status = AnalysisStore(store_path).status()
    assert status["cached_files"] == 0
    assert status["recorded_runs"] == 1


def test_store_path_that_is_a_directory_degrades_with_warning(capsys: pytest.CaptureFixture) -> None:
    directory = make_scratch("_tmp_store_lifecycle", "dir_as_store")

    result = analyze([PORT_DATA], store_path=directory)

    assert result.cache_stats is None
    assert result.diagnostics
    assert "continuing without the cache" in capsys.readouterr().err
