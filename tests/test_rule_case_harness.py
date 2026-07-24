from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .support.lint_harness import LintCaseFile, LintCaseResult


def test_lint_case_supports_single_file_false_negative_checks(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "single.v": """
            module top;
              wire a;
              assign a = 1'b0;
            endmodule
            """
        }
    )

    result.expect_no_code("NO_IMPLICIT_NET")


def test_lint_case_supports_multi_file_cross_file_rules(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "a.sv": """
            module a;
              b u_b();
            endmodule
            """,
            "b.sv": """
            module b;
              a u_a();
            endmodule
            """,
        }
    )

    result.expect_code_once("CIRCULAR_MODULE_INSTANTIATION")
    result.expect_message_contains("CIRCULAR_MODULE_INSTANTIATION", "a")
    result.expect_message_contains("CIRCULAR_MODULE_INSTANTIATION", "b")


def test_lint_case_supports_false_positive_checks(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "clean.sv": """
            module top(input logic a, input logic b, output logic y);
              always_comb begin
                y = a & b;
              end
            endmodule
            """
        }
    )

    result.expect_no_code("NO_INCOMPLETE_SENSITIVITY_LIST")


def test_temp_file_harness_preserves_generated_file_names(
    lint_temp_file_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_temp_file_case(
        {
            "a.sv": """
            module dup_mod;
              real unused_sig;
            endmodule
            """,
            "b.sv": """
            module dup_mod;
              real unused_sig;
            endmodule
            """,
        }
    )

    result.expect_files_for_code("UNUSED_VARIABLE", {"a.sv", "b.sv"})
    result.expect_files_for_code("DUPLICATE_MODULE", {"b.sv"})


def test_temp_file_harness_cleans_up_generated_case_directories(
    lint_temp_file_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    scratch_root = Path(__file__).parent / "_tmp_harness"

    result = lint_temp_file_case(
        {
            "cleanup.sv": """
            module top;
              wire a;
              assign a = 1'b0;
            endmodule
            """
        }
    )

    result.expect_no_code("NO_IMPLICIT_NET")
    leftover_cases = [
        path for path in scratch_root.iterdir() if path.is_dir()
    ] if scratch_root.exists() else []
    assert leftover_cases == []


def test_inline_case_spec_can_route_default_nettype_none_to_undeclared_variable(
    lint_inline_case_spec: Callable[[dict[str, LintCaseFile]], LintCaseResult],
) -> None:
    result = lint_inline_case_spec(
        {
            "default_nettype_none.sv": LintCaseFile(
                contents="""
                module top;
                  assign y = a;
                endmodule
                """,
                default_nettype_none=True,
            )
        }
    )

    result.expect_no_code("NO_IMPLICIT_NET")
    result.expect_code_count("UNDECLARED_VARIABLE", 2)
