from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.pkg.diagnostics import VALID_CONFIDENCES, enrich_diagnostics, metadata_by_code
from src.pkg.output import format_sarif, format_summary
from src.pkg.version import tool_version
from src.run_lint import main

DATA = Path(__file__).resolve().parents[1] / "data" / "self_assignment.v"


def _diag(code: str, severity: str, file: str = "a.v") -> dict:
    return {"code": code, "severity": severity, "file": file, "line": 1, "col": 1, "message": "m"}


class TestConfidence:
    def test_every_rule_declares_a_valid_confidence(self) -> None:
        for code, item in metadata_by_code().items():
            assert item.confidence in VALID_CONFIDENCES, code

    @pytest.mark.parametrize(
        ("code", "expected"),
        [
            ("EXPLICIT_XZ_LITERAL", "definite"),
            ("COMPARISON_ALWAYS_CONSTANT", "heuristic"),
            ("PORT_CONNECTION_WIDTH_UNKNOWN", "analysis_limit"),
            ("PARSER_ERROR", "definite"),
        ],
    )
    def test_reviewed_rules_report_their_confidence(self, code: str, expected: str) -> None:
        assert metadata_by_code()[code].confidence == expected

    def test_unreviewed_is_the_default_for_unclassified_rules(self) -> None:
        enriched = enrich_diagnostics([{"code": "NOT_A_RULE", "line": 1, "col": 1, "message": "m"}])
        assert enriched[0]["confidence"] == "unreviewed"

    def test_json_and_sarif_carry_confidence(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["--format", "json", str(DATA)]) == 0
        findings = json.loads(capsys.readouterr().out)
        assert findings and all(item["confidence"] in VALID_CONFIDENCES for item in findings)

        assert main(["--format", "sarif", str(DATA)]) == 0
        run = json.loads(capsys.readouterr().out)["runs"][0]
        assert all("confidence" in result["properties"] for result in run["results"])
        assert all("confidence" in rule["properties"] for rule in run["tool"]["driver"]["rules"])


class TestSummary:
    def test_counts_by_severity_files_and_suppressed(self) -> None:
        diagnostics = [_diag("A", "warning"), _diag("B", "warning", "b.v"), _diag("C", "info")]
        text = format_summary(diagnostics, file_count=5, version="1.2.3", suppressed=2)
        assert text == "Verilinter 1.2.3: 3 findings in 2 of 5 files (0 error, 2 warning, 1 info); 2 suppressed by baseline.\n"

    def test_empty_run_and_singular_nouns(self) -> None:
        assert format_summary([], 1, "1.2.3") == "Verilinter 1.2.3: no findings in 1 file.\n"
        assert "1 finding in 1 of 1 file (" in format_summary([_diag("A", "warning")], 1, "1.2.3")

    def test_parse_failures_are_counted_by_file(self) -> None:
        diagnostics = [_diag("PARSER_ERROR", "error"), _diag("PARSER_ERROR", "error"), _diag("A", "warning", "b.v")]
        assert format_summary(diagnostics, 2, "1.2.3").endswith("; 1 file failed to parse.\n")

    def test_text_run_prints_the_summary_on_stderr_only(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["--format", "text", str(DATA)]) == 0
        captured = capsys.readouterr()
        assert captured.err.startswith(f"Verilinter {tool_version()}:")
        assert "Verilinter" not in captured.out

    def test_json_run_prints_no_summary(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["--format", "json", str(DATA)]) == 0
        assert "Verilinter" not in capsys.readouterr().err

    def test_tool_version_is_not_unknown_in_a_checkout(self) -> None:
        assert tool_version() != "unknown"
