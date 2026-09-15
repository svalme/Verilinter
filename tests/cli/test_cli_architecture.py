from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from src.pkg.analysis_store import AnalysisStore
from src.run_lint import AnalysisResult, WorkerResult, analyze, collect_paths, main, run

DATA = Path(__file__).resolve().parents[1] / "data" / "self_assignment.v"
CLEAN_DATA = Path(__file__).resolve().parents[1] / "data" / "simple.v"
SYNTAX_ERROR_DATA = Path(__file__).resolve().parents[1] / "data" / "syntax_error.v"
SCRATCH_ROOT = Path(__file__).resolve().parents[1] / "_tmp_cli_architecture"


def _scratch(name: str) -> Path:
    target = SCRATCH_ROOT / f"{name}_{uuid.uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


# ==============================================================================
# 5.1: Direct Output File Flag (-o / --output)
# ==============================================================================


def test_output_flag_writes_text_to_file(capsys: pytest.CaptureFixture[str]) -> None:
    scratch = _scratch("text_out")
    out_file = scratch / "reports" / "report.txt"

    code = main(["--output", str(out_file), str(DATA)])

    assert code == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert out_file.is_file()
    content = out_file.read_text(encoding="utf-8")
    assert "NO_SELF_ASSIGNMENT" in content


def test_output_flag_writes_json_to_file(capsys: pytest.CaptureFixture[str]) -> None:
    scratch = _scratch("json_out")
    out_file = scratch / "report.json"

    code = main(["-o", str(out_file), "--format", "json", str(DATA)])

    assert code == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert out_file.is_file()
    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert any(item["code"] == "NO_SELF_ASSIGNMENT" for item in payload)


def test_output_flag_writes_sarif_to_file(capsys: pytest.CaptureFixture[str]) -> None:
    scratch = _scratch("sarif_out")
    out_file = scratch / "results.sarif"

    code = main(["-o", str(out_file), "--format", "sarif", str(DATA)])

    assert code == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert out_file.is_file()
    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["version"] == "2.1.0"
    assert payload["runs"][0]["tool"]["driver"]["name"] == "Verilinter"


PORT_DATA = Path(__file__).resolve().parents[1] / "data" / "port_connection_advanced.sv"


def test_output_flag_writes_connection_report_to_file(capsys: pytest.CaptureFixture[str]) -> None:
    scratch = _scratch("connections_out")
    out_file = scratch / "connections.txt"

    code = main(["-o", str(out_file), "--report", "connections", str(PORT_DATA)])

    assert code == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert out_file.is_file()
    content = out_file.read_text(encoding="utf-8")
    assert "Module Connection Summary" in content


# ==============================================================================
# 5.2: CI Exit Code Semantics (--fail-on-error, --fail-on-warning, --exit-zero)
# ==============================================================================


def test_default_exit_code_is_zero_for_rule_warnings() -> None:
    code = main([str(DATA)])
    assert code == 0


def test_default_exit_code_is_zero_for_rule_errors_without_fail_on_error() -> None:
    code = main(["--severity", "NO_SELF_ASSIGNMENT=error", str(DATA)])
    assert code == 0


def test_fail_on_error_returns_one_when_errors_present() -> None:
    code = main(["--fail-on-error", "--severity", "NO_SELF_ASSIGNMENT=error", str(DATA)])
    assert code == 1


def test_fail_on_error_returns_zero_when_only_warnings_present() -> None:
    code = main(["--fail-on-error", str(DATA)])
    assert code == 0


def test_fail_on_warning_returns_one_when_warnings_present() -> None:
    code = main(["--fail-on-warning", str(DATA)])
    assert code == 1


def test_fail_on_warning_returns_zero_on_clean_file() -> None:
    scratch = _scratch("clean_file")
    clean = scratch / "clean.v"
    clean.write_text("`timescale 1ns/1ps\nmodule clean;\nendmodule\n", encoding="utf-8")
    code = main(["--fail-on-warning", "--profile", "legacy_verilog", str(clean)])
    assert code == 0


def test_exit_zero_suppresses_parser_error_exit_code() -> None:
    scratch = _scratch("syntax_err")
    bad = scratch / "bad.v"
    bad.write_text("module bad (;\nendmodule\n", encoding="utf-8")
    assert main([str(bad)]) == 1
    assert main(["--exit-zero", str(bad)]) == 0


def test_exit_zero_suppresses_fail_on_error_exit_code() -> None:
    code = main([
        "--fail-on-error",
        "--severity", "NO_SELF_ASSIGNMENT=error",
        "--exit-zero",
        str(DATA),
    ])
    assert code == 0


def test_fail_on_error_via_config_file(monkeypatch: pytest.MonkeyPatch) -> None:
    scratch = _scratch("cfg_exit_code")
    src = scratch / "self_assignment.v"
    src.write_text(DATA.read_text(encoding="utf-8"), encoding="utf-8")
    cfg = scratch / ".verilinter.toml"
    cfg.write_text(
        """
[verilinter]
fail_on_error = true

[verilinter.severity]
NO_SELF_ASSIGNMENT = "error"
""".strip() + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(scratch)

    code = main([str(src)])
    assert code == 1


# ==============================================================================
# 5.3: Store Subcommand Architecture (verilinter store ...)
# ==============================================================================


def test_store_subcommand_status(capsys: pytest.CaptureFixture[str]) -> None:
    scratch = _scratch("store_subcommand")
    store_db = scratch / "analysis.db"

    # Populate store with a run
    main(["--store", str(store_db), str(CLEAN_DATA)])
    assert store_db.is_file()
    capsys.readouterr()

    # Query status via subcommand
    code = main(["store", "status", "--store", str(store_db)])
    assert code == 0

    captured = capsys.readouterr()
    status_data = json.loads(captured.out)
    assert status_data["recorded_runs"] >= 1
    assert status_data["cached_files"] >= 1
    assert status_data["size_bytes"] > 0


def test_store_subcommand_prune_and_vacuum(capsys: pytest.CaptureFixture[str]) -> None:
    scratch = _scratch("store_prune")
    store_db = scratch / "analysis.db"
    main(["--store", str(store_db), str(CLEAN_DATA)])

    # Prune cache records
    code_prune = main(["store", "prune", "--days", "0", "--store", str(store_db)])
    assert code_prune == 0
    assert "Pruned" in capsys.readouterr().out

    # Prune runs
    code_runs = main(["store", "prune-runs", "--keep", "0", "--store", str(store_db)])
    assert code_runs == 0
    assert "Pruned" in capsys.readouterr().out

    # Vacuum
    code_vacuum = main(["store", "vacuum", "--store", str(store_db)])
    assert code_vacuum == 0
    assert "Vacuumed" in capsys.readouterr().out


def test_store_subcommand_requires_store_path(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["store", "vacuum"])
    assert code == 1
    assert "Error: --store path is required" in capsys.readouterr().err


def test_legacy_store_flags_still_supported(capsys: pytest.CaptureFixture[str]) -> None:
    scratch = _scratch("legacy_store")
    store_db = scratch / "analysis.db"
    main(["--store", str(store_db), str(CLEAN_DATA)])

    code = main(["--vacuum-store", "--store", str(store_db)])
    assert code == 0
    assert "Vacuumed store." in capsys.readouterr().out


# ==============================================================================
# 5.4: Decoupled Engine Interface
# ==============================================================================


def test_engine_analyze_called_directly() -> None:
    result = analyze([CLEAN_DATA])
    assert isinstance(result, AnalysisResult)
    assert isinstance(result.diagnostics, list)
    assert hasattr(result, "symbol_table")


def test_engine_run_called_directly() -> None:
    diags = run([DATA])
    assert isinstance(diags, list)
    assert any(d["code"] == "NO_SELF_ASSIGNMENT" for d in diags)


def test_engine_collect_paths_handles_exclusions() -> None:
    found = collect_paths([str(CLEAN_DATA)], exclude=["*simple.v"])
    assert found == []
