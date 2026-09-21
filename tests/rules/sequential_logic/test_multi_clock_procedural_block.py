import pyslang as sl
import pytest

from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.sequential_logic.multi_clock_procedural_block import MultiClockProceduralBlockRule
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    assert_no_parse_errors("tests/rules/sequential_logic/test_multi_clock_procedural_block.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "MULTI_CLOCK_PROCEDURAL_BLOCK"]


class TestMultiClockProceduralBlockRule:
    @pytest.fixture
    def rule(self) -> MultiClockProceduralBlockRule:
        return MultiClockProceduralBlockRule()

    def test_rule_metadata(self, rule: MultiClockProceduralBlockRule) -> None:
        assert rule.code == "MULTI_CLOCK_PROCEDURAL_BLOCK"
        assert rule.category == "rtl_correctness"
        assert "rtl_strict" in rule.default_profiles

    def test_single_clock_synchronous_passes(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input d, output reg q);
              always @(posedge clk) begin
                q <= d;
              end
            endmodule
            """
        )
        assert diagnostics == []

    def test_single_clock_with_async_reset_passes(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst_n, input d, output reg q);
              always @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                  q <= 1'b0;
                else
                  q <= d;
              end
            endmodule
            """
        )
        assert diagnostics == []

    def test_single_clock_with_active_high_async_reset_passes(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst, input d, output reg q);
              always_ff @(posedge clk or posedge rst) begin
                if (rst)
                  q <= 1'b0;
                else
                  q <= d;
              end
            endmodule
            """
        )
        assert diagnostics == []

    def test_single_clock_with_dual_async_resets_passes(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst1_n, input rst2, input d, output reg q);
              always @(posedge clk or negedge rst1_n or posedge rst2) begin
                if (!rst1_n)
                  q <= 1'b0;
                else if (rst2)
                  q <= 1'b1;
                else
                  q <= d;
              end
            endmodule
            """
        )
        assert diagnostics == []

    def test_flags_multiple_clocks(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk1, input clk2, input d, output reg q);
              always @(posedge clk1 or posedge clk2) begin
                q <= d;
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert "multiple clock signals" in diagnostics[0]["message"]

    def test_flags_duplicate_edges_on_same_signal(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input d, output reg q);
              always @(posedge clk or negedge clk) begin
                q <= d;
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_flags_edge_signals_with_missing_reset_if(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst_n, input d, output reg q);
              always @(posedge clk or negedge rst_n) begin
                q <= d;
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_does_not_flag_combinational_block(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input a, input b, output reg y);
              always @* begin
                y = a & b;
              end
            endmodule
            """
        )
        assert diagnostics == []
