from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from src.pkg.analysis_store import AnalysisStore, SCHEMA_VERSION, file_sha256
from src.pkg.config import LintConfig, config_from_cli, load_config, merge_config
from src.pkg.parser.parse import extract_header_dependencies, parse_file, parse_text
from src.run_lint import analyze, main


def test_preprocessor_defines_conditional_compilation() -> None:
    # Test `ifdef conditional logic with defines passed to parser
    text_ifdef = """
    `ifdef FEATURE_ENABLED
    module alpha_mod;
    endmodule
    `else
    module beta_mod;
    endmodule
    `endif
    """
    tree_without = parse_text(text_ifdef)
    assert "beta_mod" in str(tree_without.root)
    assert "alpha_mod" not in str(tree_without.root)

    tree_with = parse_text(text_ifdef, defines=["FEATURE_ENABLED"])
    assert "alpha_mod" in str(tree_with.root)
    assert "beta_mod" not in str(tree_with.root)


def test_header_dependency_extraction(tmp_path: Path) -> None:
    inc_dir = tmp_path / "includes"
    inc_dir.mkdir()
    header_b = inc_dir / "header_b.vh"
    header_b.write_text("`define VALUE_B 42\n", encoding="utf-8")

    header_a = inc_dir / "header_a.vh"
    header_a.write_text('`include "header_b.vh"\n`define VALUE_A 10\n', encoding="utf-8")

    top_file = tmp_path / "top.sv"
    top_file.write_text(
        '`include "header_a.vh"\n'
        "module top;\n"
        "  initial begin\n"
        "    $display(`VALUE_A, `VALUE_B);\n"
        "  end\n"
        "endmodule\n",
        encoding="utf-8",
    )

    tree = parse_file(str(top_file), include_dirs=[str(inc_dir)])
    deps = extract_header_dependencies(tree)

    paths = [d["path"] for d in deps]
    assert str(header_a.resolve()) in paths
    assert str(header_b.resolve()) in paths

    dep_b = next(d for d in deps if d["path"] == str(header_b.resolve()))
    assert dep_b["hash"] == file_sha256(header_b)


def test_cache_hit_and_invalidation_on_direct_header_modification(tmp_path: Path) -> None:
    inc_dir = tmp_path / "inc"
    inc_dir.mkdir()
    header = inc_dir / "common.vh"
    header.write_text("`define DATA_WIDTH 16\n", encoding="utf-8")

    source = tmp_path / "module.sv"
    source.write_text(
        '`include "common.vh"\n'
        "module my_mod;\n"
        "  logic [`DATA_WIDTH-1:0] data;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    store_path = tmp_path / "analysis.sqlite"

    # First run: cold cache miss
    res1 = analyze([source], include_dirs=[str(inc_dir)], store_path=store_path)
    assert res1.cache_stats == {"hits": 0, "misses": 1}

    # Verify header_dependencies_json was persisted
    conn = sqlite3.connect(store_path)
    try:
        row = conn.execute("SELECT header_dependencies_json FROM cached_file_analysis").fetchone()
        assert row is not None
        deps = json.loads(row[0])
        assert len(deps) == 1
        assert deps[0]["path"] == str(header.resolve())
    finally:
        conn.close()

    # Second run: warm cache hit
    res2 = analyze([source], include_dirs=[str(inc_dir)], store_path=store_path)
    assert res2.cache_stats == {"hits": 1, "misses": 0}

    # Modify header: cache must be invalidated
    header.write_text("`define DATA_WIDTH 32\n", encoding="utf-8")
    res3 = analyze([source], include_dirs=[str(inc_dir)], store_path=store_path)
    assert res3.cache_stats == {"hits": 0, "misses": 1}

    # Subsequent run: cache hit again with updated header hash
    res4 = analyze([source], include_dirs=[str(inc_dir)], store_path=store_path)
    assert res4.cache_stats == {"hits": 1, "misses": 0}


def test_cache_invalidation_on_transitive_nested_header_modification(tmp_path: Path) -> None:
    inc_dir = tmp_path / "inc"
    inc_dir.mkdir()
    leaf = inc_dir / "leaf.vh"
    leaf.write_text("`define LEAF_VAL 1\n", encoding="utf-8")

    mid = inc_dir / "mid.vh"
    mid.write_text('`include "leaf.vh"\n`define MID_VAL 2\n', encoding="utf-8")

    source = tmp_path / "top.sv"
    source.write_text(
        '`include "mid.vh"\n'
        "module top;\n"
        "  wire [31:0] w;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    store_path = tmp_path / "analysis.sqlite"

    # 1. Warm up cache
    res1 = analyze([source], include_dirs=[str(inc_dir)], store_path=store_path)
    assert res1.cache_stats == {"hits": 0, "misses": 1}

    # 2. Confirm hit
    res2 = analyze([source], include_dirs=[str(inc_dir)], store_path=store_path)
    assert res2.cache_stats == {"hits": 1, "misses": 0}

    # 3. Modify only the transitive leaf header (neither top.sv nor mid.vh modified)
    leaf.write_text("`define LEAF_VAL 99\n", encoding="utf-8")

    res3 = analyze([source], include_dirs=[str(inc_dir)], store_path=store_path)
    assert res3.cache_stats == {"hits": 0, "misses": 1}


def test_cache_invalidation_on_header_deletion(tmp_path: Path) -> None:
    inc_dir = tmp_path / "inc"
    inc_dir.mkdir()
    header = inc_dir / "temp.vh"
    header.write_text("`define TEMP 1\n", encoding="utf-8")

    source = tmp_path / "test.sv"
    source.write_text(
        '`include "temp.vh"\n'
        "module test;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    store_path = tmp_path / "analysis.sqlite"

    res1 = analyze([source], include_dirs=[str(inc_dir)], store_path=store_path)
    assert res1.cache_stats == {"hits": 0, "misses": 1}

    # Delete header
    header.unlink()

    # Re-analyzing must detect missing dependency and not reuse stale cache
    res2 = analyze([source], include_dirs=[str(inc_dir)], store_path=store_path)
    assert res2.cache_stats == {"hits": 0, "misses": 1}


def test_cache_invalidation_on_define_changes(tmp_path: Path) -> None:
    source = tmp_path / "mod.sv"
    source.write_text(
        "`ifdef FAST\n"
        "module mod_fast;\n"
        "endmodule\n"
        "`else\n"
        "module mod_slow;\n"
        "endmodule\n"
        "`endif\n",
        encoding="utf-8",
    )
    store_path = tmp_path / "analysis.sqlite"

    # Run with defines=["FAST"]
    res1 = analyze([source], defines=["FAST"], store_path=store_path)
    assert res1.cache_stats == {"hits": 0, "misses": 1}

    # Repeat with same defines -> hit
    res2 = analyze([source], defines=["FAST"], store_path=store_path)
    assert res2.cache_stats == {"hits": 1, "misses": 0}

    # Run with different defines -> miss
    res3 = analyze([source], defines=["SLOW"], store_path=store_path)
    assert res3.cache_stats == {"hits": 0, "misses": 1}

    # Run with no defines -> miss
    res4 = analyze([source], defines=None, store_path=store_path)
    assert res4.cache_stats == {"hits": 0, "misses": 1}

    # Run with multiple defines in different order -> hit (order-independent)
    res5 = analyze([source], defines=["A=1", "B=2"], store_path=store_path)
    assert res5.cache_stats == {"hits": 0, "misses": 1}

    res6 = analyze([source], defines=["B=2", "A=1"], store_path=store_path)
    assert res6.cache_stats == {"hits": 1, "misses": 0}


def test_schema_migration_v2_to_v3(tmp_path: Path) -> None:
    store_path = tmp_path / "migrated.sqlite"
    conn = sqlite3.connect(store_path)
    try:
        # Construct schema version 2
        conn.executescript(
            """
            CREATE TABLE schema_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            INSERT INTO schema_meta (key, value) VALUES ('schema_version', '2');
            CREATE TABLE cached_file_analysis (
                file_path TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                selection_key TEXT NOT NULL,
                include_dirs_key TEXT NOT NULL,
                package_registry_fingerprint TEXT NOT NULL,
                worker_result_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (file_path, file_hash, selection_key, include_dirs_key, package_registry_fingerprint)
            );
            INSERT INTO cached_file_analysis VALUES (
                'test.sv', 'hash123', 'sel', 'inc', 'pkg', '{}', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'
            );
            """
        )
        conn.commit()
    finally:
        conn.close()

    # Open store with AnalysisStore -> triggers migration to 3
    store = AnalysisStore(store_path)
    assert SCHEMA_VERSION == "3"

    conn = sqlite3.connect(store_path)
    try:
        # Check version is 3
        version_row = conn.execute("SELECT value FROM schema_meta WHERE key = 'schema_version'").fetchone()
        assert version_row[0] == "3"

        # Check column exists
        columns = [row[1] for row in conn.execute("PRAGMA table_info(cached_file_analysis)").fetchall()]
        assert "header_dependencies_json" in columns

        # Check existing row was backfilled with '[]'
        row = conn.execute("SELECT header_dependencies_json FROM cached_file_analysis").fetchone()
        assert row[0] == "[]"
    finally:
        conn.close()


def test_lint_config_defines_support(tmp_path: Path) -> None:
    toml_path = tmp_path / ".verilinter.toml"
    toml_path.write_text(
        'defines = ["SYNTHESIS", "WIDTH=32"]\n'
        'jobs = 2\n',
        encoding="utf-8",
    )

    config = load_config(toml_path)
    assert config.defines == ("SYNTHESIS", "WIDTH=32")
    assert config.defines_explicit is True

    # Test CLI override merges or replaces
    cli_cfg = config_from_cli(
        profile=None,
        rules=None,
        categories=None,
        defines=["SIMULATION"],
        fmt=None,
        jobs=None,
        severity=None,
        baseline=None,
        store=None,
        no_cache=False,
    )
    assert cli_cfg.defines == ("SIMULATION",)
    assert cli_cfg.defines_explicit is True

    merged = merge_config(config, cli_cfg)
    assert merged.defines == ("SIMULATION",)
    assert merged.jobs == 2


def test_cli_define_flags_integration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    source = tmp_path / "top.sv"
    source.write_text(
        "`ifdef REQUIRE_MACRO\n"
        "module top;\n"
        "endmodule\n"
        "`else\n"
        "module top(input wire clk, output reg y);\n"
        "  reg tmp;\n"
        "  always @(posedge clk) begin\n"
        "    tmp <= tmp;\n"
        "    y <= tmp;\n"
        "  end\n"
        "endmodule\n"
        "`endif\n",
        encoding="utf-8",
    )

    # Run without -D: triggers NO_SELF_ASSIGNMENT warning
    rc = main([str(source), "--format", "json"])
    out = capsys.readouterr().out
    assert rc == 0
    data = json.loads(out)
    assert any(d.get("code") == "NO_SELF_ASSIGNMENT" for d in data)

    # Run with -D REQUIRE_MACRO: clean module, no NO_SELF_ASSIGNMENT
    rc2 = main([str(source), "-D", "REQUIRE_MACRO", "--format", "json"])
    out2 = capsys.readouterr().out
    assert rc2 == 0
    data2 = json.loads(out2)
    assert not any(d.get("code") == "NO_SELF_ASSIGNMENT" for d in data2)
