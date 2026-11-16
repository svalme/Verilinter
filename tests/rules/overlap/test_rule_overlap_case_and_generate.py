"""Overlaps between the case, if and generate rules."""
from collections.abc import Callable
from tests.support.lint_harness import LintCaseResult


def test_missing_default_on_state_case_also_flagged_as_no_default_case_statement(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "state_case.sv": """
            module top(input clk, input rst_n, output reg y);
              localparam IDLE = 2'b00;
              localparam RUN = 2'b01;
              reg [1:0] state;
              always @(posedge clk or negedge rst_n) begin
                if (!rst_n) state <= IDLE;
                else case (state)
                  IDLE: state <= RUN;
                  RUN: state <= IDLE;
                endcase
              end
            endmodule
            """
        }
    )

    result.expect_code_once("NO_DEFAULT_CASE_STATEMENT")
    result.expect_code_once("MISSING_DEFAULT_ON_STATE_CASE")


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

    result.expect_codes(
        {
            "DEFAULT_CASE",
            "NO_CASE_GENERATE",
            "UNUSED_VARIABLE",
            "MISSING_TIMESCALE_DIRECTIVE",
            "MISSING_GENERATE_BLOCK_LABEL",
            "MODULE_FILENAME_MISMATCH",
        }
    )
    result.expect_code_once("DEFAULT_CASE")
    result.expect_code_once("NO_CASE_GENERATE")
    result.expect_code_once("MISSING_GENERATE_BLOCK_LABEL")
    result.expect_no_code("NO_DEFAULT_CASE_STATEMENT")


def test_generate_for_uses_generate_rule_not_procedural_for_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "generate_for.sv": """
            module top;
              genvar i;
              generate
                for (i = 0; i < 4; i = i + 1) begin : g
                end
              endgenerate
            endmodule
            """
        }
    )

    result.expect_code_once("NO_GENERATE_FOR")
    result.expect_no_code("NO_FOR_LOOP")


def test_if_generate_uses_generate_rule_not_procedural_if_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "if_generate.sv": """
            module top;
              generate
                if (1) begin : g
                end
              endgenerate
            endmodule
            """
        }
    )

    result.expect_code_once("NO_IF_GENERATE")


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
                case (sel) inside
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


def test_case_overlapping_items_and_no_duplicate_case_item_coexist(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    # 1. Numeric duplicate with different representations triggers CASE_OVERLAPPING_ITEMS but not NO_DUPLICATE_CASE_ITEM
    diff_repr = lint_inline_case(
        {
            "case_diff_repr.sv": """
            module top(input [3:0] sel, output logic y);
              always_comb begin
                case (sel)
                  4'd2: y = 1'b1;
                  4'b0010: y = 1'b0;
                  default: y = 1'b0;
                endcase
              end
            endmodule
            """
        }
    )
    diff_repr.expect_code_once("CASE_OVERLAPPING_ITEMS")
    diff_repr.expect_no_code("NO_DUPLICATE_CASE_ITEM")

    # 2. Exact literal duplicate triggers both CASE_OVERLAPPING_ITEMS and NO_DUPLICATE_CASE_ITEM
    exact_dup = lint_inline_case(
        {
            "case_exact_dup.sv": """
            module top(input [3:0] sel, output logic y);
              always_comb begin
                case (sel)
                  4'd2: y = 1'b1;
                  4'd2: y = 1'b0;
                  default: y = 1'b0;
                endcase
              end
            endmodule
            """
        }
    )
    exact_dup.expect_code_once("CASE_OVERLAPPING_ITEMS")
    exact_dup.expect_code_once("NO_DUPLICATE_CASE_ITEM")
