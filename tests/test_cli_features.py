from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import pytest

from src.run_lint import _parse_args, _resolve_config, main

DATA = Path(__file__).parent / "data" / "self_assignment.v"
PORT_DATA = Path(__file__).parent / "data" / "port_connection_issues.sv"
PORT_ADVANCED_DATA = Path(__file__).parent / "data" / "port_connection_advanced.sv"
WILDCARD_PORT_DATA = Path(__file__).parent / "data" / "wildcard_port_connection.sv"
SCRATCH_ROOT = Path(__file__).parent / "_tmp_cli_features"


def _prepare_scratch(name: str) -> Path:
    target = SCRATCH_ROOT / f"{name}_{uuid.uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def test_main_prints_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    result = main(["--format", "json", str(DATA)])

    captured = capsys.readouterr()
    assert result == 0
    payload = json.loads(captured.out)
    assert any(item["code"] == "NO_SELF_ASSIGNMENT" for item in payload)


def test_main_prints_sarif_output(capsys: pytest.CaptureFixture[str]) -> None:
    result = main(["--format", "sarif", str(DATA)])

    captured = capsys.readouterr()
    assert result == 0
    payload = json.loads(captured.out)
    assert payload["version"] == "2.1.0"
    assert payload["runs"][0]["tool"]["driver"]["name"] == "Verilinter"


def test_main_loads_default_config(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    tmp_path = _prepare_scratch("config")
    source = tmp_path / "self_assignment.v"
    source.write_text(DATA.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / ".verilinter.toml").write_text(
        """
[verilinter]
format = "json"
rules = ["NO_SELF_ASSIGNMENT"]

[verilinter.severity]
NO_SELF_ASSIGNMENT = "error"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    result = main([str(source)])

    captured = capsys.readouterr()
    assert result == 0
    payload = json.loads(captured.out)
    assert payload[0]["code"] == "NO_SELF_ASSIGNMENT"
    assert payload[0]["severity"] == "error"


def test_cli_format_overrides_config_to_text(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tmp_path = _prepare_scratch("format_override")
    source = tmp_path / "self_assignment.v"
    source.write_text(DATA.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / ".verilinter.toml").write_text(
        """
[verilinter]
format = "json"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    result = main(["--format", "text", str(source)])

    captured = capsys.readouterr()
    assert result == 0
    assert "NO_SELF_ASSIGNMENT" in captured.out
    with pytest.raises(json.JSONDecodeError):
        json.loads(captured.out)


def test_cli_jobs_overrides_config_to_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tmp_path = _prepare_scratch("jobs_override")
    source = tmp_path / "self_assignment.v"
    source.write_text(DATA.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / ".verilinter.toml").write_text(
        """
[verilinter]
jobs = 4
""".strip()
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    config = _resolve_config(_parse_args(["--jobs", "1", str(source)]))

    assert config.jobs == 1


def test_main_can_write_and_apply_baseline(
    capsys: pytest.CaptureFixture[str],
) -> None:
    tmp_path = _prepare_scratch("baseline")
    source = tmp_path / "self_assignment.v"
    source.write_text(DATA.read_text(encoding="utf-8"), encoding="utf-8")
    baseline = tmp_path / "baseline.json"

    write_result = main(["--write-baseline", str(baseline), str(source)])
    write_captured = capsys.readouterr()
    assert write_result == 0
    assert write_captured.out == ""
    assert baseline.exists()

    result = main(["--baseline", str(baseline), str(source)])
    captured = capsys.readouterr()
    assert result == 0
    assert "No issues found." in captured.out


def test_main_prints_connection_report(capsys: pytest.CaptureFixture[str]) -> None:
    result = main(["--report", "connections", str(PORT_DATA)])

    captured = capsys.readouterr()
    assert result == 0
    assert "Module Connection Summary" in captured.out
    assert "top -> child (u_unconn)" in captured.out
    assert "y: <unconnected>" in captured.out


def test_connection_report_mentions_unknown_width_and_bad_port(capsys: pytest.CaptureFixture[str]) -> None:
    result = main(["--report", "connections", str(PORT_ADVANCED_DATA)])

    captured = capsys.readouterr()
    assert result == 0
    assert "unknown child port qq" in captured.out
    assert "cannot infer width" in captured.out


def test_connection_report_mentions_wildcard_and_ordered_style_issues(capsys: pytest.CaptureFixture[str]) -> None:
    wildcard_result = main(["--report", "connections", str(WILDCARD_PORT_DATA)])
    wildcard_captured = capsys.readouterr()
    assert wildcard_result == 0
    assert "uses wildcard port connections" in wildcard_captured.out
    assert "<wildcard port binding: explicit per-port mapping not expanded>" in wildcard_captured.out

    ordered_result = main(["--report", "connections", str(PORT_ADVANCED_DATA)])
    ordered_captured = capsys.readouterr()
    assert ordered_result == 0
    assert "uses ordered port connections" in ordered_captured.out
    assert "uses ordered parameter overrides" in ordered_captured.out
