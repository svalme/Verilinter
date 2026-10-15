from __future__ import annotations

import pytest

from src.pkg.handlers.register_handlers import *
from src.pkg.parser.parse import parse_text
from src.pkg.rules.simulation_vs_synthesis.procedural_assignment_to_initialized_variable import (
    ProceduralAssignmentToInitializedVariableRule,
)
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.lint_harness import run_inline_lint_case


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    rule = ProceduralAssignmentToInitializedVariableRule()
    return rule.run(symbol_table)


class TestProceduralAssignmentToInitializedVariableRule:
    @pytest.fixture
    def rule(self) -> ProceduralAssignmentToInitializedVariableRule:
        return ProceduralAssignmentToInitializedVariableRule()

    def test_rule_has_correct_code(self, rule: ProceduralAssignmentToInitializedVariableRule) -> None:
        assert rule.code == "PROCASSINIT"

    def test_flags_initialized_variable_assigned_in_always_ff(self) -> None:
        code = """
        module top(input logic clk_i, input logic d_i, output logic q_o);
          logic r = 1'b0;
          always_ff @(posedge clk_i) begin
            r <= d_i;
          end
          assign q_o = r;
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 1
        assert diags[0]["line"] == 3
        assert diags[0]["col"] == 17
        assert "Procedural assignment to declaration with initial value: 'r'" in diags[0]["message"]

    def test_flags_initialized_variable_assigned_in_always_comb(self) -> None:
        code = """
        module top(input logic a_i, output logic y_o);
          logic val = 1'b0;
          always_comb begin
            val = a_i;
          end
          assign y_o = val;
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 1
        assert diags[0]["line"] == 3
        assert diags[0]["col"] == 17
        assert "Procedural assignment to declaration with initial value: 'val'" in diags[0]["message"]

    def test_flags_initialized_variable_assigned_in_always_latch(self) -> None:
        code = """
        module top(input logic en_i, input logic d_i, output logic q_o);
          logic latch_val = 1'b0;
          always_latch begin
            if (en_i) latch_val <= d_i;
          end
          assign q_o = latch_val;
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 1
        assert diags[0]["line"] == 3
        assert diags[0]["col"] == 17
        assert "Procedural assignment to declaration with initial value: 'latch_val'" in diags[0]["message"]

    def test_flags_initialized_variable_assigned_in_plain_always(self) -> None:
        code = """
        module top(input logic clk_i, input logic d_i, output logic q_o);
          reg r = 1'b1;
          always @(posedge clk_i) begin
            r <= d_i;
          end
          assign q_o = r;
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 1
        assert diags[0]["line"] == 3
        assert diags[0]["col"] == 15
        assert "Procedural assignment to declaration with initial value: 'r'" in diags[0]["message"]

    def test_allows_variable_assigned_only_in_initial_block(self) -> None:
        code = """
        module top;
          logic init_val = 1'b0;
          initial begin
            init_val = 1'b1;
          end
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 0

    def test_allows_initialized_variable_with_no_procedural_writes(self) -> None:
        code = """
        module top(output logic y_o);
          logic const_val = 1'b1;
          assign y_o = const_val;
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 0

    def test_allows_uninitialized_variable_procedurally_assigned(self) -> None:
        code = """
        module top(input logic clk_i, input logic d_i, output logic q_o);
          logic normal_flop;
          always_ff @(posedge clk_i) begin
            normal_flop <= d_i;
          end
          assign q_o = normal_flop;
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 0

    def test_allows_local_variable_in_automatic_function(self) -> None:
        code = """
        module top;
          function automatic int calc(int a);
            int temp = 0;
            temp = a + 1;
            return temp;
          endfunction
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 0

    def test_allows_parameters_and_localparams(self) -> None:
        code = """
        module top #(parameter int P = 1) ();
          localparam int LP = 2;
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 0

    def test_pipeline_integration_with_expect_diagnostics(self) -> None:
        result = run_inline_lint_case(
            {
                "top.sv": """
                module top(input logic clk_i, input logic d_i, output logic q_o);
                  logic r = 1'b0;
                  always_ff @(posedge clk_i) begin
                    r <= d_i;
                  end
                  assign q_o = r;
                endmodule
                """
            }
        )
        result.expect_diagnostics([(2, "PROCASSINIT")], filter_code="PROCASSINIT")
