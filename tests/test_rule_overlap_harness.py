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


def test_unique0_case_still_uses_procedural_missing_default_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "unique0_case.sv": """
            module top(input logic sel, output logic y);
              always_comb begin
                unique0 case (sel)
                  1'b0: y = 1'b0;
                endcase
              end
            endmodule
            """
        }
    )

    result.expect_code_once("NO_UNIQUE0_CASE")
    result.expect_code_once("NO_DEFAULT_CASE_STATEMENT")
    result.expect_no_code("DEFAULT_CASE")


def test_unique_if_uses_if_rule_not_case_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "unique_if.sv": """
            module top(input logic a, b, output logic y);
              always_comb begin
                unique if (a) y = b;
                else y = 1'b0;
              end
            endmodule
            """
        }
    )

    result.expect_code_once("NO_UNIQUE_IF")
    result.expect_no_code("NO_UNIQUE_PRIORITY_CASE")


def test_priority_if_uses_if_rule_not_case_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "priority_if.sv": """
            module top(input logic a, b, c, output logic y);
              always_comb begin
                priority if (a) y = b;
                else y = c;
              end
            endmodule
            """
        }
    )

    result.expect_code_once("NO_PRIORITY_IF")
    result.expect_no_code("NO_UNIQUE_PRIORITY_CASE")


def test_case_inside_still_uses_procedural_missing_default_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "case_inside.sv": """
            module top(input logic [1:0] sel, output logic y);
              always_comb begin
                case inside (sel)
                  2'b00: y = 1'b0;
                endcase
              end
            endmodule
            """
        }
    )

    result.expect_code_once("NO_CASE_INSIDE")
    result.expect_code_once("NO_DEFAULT_CASE_STATEMENT")
    result.expect_no_code("DEFAULT_CASE")


def test_inside_operator_uses_operator_rule_not_case_inside_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "inside_operator.sv": """
            module top(input logic [1:0] sel, output logic y);
              always_comb begin
                y = (sel inside {2'b00, 2'b01}) ? 1'b1 : 1'b0;
              end
            endmodule
            """
        }
    )

    result.expect_code_once("NO_INSIDE_OPERATOR")
    result.expect_no_code("NO_CASE_INSIDE")


def test_forever_loop_can_coexist_with_initial_block_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "forever_loop.sv": """
            module top;
              initial forever #1;
            endmodule
            """
        }
    )

    result.expect_code_once("NO_INITIAL_BLOCK")
    result.expect_code_once("NO_FOREVER_LOOP")


def test_wait_statement_can_coexist_with_initial_block_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "wait_statement.sv": """
            module top(input logic a);
              initial wait (a);
            endmodule
            """
        }
    )

    result.expect_code_once("NO_INITIAL_BLOCK")
    result.expect_code_once("NO_WAIT_STATEMENT")
