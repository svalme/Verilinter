from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.combinational_logic.no_latch_in_always_comb import NoLatchInAlwaysCombRule

from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/combinational_logic/test_no_latch_in_always_comb.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "NO_LATCH_IN_ALWAYS_COMB"]


class TestNoLatchInAlwaysComb:
    def test_symmetric_if_else_does_not_infer_latch(self) -> None:
        code = """
        module top(input logic a, b, c, output logic y, z);
            always_comb begin
                if (a) begin
                    y = b;
                    z = c;
                end else begin
                    y = '0;
                    z = '1;
                end
            end
        endmodule
        """
        diagnostics = _diagnostics(code)
        assert len(diagnostics) == 0

    def test_prior_assignment_overridden_in_one_branch_does_not_infer_latch(self) -> None:
        code = """
        module top(input logic a, b, c, output logic y, z);
            always_comb begin
                y = '0;
                z = '0;
                if (a) begin
                    y = b;
                    z = c;
                end else begin
                    y = '1;
                    // z retains default '0 from prior assignment
                end
            end
        endmodule
        """
        diagnostics = _diagnostics(code)
        assert len(diagnostics) == 0

    def test_case_with_default_all_targets_assigned_no_latch(self) -> None:
        code = """
        module top(input logic [1:0] sel, input logic a, b, output logic y);
            always_comb begin
                case (sel)
                    2'b00: y = a;
                    2'b01: y = b;
                    default: y = '0;
                endcase
            end
        endmodule
        """
        diagnostics = _diagnostics(code)
        assert len(diagnostics) == 0

    def test_case_with_default_but_asymmetric_branches_infers_latch(self) -> None:
        code = """
        module top(input logic [1:0] sel, input logic a, b, output logic y, z);
            always_comb begin
                case (sel)
                    2'b00: begin
                        y = a;
                        z = 1'b1;
                    end
                    2'b01: begin
                        y = b;
                        // z missing here!
                    end
                    default: begin
                        y = '0;
                        z = '0;
                    end
                endcase
            end
        endmodule
        """
        diagnostics = _diagnostics(code)
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_LATCH_IN_ALWAYS_COMB"

    def test_sequential_always_ff_ignored(self) -> None:
        code = """
        module top(input logic clk, input logic a, output logic y);
            always_ff @(posedge clk) begin
                if (a) y <= 1'b1;
            end
        endmodule
        """
        diagnostics = _diagnostics(code)
        assert len(diagnostics) == 0

    def test_nested_if_else_ladder_intermediate_omission_infers_latch(self) -> None:
        # Multi-stage ladder: x is assigned in all branches, but y is omitted in intermediate else-if
        code = """
        module top(input logic c1, c2, input logic [7:0] a, b, c, output logic [7:0] x, y);
            always_comb begin
                if (c1) begin
                    x = a;
                    y = a;
                end else if (c2) begin
                    x = b;
                    // y is missing in this intermediate branch!
                end else begin
                    x = c;
                    y = c;
                end
            end
        endmodule
        """
        diagnostics = _diagnostics(code)
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_LATCH_IN_ALWAYS_COMB"

    def test_nested_if_else_ladder_terminal_else_omission_infers_latch(self) -> None:
        # Multi-stage ladder: terminal else assigns x but omits y
        code = """
        module top(input logic c1, c2, input logic [7:0] a, b, c, output logic [7:0] x, y);
            always_comb begin
                if (c1) begin
                    x = a;
                    y = a;
                end else if (c2) begin
                    x = b;
                    y = b;
                end else begin
                    x = c;
                    // y omitted in terminal else!
                end
            end
        endmodule
        """
        diagnostics = _diagnostics(code)
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_LATCH_IN_ALWAYS_COMB"

    def test_nested_if_else_ladder_empty_statement_branch_infers_latch(self) -> None:
        # Intermediate ladder branch contains an empty statement
        code = """
        module top(input logic c1, c2, input logic a, b, output logic x);
            always_comb begin
                if (c1) begin
                    x = a;
                end else if (c2) begin
                    ; // empty statement!
                end else begin
                    x = b;
                end
            end
        endmodule
        """
        diagnostics = _diagnostics(code)
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_LATCH_IN_ALWAYS_COMB"

    def test_nested_if_else_ladder_all_variables_fully_assigned_no_latch(self) -> None:
        # Multi-stage ladder where x, y, and z are fully assigned across all branches
        code = """
        module top(input logic c1, c2, input logic [7:0] a, b, c, output logic [7:0] x, y, z);
            always_comb begin
                if (c1) begin
                    x = a;
                    y = b;
                    z = c;
                end else if (c2) begin
                    x = b;
                    y = c;
                    z = a;
                end else begin
                    x = c;
                    y = a;
                    z = b;
                end
            end
        endmodule
        """
        diagnostics = _diagnostics(code)
        assert len(diagnostics) == 0

    def test_partial_preassignment_with_adversarial_branches(self) -> None:
        # var_a has an unconditional default pre-assignment; var_b is assigned in both branches;
        # var_c has no pre-assignment and is only assigned conditionally in the if-branch.
        code = """
        module top(input logic cond, input logic in_a, in_b, in_c, output logic var_a, var_b, var_c);
            always_comb begin
                var_a = 1'b0; // unconditional default
                if (cond) begin
                    var_a = in_a;
                    var_b = in_b;
                    var_c = in_c;
                end else begin
                    var_b = 1'b0;
                    // var_c omitted and not pre-assigned!
                end
            end
        endmodule
        """
        diagnostics = _diagnostics(code)
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_LATCH_IN_ALWAYS_COMB"

    def test_sequential_conditionals_independent_variable_latching(self) -> None:
        # Two sequential if-statements in the same always_comb: first is fully covered, second has missing else
        code = """
        module top(input logic c1, c2, input logic a, b, c, output logic x, y);
            always_comb begin
                if (c1) x = a; else x = b;
                if (c2) y = c; // missing else infers latch on y!
            end
        endmodule
        """
        diagnostics = _diagnostics(code)
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_LATCH_IN_ALWAYS_COMB"

    def test_nested_conditional_inside_case_clause_asymmetry(self) -> None:
        # case with default, but 2'b00 contains a sub-conditional omitting an else branch
        code = """
        module top(input logic [1:0] sel, input logic sub_c, input logic a, output logic x);
            always_comb begin
                case (sel)
                    2'b00: begin
                        if (sub_c) x = a; // no else clause in this sub-branch!
                    end
                    default: x = 1'b0;
                endcase
            end
        endmodule
        """
        diagnostics = _diagnostics(code)
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_LATCH_IN_ALWAYS_COMB"

    def test_case_statement_multiple_asymmetric_variables(self) -> None:
        # Case statement where x is assigned in all clauses, but y is omitted in 2'b01
        code = """
        module top(input logic [1:0] sel, input logic [7:0] a, b, output logic [7:0] x, y);
            always_comb begin
                case (sel)
                    2'b00: begin
                        x = a;
                        y = b;
                    end
                    2'b01: begin
                        x = b;
                        // y omitted!
                    end
                    default: begin
                        x = '0;
                        y = '0;
                    end
                endcase
            end
        endmodule
        """
        diagnostics = _diagnostics(code)
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_LATCH_IN_ALWAYS_COMB"

    def test_case_statement_all_variables_fully_assigned_complex_no_latch(self) -> None:
        # Multiple variables assigned across all case items and default
        code = """
        module top(input logic [1:0] sel, input logic a, b, output logic x, y);
            always_comb begin
                case (sel)
                    2'b00: begin
                        x = a;
                        y = b;
                    end
                    2'b01: begin
                        x = ~a;
                        y = ~b;
                    end
                    default: begin
                        x = 1'b0;
                        y = 1'b1;
                    end
                endcase
            end
        endmodule
        """
        diagnostics = _diagnostics(code)
        assert len(diagnostics) == 0

    def test_multiple_always_comb_blocks_one_clean_one_latching(self) -> None:
        # Two always_comb blocks: block 1 is clean, block 2 infers a latch
        code = """
        module top(input logic c1, c2, input logic a, b, output logic x, y);
            always_comb begin
                if (c1) x = a; else x = 1'b0;
            end

            always_comb begin
                if (c2) y = b; // missing else infers latch
            end
        endmodule
        """
        diagnostics = _diagnostics(code)
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_LATCH_IN_ALWAYS_COMB"
