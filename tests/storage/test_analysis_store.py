from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import pkg.analysis_store as analysis_store_module
from src.pkg.rules.rule_selection import RuleSelection
import src.run_lint as run_lint_module
from src.run_lint import analyze

DATA = Path(__file__).resolve().parents[1] / "data" / "self_assignment.v"
PORT_DATA = Path(__file__).resolve().parents[1] / "data" / "port_connection_issues.sv"
SCRATCH_ROOT = Path(__file__).resolve().parents[1] / "_tmp_analysis_store"


def _scratch_dir(name: str) -> Path:
    target = SCRATCH_ROOT / f"{name}_{uuid.uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def test_analyze_persists_run_and_connection_rows() -> None:
    tmp = _scratch_dir("persist")
    store_path = tmp / "verilinter.sqlite"

    result = analyze([PORT_DATA], store_path=store_path, fmt="text", report_kind="connections")

    assert result.cache_stats == {"hits": 0, "misses": 1}
    assert store_path.exists()

    conn = sqlite3.connect(store_path)
    try:
        run_count = conn.execute("SELECT COUNT(*) FROM analysis_runs").fetchone()[0]
        file_count = conn.execute("SELECT COUNT(*) FROM analysis_run_files").fetchone()[0]
        diag_count = conn.execute("SELECT COUNT(*) FROM analysis_run_diagnostics").fetchone()[0]
        inst_count = conn.execute("SELECT COUNT(*) FROM analysis_run_instantiations").fetchone()[0]
        conn_count = conn.execute("SELECT COUNT(*) FROM analysis_run_connections").fetchone()[0]
    finally:
        conn.close()

    assert run_count == 1
    assert file_count == 1
    assert diag_count == len(result.diagnostics)
    assert inst_count >= 1
    assert conn_count >= 1


def test_analyze_reuses_cached_worker_result(monkeypatch: pytest.MonkeyPatch) -> None:
    tmp = _scratch_dir("cache")
    source = tmp / "self_assignment.v"
    source.write_text(DATA.read_text(encoding="utf-8"), encoding="utf-8")
    store_path = tmp / "verilinter.sqlite"

    first = analyze([source], store_path=store_path)
    assert first.cache_stats == {"hits": 0, "misses": 1}

    def fail_parse(path: str):
        raise AssertionError(f"parse_file should not be called for cached file {path}")

    monkeypatch.setattr(run_lint_module, "parse_file", fail_parse)
    second = analyze([source], store_path=store_path)

    assert second.cache_stats == {"hits": 1, "misses": 0}
    assert [d["code"] for d in second.diagnostics] == [d["code"] for d in first.diagnostics]


def test_analyze_can_disable_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    tmp = _scratch_dir("no_cache")
    source = tmp / "self_assignment.v"
    source.write_text(DATA.read_text(encoding="utf-8"), encoding="utf-8")
    store_path = tmp / "verilinter.sqlite"

    analyze([source], store_path=store_path)

    calls: list[str] = []
    real_parse = run_lint_module.parse_file

    def track_parse(path: str, include_dirs=None):
        calls.append(path)
        return real_parse(path)

    monkeypatch.setattr(run_lint_module, "parse_file", track_parse)
    analyze([source], store_path=store_path, use_cache=False)

    assert calls == [str(source)]


def test_analyze_refreshes_when_file_contents_change(monkeypatch: pytest.MonkeyPatch) -> None:
    tmp = _scratch_dir("file_change")
    source = tmp / "self_assignment.v"
    source.write_text(DATA.read_text(encoding="utf-8"), encoding="utf-8")
    store_path = tmp / "verilinter.sqlite"

    analyze([source], store_path=store_path)
    source.write_text(
        DATA.read_text(encoding="utf-8").replace("tmp <= tmp;", "tmp <= clk;"),
        encoding="utf-8",
    )

    calls: list[str] = []
    real_parse = run_lint_module.parse_file

    def track_parse(path: str, include_dirs=None):
        calls.append(path)
        return real_parse(path)

    monkeypatch.setattr(run_lint_module, "parse_file", track_parse)
    result = analyze([source], store_path=store_path)

    assert result.cache_stats == {"hits": 0, "misses": 1}
    assert calls == [str(source)]


def test_analyze_refreshes_when_rule_selection_changes(monkeypatch: pytest.MonkeyPatch) -> None:
    tmp = _scratch_dir("selection_change")
    source = tmp / "self_assignment.v"
    source.write_text(DATA.read_text(encoding="utf-8"), encoding="utf-8")
    store_path = tmp / "verilinter.sqlite"

    analyze([source], store_path=store_path)

    calls: list[str] = []
    real_parse = run_lint_module.parse_file

    def track_parse(path: str, include_dirs=None):
        calls.append(path)
        return real_parse(path)

    monkeypatch.setattr(run_lint_module, "parse_file", track_parse)
    result = analyze(
        [source],
        store_path=store_path,
        rule_selection=RuleSelection(enabled_codes=frozenset({"NO_SELF_ASSIGNMENT"})),
    )

    assert result.cache_stats == {"hits": 0, "misses": 1}
    assert calls == [str(source)]


def test_analyze_refreshes_when_analyzer_cache_version_changes(monkeypatch: pytest.MonkeyPatch) -> None:
    tmp = _scratch_dir("version_change")
    source = tmp / "self_assignment.v"
    source.write_text(DATA.read_text(encoding="utf-8"), encoding="utf-8")
    store_path = tmp / "verilinter.sqlite"

    analyze([source], store_path=store_path)

    calls: list[str] = []
    real_parse = run_lint_module.parse_file

    def track_parse(path: str, include_dirs=None):
        calls.append(path)
        return real_parse(path)

    monkeypatch.setattr(run_lint_module, "parse_file", track_parse)
    monkeypatch.setattr(analysis_store_module, "ANALYZER_CACHE_VERSION", "2026-08-28-test-bump")
    result = analyze([source], store_path=store_path)

    assert result.cache_stats == {"hits": 0, "misses": 1}
    assert calls == [str(source)]


def test_analyze_rejects_incompatible_schema_version() -> None:
    tmp = _scratch_dir("schema_mismatch")
    store_path = tmp / "verilinter.sqlite"

    analyze([PORT_DATA], store_path=store_path)

    conn = sqlite3.connect(store_path)
    try:
        conn.execute(
            "UPDATE schema_meta SET value = ? WHERE key = 'schema_version'",
            ("999",),
        )
        conn.commit()
    finally:
        conn.close()

    with pytest.raises(ValueError, match="schema version mismatch"):
        analyze([PORT_DATA], store_path=store_path)


def test_analyze_migrates_supported_older_schema_version() -> None:
    tmp = _scratch_dir("schema_migrate")
    store_path = tmp / "verilinter.sqlite"

    analyze([PORT_DATA], store_path=store_path)

    conn = sqlite3.connect(store_path)
    try:
        conn.execute(
            "UPDATE schema_meta SET value = ? WHERE key = 'schema_version'",
            ("0",),
        )
        conn.commit()
    finally:
        conn.close()

    result = analyze([PORT_DATA], store_path=store_path)
    assert result.cache_stats is not None

    conn = sqlite3.connect(store_path)
    try:
        version = conn.execute(
            "SELECT value FROM schema_meta WHERE key = 'schema_version'"
        ).fetchone()[0]
    finally:
        conn.close()

    assert version == analysis_store_module.SCHEMA_VERSION


def test_migrate_schema_1_to_2_preserves_rows_and_adds_cascade() -> None:
    tmp = _scratch_dir("schema_migrate_cascade")
    store_path = tmp / "verilinter.sqlite"

    analyze([PORT_DATA], store_path=store_path, fmt="text", report_kind="connections")

    conn = sqlite3.connect(store_path)
    try:
        conn.execute(
            "UPDATE schema_meta SET value = ? WHERE key = 'schema_version'",
            ("1",),
        )
        conn.commit()
        before = {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "analysis_run_files",
                "analysis_run_diagnostics",
                "analysis_run_modules",
                "analysis_run_instantiations",
                "analysis_run_connections",
            )
        }
    finally:
        conn.close()

    # Reopening the store triggers the 1 -> 2 migration.
    store = analysis_store_module.AnalysisStore(store_path)

    conn = sqlite3.connect(store_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        version = conn.execute("SELECT value FROM schema_meta WHERE key = 'schema_version'").fetchone()[0]
        assert version == analysis_store_module.SCHEMA_VERSION

        for table, expected_count in before.items():
            actual = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            assert actual == expected_count

        run_id = conn.execute("SELECT id FROM analysis_runs").fetchone()[0]
        conn.execute("DELETE FROM analysis_runs WHERE id = ?", (run_id,))
        conn.commit()

        for table in before:
            remaining = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            assert remaining == 0
    finally:
        conn.close()
    del store


def test_prune_cache_removes_entries_older_than_cutoff() -> None:
    tmp = _scratch_dir("prune_cache")
    store_path = tmp / "verilinter.sqlite"

    analyze([PORT_DATA], store_path=store_path)

    conn = sqlite3.connect(store_path)
    try:
        conn.execute(
            "UPDATE cached_file_analysis SET cached_at = ?",
            ((datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),),
        )
        conn.commit()
    finally:
        conn.close()

    store = analysis_store_module.AnalysisStore(store_path)
    removed = store.prune_cache(older_than_days=5)
    assert removed == 1

    conn = sqlite3.connect(store_path)
    try:
        remaining = conn.execute("SELECT COUNT(*) FROM cached_file_analysis").fetchone()[0]
    finally:
        conn.close()
    assert remaining == 0


def test_prune_cache_keeps_entries_within_cutoff() -> None:
    tmp = _scratch_dir("prune_cache_keep")
    store_path = tmp / "verilinter.sqlite"

    analyze([PORT_DATA], store_path=store_path)

    store = analysis_store_module.AnalysisStore(store_path)
    removed = store.prune_cache(older_than_days=5)
    assert removed == 0

    conn = sqlite3.connect(store_path)
    try:
        remaining = conn.execute("SELECT COUNT(*) FROM cached_file_analysis").fetchone()[0]
    finally:
        conn.close()
    assert remaining == 1


def test_prune_runs_keeps_last_n_and_removes_child_rows() -> None:
    tmp = _scratch_dir("prune_runs")
    store_path = tmp / "verilinter.sqlite"

    for _ in range(3):
        analyze([PORT_DATA], store_path=store_path, fmt="text", report_kind="connections")

    store = analysis_store_module.AnalysisStore(store_path)
    removed = store.prune_runs(keep_last=1)
    assert removed == 2

    conn = sqlite3.connect(store_path)
    try:
        run_ids = [row[0] for row in conn.execute("SELECT id FROM analysis_runs").fetchall()]
        assert len(run_ids) == 1
        remaining_id = run_ids[0]

        for table in (
            "analysis_run_files",
            "analysis_run_diagnostics",
            "analysis_run_modules",
            "analysis_run_instantiations",
            "analysis_run_connections",
        ):
            orphaned = conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE run_id != ?", (remaining_id,)
            ).fetchone()[0]
            assert orphaned == 0
    finally:
        conn.close()


def test_vacuum_store_preserves_data() -> None:
    tmp = _scratch_dir("vacuum")
    store_path = tmp / "verilinter.sqlite"

    analyze([PORT_DATA], store_path=store_path)
    store = analysis_store_module.AnalysisStore(store_path)
    store.vacuum()

    conn = sqlite3.connect(store_path)
    try:
        run_count = conn.execute("SELECT COUNT(*) FROM analysis_runs").fetchone()[0]
    finally:
        conn.close()
    assert run_count == 1
