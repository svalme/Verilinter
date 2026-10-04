"""Unit tests for the lint testing harness and LintCaseResult assertion helpers."""
from __future__ import annotations

from pathlib import Path
import pytest

from tests.support.lint_harness import (
    Diagnostic,
    LintCaseResult,
    run_inline_lint_case,
    run_paired_lint_case,
)


def _diag(
    code: str = "RULE_A",
    line: int = 10,
    col: int = 5,
    file: str = "test.sv",
    message: str = "Violation message",
) -> Diagnostic:
    return {
        "code": code,
        "line": line,
        "col": col,
        "file": file,
        "message": message,
    }


def test_expect_clean_passes_on_empty() -> None:
    result = LintCaseResult(diagnostics=[])
    result.expect_clean()
    result.expect_empty()


def test_expect_clean_fails_on_non_empty() -> None:
    result = LintCaseResult(diagnostics=[_diag()])
    with pytest.raises(AssertionError, match="Expected clean lint result"):
        result.expect_clean()


def test_expect_diagnostics_empty_expected_passes_on_empty() -> None:
    result = LintCaseResult(diagnostics=[])
    result.expect_diagnostics([])


def test_expect_diagnostics_empty_expected_fails_on_non_empty() -> None:
    result = LintCaseResult(diagnostics=[_diag()])
    with pytest.raises(AssertionError, match="Expected 0 diagnostics"):
        result.expect_diagnostics([])


def test_expect_diagnostics_line_and_code_tuples() -> None:
    result = LintCaseResult(
        diagnostics=[
            _diag(code="RULE_A", line=12),
            _diag(code="RULE_B", line=5),
        ]
    )
    # Default sort=True checks sorted order regardless of actual order
    result.expect_diagnostics([(5, "RULE_B"), (12, "RULE_A")])
    result.expect_diagnostics([(12, "RULE_A"), (5, "RULE_B")])

    with pytest.raises(AssertionError, match="Diagnostic expectation mismatch"):
        result.expect_diagnostics([(5, "RULE_A"), (12, "RULE_B")])


def test_expect_diagnostics_line_col_code_tuples() -> None:
    result = LintCaseResult(
        diagnostics=[
            _diag(code="RULE_A", line=10, col=2),
            _diag(code="RULE_A", line=10, col=8),
        ]
    )
    result.expect_diagnostics([(10, 2, "RULE_A"), (10, 8, "RULE_A")])

    with pytest.raises(AssertionError, match="Diagnostic expectation mismatch"):
        result.expect_diagnostics([(10, 3, "RULE_A"), (10, 8, "RULE_A")])


def test_expect_diagnostics_file_line_code_tuples() -> None:
    result = LintCaseResult(
        diagnostics=[
            _diag(code="RULE_X", line=3, file="foo.sv"),
            _diag(code="RULE_Y", line=7, file="bar.sv"),
        ]
    )
    result.expect_diagnostics([("foo.sv", 3, "RULE_X"), ("bar.sv", 7, "RULE_Y")])

    with pytest.raises(AssertionError, match="Diagnostic expectation mismatch"):
        result.expect_diagnostics([("baz.sv", 3, "RULE_X"), ("bar.sv", 7, "RULE_Y")])


def test_expect_diagnostics_file_line_col_code_tuples() -> None:
    result = LintCaseResult(
        diagnostics=[
            _diag(code="RULE_Z", line=20, col=4, file="dir/mod.sv"),
        ]
    )
    result.expect_diagnostics([("mod.sv", 20, 4, "RULE_Z")])


def test_expect_diagnostics_code_strings() -> None:
    result = LintCaseResult(
        diagnostics=[
            _diag(code="ALPHA"),
            _diag(code="BETA"),
        ]
    )
    result.expect_diagnostics(["ALPHA", "BETA"])

    with pytest.raises(AssertionError, match="Diagnostic expectation mismatch"):
        result.expect_diagnostics(["ALPHA"])


def test_expect_diagnostics_with_filter_code() -> None:
    result = LintCaseResult(
        diagnostics=[
            _diag(code="RULE_A", line=10),
            _diag(code="RULE_B", line=15),
            _diag(code="RULE_A", line=20),
        ]
    )
    result.expect_diagnostics([(10, "RULE_A"), (20, "RULE_A")], filter_code="RULE_A")
    result.expect_diagnostics([(15, "RULE_B")], filter_code="RULE_B")
    result.expect_diagnostics([], filter_code="NONEXISTENT")


def test_expect_diagnostics_with_filter_file() -> None:
    result = LintCaseResult(
        diagnostics=[
            _diag(code="RULE_A", line=5, file="a.sv"),
            _diag(code="RULE_B", line=8, file="b.sv"),
        ]
    )
    result.expect_diagnostics([(5, "RULE_A")], filter_file="a.sv")
    result.expect_diagnostics([(8, "RULE_B")], filter_file="b.sv")


def test_expect_diagnostics_unsupported_shape_raises() -> None:
    result = LintCaseResult(diagnostics=[_diag()])
    with pytest.raises(ValueError, match="Unsupported diagnostic expectation shape"):
        result.expect_diagnostics([12345])  # type: ignore[list-item]


def test_run_paired_lint_case_clean_parity(tmp_path: Path) -> None:
    result = run_paired_lint_case(
        {
            "valid.sv": """
            `timescale 1ns/1ps
            module valid_mod(input logic clk_i);
            endmodule
            """
        },
        tmp_path=tmp_path,
    )
    # The snippet only produces standard naming warnings if enabled
    assert isinstance(result, LintCaseResult)


def test_run_paired_lint_case_with_diagnostics_parity(tmp_path: Path) -> None:
    files = {
        "m1.sv": """
        module m1(input logic [3:0] in_i, output logic out_o);
          assign out_o = in_i[10];
        endmodule
        """,
        "m2.sv": """
        module m2(input logic [7:0] data_i, output logic [7:0] data_o);
          assign data_o = data_i[0 +: -1];
        endmodule
        """,
    }
    result = run_paired_lint_case(files, tmp_path=tmp_path)
    assert result.for_code("CONSTANT_INDEX_OUT_OF_RANGE") != []
    assert result.for_code("INDEXED_PART_SELECT_WIDTH") != []


def test_expect_diagnostics_inconsistent_shapes_raises() -> None:
    result = LintCaseResult(diagnostics=[_diag(line=10, code="RULE_A"), _diag(line=20, code="RULE_B")])
    with pytest.raises(ValueError, match="Inconsistent expectation shapes in expect_diagnostics"):
        result.expect_diagnostics([(10, "RULE_A"), ("test.sv", 20, "RULE_B")])  # type: ignore[list-item]


def test_expect_diagnostics_strict_tuple_type_check_raises() -> None:
    result = LintCaseResult(diagnostics=[_diag()])
    with pytest.raises(ValueError, match="Unsupported diagnostic expectation shape"):
        result.expect_diagnostics([(10, 20)])  # type: ignore[list-item]


def test_run_paired_lint_case_with_duplicate_module_and_subdirectories(tmp_path: Path) -> None:
    files = {
        "sub/first.sv": "module dup_across_files; endmodule",
        "sub/second.sv": "module dup_across_files; endmodule",
    }
    result = run_paired_lint_case(files, tmp_path=tmp_path)
    assert result.for_code("DUPLICATE_MODULE") != []

