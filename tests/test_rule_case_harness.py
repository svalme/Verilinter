from __future__ import annotations

from collections.abc import Callable

from .support.lint_harness import LintCaseResult


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

    assert result.for_code("NO_IMPLICIT_NET") == []


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

    circular = result.for_code("CIRCULAR_MODULE_INSTANTIATION")
    assert len(circular) == 1
    assert "a" in str(circular[0]["message"])
    assert "b" in str(circular[0]["message"])


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

    assert result.for_code("NO_INCOMPLETE_SENSITIVITY_LIST") == []
