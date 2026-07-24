from __future__ import annotations

from collections.abc import Callable

from .support.lint_harness import LintCaseFile, LintCaseResult


def test_default_nettype_none_routes_unresolved_names_to_undeclared_not_implicit(
    lint_inline_case_spec: Callable[[dict[str, LintCaseFile]], LintCaseResult],
) -> None:
    result = lint_inline_case_spec(
        {
            "default_nettype_none.sv": LintCaseFile(
                contents="""
                module top;
                  always_comb begin
                    y = a;
                  end
                endmodule
                """,
                default_nettype_none=True,
            )
        }
    )

    result.expect_codes({"UNDECLARED_VARIABLE"})
    result.expect_code_count("UNDECLARED_VARIABLE", 2)
    result.expect_no_code("NO_IMPLICIT_NET")


def test_completely_unused_output_port_stays_with_unused_variable_not_undriven_output(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "unused_output.sv": """
            module top(output logic y);
            endmodule
            """
        }
    )

    result.expect_codes({"UNUSED_VARIABLE"})
    result.expect_code_once("UNUSED_VARIABLE")
    result.expect_no_code("NO_UNDRIVEN_OUTPUT_PORT")


def test_read_but_undriven_output_port_uses_output_specific_rule_not_unused_variable(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "read_undriven_output.sv": """
            module top(output logic y);
              logic z;
              always_comb begin
                z = y;
              end
            endmodule
            """
        }
    )

    result.expect_code_once("NO_UNDRIVEN_OUTPUT_PORT")
    result.expect_code_once("READ_BEFORE_WRITE")
    result.expect_no_code("UNUSED_VARIABLE")


def test_written_but_unread_input_port_uses_input_specific_rule_not_unused_variable(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "write_only_input.sv": """
            module top(input logic a, output logic y);
              logic z = 1'b0;
              always_comb begin
                a = z;
                y = z;
              end
            endmodule
            """
        }
    )

    result.expect_codes({"NO_WRITE_ONLY_INPUT_PORT"})
    result.expect_code_once("NO_WRITE_ONLY_INPUT_PORT")
    result.expect_no_code("UNUSED_VARIABLE")


def test_case_generate_missing_default_uses_generate_rule_not_procedural_case_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "case_generate.sv": """
            module top;
              generate
                case (1)
                  0: begin
                    wire a;
                  end
                endcase
              endgenerate
            endmodule
            """
        }
    )

    result.expect_codes({"DEFAULT_CASE", "NO_CASE_GENERATE", "UNUSED_VARIABLE"})
    result.expect_code_once("DEFAULT_CASE")
    result.expect_code_once("NO_CASE_GENERATE")
    result.expect_no_code("NO_DEFAULT_CASE_STATEMENT")


def test_procedural_case_missing_default_uses_procedural_case_rule_not_generate_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "procedural_case.sv": """
            module top(input logic sel, output logic y);
              always_comb begin
                case (sel)
                  1'b0: y = 1'b0;
                endcase
              end
            endmodule
            """
        }
    )

    result.expect_code_once("NO_DEFAULT_CASE_STATEMENT")
    result.expect_no_code("DEFAULT_CASE")
