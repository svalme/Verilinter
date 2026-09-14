"""Item 5 of the testing plan: verify the actual CLI/application boundary
(argv parsing -> config -> `parse_file`/`Walker.walk` -> the real rule
runners -> `render_diagnostics`) across execution modes, rather than the
parser-checked in-memory harness `lint_harness.py` uses.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from src.run_lint import main

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SELF_ASSIGNMENT_DATA = DATA_DIR / "self_assignment.v"
SCRATCH_ROOT = Path(__file__).resolve().parents[1] / "_tmp_cli_execution_modes"


def _prepare_scratch(name: str) -> Path:
    target = SCRATCH_ROOT / f"{name}_{uuid.uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def _normalized(diagnostics: list[dict]) -> list[tuple]:
    return sorted((d["code"], d["file"], d["line"], d["col"]) for d in diagnostics)


class TestSequentialVsParallelExecution:
    def test_jobs_one_and_jobs_four_agree_on_a_multi_file_directory(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        tmp = _prepare_scratch("jobs")
        for name in (
            "self_assignment.v",
            "port_connection_issues.sv",
            "port_connection_advanced.sv",
            "wildcard_port_connection.sv",
        ):
            (tmp / name).write_text((DATA_DIR / name).read_text(encoding="utf-8"), encoding="utf-8")

        main(["--format", "json", "--jobs", "1", str(tmp)])
        sequential = json.loads(capsys.readouterr().out)

        main(["--format", "json", "--jobs", "4", str(tmp)])
        parallel = json.loads(capsys.readouterr().out)

        assert sequential != []
        assert _normalized(sequential) == _normalized(parallel)


class TestRuleCategoryFiltering:
    def test_correctness_categories_alone_drop_naming_and_policy_checks(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        tmp = _prepare_scratch("category")
        source = tmp / "mixed.sv"
        source.write_text(
            """
`timescale 1ns/1ps
module mixed(input clk, output y);
  wire [3:0] narrow;
  assign narrow = 4'hFF;
  assign y = y;
endmodule
""".strip()
            + "\n",
            encoding="utf-8",
        )

        main(["--format", "json", str(source)])
        unfiltered_codes = {d["code"] for d in json.loads(capsys.readouterr().out)}
        assert {"PORT_DIRECTION_SUFFIX", "NO_SELF_ASSIGNMENT", "LITERAL_WIDTH_OVERFLOW"} <= unfiltered_codes

        main(
            [
                "--format",
                "json",
                "--category",
                "rtl_correctness",
                "--category",
                "semantic_correctness",
                "--category",
                "module_correctness",
                str(source),
            ]
        )
        filtered = json.loads(capsys.readouterr().out)
        filtered_codes = {d["code"] for d in filtered}

        # LITERAL_WIDTH_OVERFLOW (rtl_correctness) survives; the two rtl_style
        # naming/self-assignment checks are dropped.
        assert "LITERAL_WIDTH_OVERFLOW" in filtered_codes
        assert "PORT_DIRECTION_SUFFIX" not in filtered_codes
        assert "NO_SELF_ASSIGNMENT" not in filtered_codes
        assert all(
            d["category"] in {"rtl_correctness", "semantic_correctness", "module_correctness"} for d in filtered
        )


class TestOutputFormatConsistency:
    def test_text_json_and_sarif_agree_on_self_assignment_location(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        main(["--format", "text", str(SELF_ASSIGNMENT_DATA)])
        text_out = capsys.readouterr().out
        assert "8:9 - [NO_SELF_ASSIGNMENT] [WARNING] Self-assignment detected" in text_out

        main(["--format", "json", str(SELF_ASSIGNMENT_DATA)])
        json_out = json.loads(capsys.readouterr().out)
        json_entry = next(d for d in json_out if d["code"] == "NO_SELF_ASSIGNMENT")
        assert (json_entry["line"], json_entry["col"]) == (8, 9)
        assert json_entry["message"] == "Self-assignment detected"

        main(["--format", "sarif", str(SELF_ASSIGNMENT_DATA)])
        sarif_out = json.loads(capsys.readouterr().out)
        sarif_result = next(r for r in sarif_out["runs"][0]["results"] if r["ruleId"] == "NO_SELF_ASSIGNMENT")
        region = sarif_result["locations"][0]["physicalLocation"]["region"]
        assert (region["startLine"], region["startColumn"]) == (8, 9)
        assert sarif_result["message"]["text"] == "Self-assignment detected"


class TestMalformedInputHandling:
    def test_actual_syntax_error_is_silently_recovered_not_surfaced_or_failed(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Pins current behavior: `_lint_single_file` in `run_lint.py` calls
        `parse_file`/`Walker.walk` directly and does not inspect the parsed tree's
        own `.diagnostics` for parser errors. A genuine syntax error is absorbed by
        pyslang's parser recovery: the CLI exits 0 and reports only whatever
        ordinary lint findings the recovered AST produces. A future change that
        surfaces parser errors (as a diagnostic or a non-zero exit status) should
        update this test deliberately.
        """
        tmp = _prepare_scratch("malformed")
        source = tmp / "broken.sv"
        source.write_text(
            """
`timescale 1ns/1ps
module broken(input a, output y);
  assign y = a +;
endmodule
""".strip()
            + "\n",
            encoding="utf-8",
        )

        result = main(["--format", "json", str(source)])
        diagnostics = json.loads(capsys.readouterr().out)

        assert result == 0
        assert diagnostics != []
        assert {d["code"] for d in diagnostics} == {"PORT_DIRECTION_SUFFIX"}
        assert not any(
            "parse" in str(d["message"]).lower() or "syntax" in str(d["message"]).lower() for d in diagnostics
        )
