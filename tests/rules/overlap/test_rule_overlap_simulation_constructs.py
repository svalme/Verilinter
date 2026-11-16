"""Overlaps between the simulation-construct rules and the rules for names, gates and loops."""
from collections.abc import Callable
from tests.support.lint_harness import LintCaseResult


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


def test_function_declaration_uses_its_own_rule_not_task_declaration_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "function_and_task.sv": """
            module top;
              function automatic int add_one(input int x);
                add_one = x + 1;
              endfunction

              task automatic do_work;
              endtask
            endmodule
            """
        }
    )

    result.expect_code_once("NO_FUNCTION_DECLARATION")
    result.expect_code_once("NO_TASK_DECLARATION")


def test_property_declaration_and_concurrent_assertion_fire_independently(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "property_and_assert.sv": """
            module top(input clk, input a);
              property p1;
                @(posedge clk) a;
              endproperty
              assert property (p1);
            endmodule
            """
        }
    )

    result.expect_code_once("NO_PROPERTY_DECLARATION")
    result.expect_code_once("NO_CONCURRENT_ASSERTION")
    result.expect_no_code("NO_IMMEDIATE_ASSERTION")


def test_uwire_uses_its_own_rule_not_wand_wor_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "uwire_and_wand.sv": """
            module top(input a, input b, output c, output d);
              uwire w1;
              wand w2;
              assign w1 = a;
              assign c = w1;
              assign w2 = b;
              assign d = w2;
            endmodule
            """
        }
    )

    result.expect_code_once("NO_UWIRE")
    result.expect_code_once("NO_WAND_WOR")


def test_task_and_function_declaration_names_do_not_trigger_implicit_net(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "task_name_regression.sv": """
            module top;
              task automatic do_work;
              endtask
            endmodule
            """
        }
    )

    result.expect_code_once("NO_TASK_DECLARATION")
    result.expect_no_code("NO_IMPLICIT_NET")


def test_or_joined_sensitivity_list_does_not_trigger_gate_primitive_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    """`or` is a gate-primitive keyword (`or g1(c, a, b);`) but is also the classic
    event/sensitivity-list separator (`@(posedge clk or negedge rst_n)`), sharing the
    same TokenKind.OrKeyword. Only the former is a gate instantiation."""
    result = lint_inline_case(
        {
            "or_sensitivity_list.sv": """
            module top(input clk, input rst_n, input d, output reg q);
              always @(posedge clk or negedge rst_n) begin
                if (!rst_n) q <= 1'b0;
                else q <= d;
              end
            endmodule
            """
        }
    )

    result.expect_no_code("NO_GATE_PRIMITIVE")


def test_plain_or_joined_sensitivity_list_does_not_trigger_gate_primitive_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "plain_or_sensitivity_list.sv": """
            module top(input a, input b, output reg y);
              always @(a or b) y = a & b;
            endmodule
            """
        }
    )

    result.expect_no_code("NO_GATE_PRIMITIVE")


def test_or_gate_instantiation_still_triggers_gate_primitive_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "or_gate.sv": """
            module top(input a, input b, output c);
              or g1(c, a, b);
            endmodule
            """
        }
    )

    result.expect_code_once("NO_GATE_PRIMITIVE")


def test_disable_iff_in_concurrent_assertion_does_not_trigger_disable_statement_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "disable_iff.sv": """
            module top(input clk, input rst, input a, input b);
              assert property (@(posedge clk) disable iff (rst) a |-> b);
            endmodule
            """
        }
    )

    result.expect_code_once("NO_CONCURRENT_ASSERTION")
    result.expect_no_code("NO_DISABLE_STATEMENT")


def test_implication_operator_in_expression_does_not_trigger_event_trigger_rule(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    result = lint_inline_case(
        {
            "implication_expr.sv": """
            module m(input a, input b, output y);
              assign y = (a -> b);
            endmodule
            """
        }
    )

    result.expect_no_code("NO_EVENT_TRIGGER")


def test_infinite_loop_and_sequential_blocking_coexistence(
    lint_inline_case: Callable[[dict[str, str]], LintCaseResult],
) -> None:
    # Infinite loop inside clocked procedural block co-fires with NO_BLOCKING_SEQUENTIAL
    seq_infinite = lint_inline_case(
        {
            "seq_infinite.sv": """
            module top(input logic clk_i);
              logic [7:0] count;
              always @(posedge clk_i) begin
                forever begin
                  count = count + 1'b1;
                end
              end
            endmodule
            """
        }
    )
    seq_infinite.expect_code_once("INFINITELOOP")
    seq_infinite.expect_code_once("NO_BLOCKING_SEQUENTIAL")
