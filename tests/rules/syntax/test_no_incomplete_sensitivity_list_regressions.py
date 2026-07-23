from __future__ import annotations

from collections.abc import Callable

import pytest

from ...support.lint_harness import LintCaseResult


@pytest.mark.xfail(
    strict=True,
    reason="Identifiers used as selectors inside assignment LHS expressions are still misclassified as write-only.",
)
def test_flags_selector_read_on_assignment_lhs_when_missing_from_sensitivity_list(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "selector_read.sv": """
            module top(input logic [3:0] x, input logic [1:0] b, input logic c);
              logic [3:0] y;
              always @(c) begin
                y[b] = c;
              end
            endmodule
            """
        }
    )

    diagnostics = result.for_code("NO_INCOMPLETE_SENSITIVITY_LIST")
    assert len(diagnostics) == 1
    assert "b" in str(diagnostics[0]["message"])


@pytest.mark.xfail(
    strict=True,
    reason="Explicit sensitivity expressions currently under-collect identifiers from compound event expressions.",
)
def test_does_not_flag_identifiers_already_covered_inside_compound_sensitivity_expression(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "compound_event.sv": """
            module top(input logic [3:0] a, input logic [1:0] sel, output logic y);
              always @(a[sel]) begin
                y = a[sel];
              end
            endmodule
            """
        }
    )

    assert result.for_code("NO_INCOMPLETE_SENSITIVITY_LIST") == []
