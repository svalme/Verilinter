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


def test_task_declaration_reports_task_rule_cleanly(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "task_declaration.sv": """
            module top;
              task automatic do_work;
              endtask
            endmodule
            """
        }
    )

    result.expect_code_once("NO_TASK_DECLARATION")


def test_program_declaration_reports_program_rule_cleanly(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "program_declaration.sv": """
            program automatic test_prog;
            endprogram
            """
        }
    )

    result.expect_code_once("NO_PROGRAM_DECLARATION")


def test_clocking_declaration_reports_clocking_rule_cleanly(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "clocking_declaration.sv": """
            module top(input logic clk);
              clocking cb @(posedge clk);
              endclocking
            endmodule
            """
        }
    )

    result.expect_code_once("NO_CLOCKING_DECLARATION")


def test_checker_declaration_reports_checker_rule_cleanly(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "checker_declaration.sv": """
            checker c;
            endchecker
            """
        }
    )

    result.expect_code_once("NO_CHECKER_DECLARATION")


def test_interface_declaration_reports_interface_rule_cleanly(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "interface_declaration.sv": """
            interface bus_if;
            endinterface
            """
        }
    )

    result.expect_code_once("NO_INTERFACE_DECLARATION")


def test_modport_declaration_reports_modport_rule_cleanly(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "modport_declaration.sv": """
            interface bus_if(input logic clk);
              modport master(input clk);
            endinterface
            """
        }
    )

    result.expect_code_once("NO_MODPORT_DECLARATION")


def test_package_declaration_reports_package_rule_cleanly(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "package_declaration.sv": """
            package common_pkg;
            endpackage
            """
        }
    )

    result.expect_code_once("NO_PACKAGE_DECLARATION")


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


def test_repeat_loop_can_coexist_with_initial_block_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "repeat_loop.sv": """
            module top;
              initial repeat (4) count = count + 1;
            endmodule
            """
        }
    )

    result.expect_code_once("NO_INITIAL_BLOCK")
    result.expect_code_once("NO_REPEAT_LOOP")


def test_while_loop_can_coexist_with_initial_block_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "while_loop.sv": """
            module top(input logic a);
              initial while (a) a = 1'b0;
            endmodule
            """
        }
    )

    result.expect_code_once("NO_INITIAL_BLOCK")
    result.expect_code_once("NO_WHILE_LOOP")


def test_foreach_loop_can_coexist_with_initial_block_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "foreach_loop.sv": """
            module top;
              logic [3:0] arr;
              initial foreach (arr[i]) arr[i] = 1'b0;
            endmodule
            """
        }
    )

    result.expect_code_once("NO_INITIAL_BLOCK")
    result.expect_code_once("NO_FOREACH_LOOP")


def test_do_while_loop_can_coexist_with_initial_block_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "do_while_loop.sv": """
            module top(input logic a);
              initial do a = 1'b0; while (a);
            endmodule
            """
        }
    )

    result.expect_code_once("NO_INITIAL_BLOCK")
    result.expect_code_once("NO_DO_WHILE_LOOP")
    result.expect_no_code("NO_WHILE_LOOP")


def test_for_loop_can_coexist_with_initial_block_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "for_loop.sv": """
            module top;
              integer i;
              initial for (i = 0; i < 4; i = i + 1) i = i + 1;
            endmodule
            """
        }
    )

    result.expect_code_once("NO_INITIAL_BLOCK")
    result.expect_code_once("NO_FOR_LOOP")


def test_disable_statement_can_coexist_with_initial_block_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "disable_statement.sv": """
            module top;
              initial disable done_flag;
            endmodule
            """
        }
    )

    result.expect_code_once("NO_INITIAL_BLOCK")
    result.expect_code_once("NO_DISABLE_STATEMENT")


def test_event_trigger_can_coexist_with_initial_block_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "event_trigger.sv": """
            module top;
              initial begin
                -> done_flag;
                ->> done_flag;
              end
            endmodule
            """
        }
    )

    result.expect_code_once("NO_INITIAL_BLOCK")
    result.expect_code_count("NO_EVENT_TRIGGER", 2)


def test_fork_join_can_coexist_with_initial_block_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "fork_join.sv": """
            module top;
              initial fork
                done_a = 1'b0;
                done_b = 1'b1;
              join
            endmodule
            """
        }
    )

    result.expect_code_once("NO_INITIAL_BLOCK")
    result.expect_code_once("NO_FORK_JOIN")


def test_udp_instantiation_uses_primitive_declaration_rule_not_undefined_module(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "udp_instance.sv": """
            primitive my_udp(o, a, b);
              output o;
              input a, b;
              table
                00 : 0;
                01 : 1;
                10 : 1;
                11 : 1;
              endtable
            endprimitive

            module top(input a, input b, output c);
              my_udp g1(c, a, b);
            endmodule
            """
        }
    )

    result.expect_code_once("NO_PRIMITIVE_DECLARATION")
    result.expect_no_code("UNDEFINED_MODULE")


def test_gate_primitive_uses_gate_rule_not_tran_rtran_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "gate_and_tran.sv": """
            module top(
                input a, input b, output c,
                inout wire d, inout wire e
            );
              and g1(c, a, b);
              tran t1(d, e);
            endmodule
            """
        }
    )

    result.expect_code_once("NO_GATE_PRIMITIVE")
    result.expect_code_once("NO_TRAN_RTRAN")


def test_display_system_task_can_coexist_with_initial_block_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "display_system_task.sv": """
            module top;
              initial $display("hello");
            endmodule
            """
        }
    )

    result.expect_code_once("NO_INITIAL_BLOCK")
    result.expect_code_once("NO_DISPLAY_SYSTEM_TASK")
    result.expect_no_code("NO_SIMULATION_CONTROL_TASK")


def test_simulation_control_task_uses_its_own_rule_not_display_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "simulation_control_task.sv": """
            module top;
              initial $finish;
            endmodule
            """
        }
    )

    result.expect_code_once("NO_INITIAL_BLOCK")
    result.expect_code_once("NO_SIMULATION_CONTROL_TASK")
    result.expect_no_code("NO_DISPLAY_SYSTEM_TASK")


def test_ordinary_continuous_assign_does_not_trigger_assign_deassign_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "continuous_assign.sv": """
            module top(input a, input b, output c);
              assign c = a & b;
            endmodule
            """
        }
    )

    result.expect_no_code("NO_ASSIGN_DEASSIGN")


def test_procedural_assign_deassign_still_uses_its_own_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "procedural_assign.sv": """
            module top;
              reg a;
              initial begin
                assign a = 1'b1;
                deassign a;
              end
            endmodule
            """
        }
    )

    result.expect_code_count("NO_ASSIGN_DEASSIGN", 2)
