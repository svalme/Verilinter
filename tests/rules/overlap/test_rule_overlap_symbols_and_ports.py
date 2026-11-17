"""Overlaps between the symbol, port, width and index rules."""
from collections.abc import Callable
from tests.support.lint_harness import LintCaseFile, LintCaseResult


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

    result.expect_codes({"UNDECLARED_VARIABLE", "MISSING_TIMESCALE_DIRECTIVE", "MODULE_FILENAME_MISMATCH"})
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

    result.expect_codes(
        {"UNUSED_VARIABLE", "MISSING_TIMESCALE_DIRECTIVE", "MODULE_FILENAME_MISMATCH", "PORT_DIRECTION_SUFFIX"}
    )
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


def test_written_but_unread_input_port_uses_both_input_write_rules_not_unused_variable(
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

    result.expect_codes(
        {
            "NO_WRITE_ONLY_INPUT_PORT",
            "NO_INPUT_PORT_WRITE",
            "MISSING_TIMESCALE_DIRECTIVE",
            "MODULE_FILENAME_MISMATCH",
            "PORT_DIRECTION_SUFFIX",
        }
    )
    result.expect_code_once("NO_WRITE_ONLY_INPUT_PORT")
    result.expect_code_once("NO_INPUT_PORT_WRITE")
    result.expect_no_code("UNUSED_VARIABLE")


def test_written_input_port_still_flags_when_input_is_also_read(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "read_and_write_input.sv": """
            module top(input logic a, output logic y);
              logic z = 1'b0;
              always_comb begin
                y = a;
                a = z;
              end
            endmodule
            """
        }
    )

    result.expect_code_once("NO_INPUT_PORT_WRITE")
    result.expect_no_code("NO_WRITE_ONLY_INPUT_PORT")


def test_written_but_unread_local_variable_uses_write_only_variable_not_unused_variable(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "write_only_local.sv": """
            module top(input logic a, output logic y);
              logic x;
              always_comb begin
                x = a;
                y = 1'b0;
              end
            endmodule
            """
        }
    )

    result.expect_code_once("NO_WRITE_ONLY_VARIABLE")
    result.expect_no_code("UNUSED_VARIABLE")


def test_async_reset_xz_value_also_flagged_as_explicit_xz_literal(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "top.sv": """
            module top(input clk, input rst, output reg q);
              always @(posedge clk or posedge rst) begin
                if (rst) begin
                  q <= 1'bx;
                end
              end
            endmodule
            """
        }
    )

    result.expect_codes(
        {"MISSING_TIMESCALE_DIRECTIVE", "EXPLICIT_XZ_LITERAL", "ASYNC_RESET_XZ_VALUE", "PORT_DIRECTION_SUFFIX"}
    )


def test_xz_equality_comparison_also_flagged_as_explicit_xz_literal(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "top.sv": """
            module top(input [3:0] a, output y);
              assign y = (a == 4'bx01z);
            endmodule
            """
        }
    )

    result.expect_code_once("XZ_EQUALITY_COMPARISON")
    result.expect_code_once("EXPLICIT_XZ_LITERAL")


def test_named_empty_port_connection_is_only_flagged_as_unconnected(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    # `.a()` is a named connection with no expression, so `expr_text` is `None`.
    # `unconnected_port_names` counts it as unconnected, and `width_unknown_details`
    # skips it, so only `NO_UNCONNECTED_INSTANCE_PORTS` fires on that connection.
    result = lint_inline_case(
        {
            "top.sv": """
            module child(input [3:0] a, input [3:0] b);
            endmodule
            module top;
              wire [3:0] y;
              child u1(.a(), .b(y));
            endmodule
            """
        }
    )
    result.expect_code_once("NO_UNCONNECTED_INSTANCE_PORTS")
    result.expect_no_code("PORT_CONNECTION_WIDTH_UNKNOWN")


def test_assignment_truncation_also_flagged_as_assignment_width_mismatch(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "truncation.sv": """
            module top;
              wire [7:0] x;
              wire [3:0] y_i;
              assign y_i = x;
            endmodule
            """
        }
    )

    result.expect_code_once("ASSIGNMENT_WIDTH_MISMATCH")
    result.expect_code_once("ASSIGNMENT_TRUNCATION")


def test_input_port_read_with_no_local_write_does_not_trigger_read_before_write(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "input_port_read.sv": """
            module top(input logic clk, input logic d, output logic q);
              always_ff @(posedge clk) begin
                q <= d;
              end
            endmodule
            """
        }
    )

    result.expect_no_code("READ_BEFORE_WRITE")


def test_defparam_hierarchical_target_does_not_trigger_implicit_net(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "defparam_hierarchical.sv": """
            module child #(parameter WIDTH = 1) ();
            endmodule

            module top;
              child u_child();
              defparam u_child.WIDTH = 8;
            endmodule
            """
        }
    )

    result.expect_code_once("NO_DEFPARAM")
    result.expect_no_code("NO_IMPLICIT_NET")


def test_disable_statement_label_does_not_trigger_implicit_net(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "disable_label.sv": """
            module top;
              initial begin : blk
                disable blk;
              end
            endmodule
            """
        }
    )

    result.expect_code_once("NO_DISABLE_STATEMENT")
    result.expect_no_code("NO_IMPLICIT_NET")


def test_typedef_reference_does_not_trigger_implicit_net(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "named_type.sv": """
            typedef logic [7:0] byte_t;
            module top;
              byte_t v;
              always_comb v = 8'd0;
            endmodule
            """
        }
    )

    result.expect_no_code("NO_IMPLICIT_NET")


def test_scoped_typedef_reference_does_not_trigger_implicit_net(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "scoped_named_type.sv": """
            package pkg2;
              typedef logic [7:0] byte_t;
            endpackage
            module top;
              pkg2::byte_t v;
              always_comb v = 8'd0;
            endmodule
            """
        }
    )

    result.expect_code_once("NO_PACKAGE_DECLARATION")
    result.expect_no_code("NO_IMPLICIT_NET")


def test_function_call_site_does_not_trigger_implicit_net(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "call_site.sv": """
            module caller;
              logic [7:0] result;
              always_comb result = add_one(3);
            endmodule
            """
        }
    )

    result.expect_no_code("NO_IMPLICIT_NET")


def test_cover_cross_items_do_not_trigger_implicit_net(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "cover_cross.sv": """
            module top(input logic [1:0] x, input logic [1:0] y);
              covergroup cg;
                cpx: coverpoint x;
                cpy: coverpoint y;
                crs: cross cpx, cpy;
              endgroup
            endmodule
            """
        }
    )

    result.expect_code_once("NO_COVERGROUP_DECLARATION")
    result.expect_no_code("NO_IMPLICIT_NET")


def test_extends_clause_base_name_does_not_trigger_implicit_net(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "extends.sv": """
            class Base;
            endclass
            class C extends Base;
            endclass
            """
        }
    )

    result.expect_code_count("NO_CLASS_DECLARATION", 2)
    result.expect_no_code("NO_IMPLICIT_NET")


def test_indexed_part_select_width_and_constant_index_out_of_range_boundary(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    # 1. Variable width triggers INDEXED_PART_SELECT_WIDTH; CONSTANT_INDEX_OUT_OF_RANGE skips variable width
    var_width = lint_inline_case(
        {
            "var_width.sv": """
            module top(input logic [7:0] a, input logic [2:0] w, output logic [7:0] y);
              assign y = a[0 +: w];
            endmodule
            """
        }
    )
    var_width.expect_code_once("INDEXED_PART_SELECT_WIDTH")
    var_width.expect_no_code("CONSTANT_INDEX_OUT_OF_RANGE")

    # 2. Constant width exceeding signal range triggers CONSTANT_INDEX_OUT_OF_RANGE; legal constant width does not trigger INDEXED_PART_SELECT_WIDTH
    range_overflow = lint_inline_case(
        {
            "range_overflow.sv": """
            module top(input logic [7:0] a, output logic [15:0] y);
              assign y = a[0 +: 16];
            endmodule
            """
        }
    )
    range_overflow.expect_code_once("CONSTANT_INDEX_OUT_OF_RANGE")
    range_overflow.expect_no_code("INDEXED_PART_SELECT_WIDTH")

    # 3. Negative constant width triggers INDEXED_PART_SELECT_WIDTH
    neg_width = lint_inline_case(
        {
            "neg_width.sv": """
            module top(input logic [7:0] a, output logic [7:0] y);
              assign y = a[0 +: -2];
            endmodule
            """
        }
    )
    neg_width.expect_code_once("INDEXED_PART_SELECT_WIDTH")


def test_reversed_indexed_part_select_and_constant_index_boundary(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    # Typo [2 :+ 1] triggers REVERSED_INDEXED_PART_SELECT while indices 2 and +1 are in bounds
    reversed_slice = lint_inline_case(
        {
            "reversed_slice.sv": """
            module top(input logic [7:0] a, output logic [1:0] y);
              assign y = a[2 :+ 1];
            endmodule
            """
        }
    )
    reversed_slice.expect_code_once("REVERSED_INDEXED_PART_SELECT")
    reversed_slice.expect_no_code("CONSTANT_INDEX_OUT_OF_RANGE")


def test_unassigned_task_output_reports_both_unused_variable_and_subroutine_output_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "task_output.sv": """
            module top;
              task x;
                output o;
                begin
                end
              endtask
            endmodule
            """
        }
    )

    result.expect_code_once("UNDRIVEN_SUBROUTINE_OUTPUT")
    result.expect_code_once("UNUSED_VARIABLE")


def test_variable_driven_only_by_an_instance_output_is_reported_by_the_instance_rule_not_the_write_only_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "instance_driven.sv": """
            module sub(output logic p);
              assign p = 1'b0;
            endmodule
            module top(output logic o);
              logic a;
              sub u(.p(a));
              assign o = 1'b0;
            endmodule
            """
        }
    )

    result.expect_code_once("UNREAD_INSTANCE_OUTPUT")
    result.expect_no_code("NO_WRITE_ONLY_VARIABLE")
