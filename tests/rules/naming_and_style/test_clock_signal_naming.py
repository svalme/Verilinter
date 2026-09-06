import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.naming_and_style.clock_signal_naming import ClockSignalNamingRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "CLOCK_SIGNAL_NAMING"]


class TestClockSignalNamingRule:
    @pytest.fixture
    def rule(self) -> ClockSignalNamingRule:
        return ClockSignalNamingRule()

    def test_rule_has_correct_code(self, rule: ClockSignalNamingRule) -> None:
        assert rule.code == "CLOCK_SIGNAL_NAMING"

    def test_flags_sync_block_clock_not_named_clk(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input sys_clock, output reg q);
              always @(posedge sys_clock) begin
                q <= 1'b0;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_clk_named_signal(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, output reg q);
              always @(posedge clk) begin
                q <= 1'b0;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_clk_suffixed_signal(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input core_clk, output reg q);
              always @(posedge core_clk) begin
                q <= 1'b0;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_async_block(self) -> None:
        # Two edge-qualified signals -- can't tell clock from reset, so
        # deliberately not attempted (same restraint as RESET_SIGNAL_NAMING).
        diagnostics = _diagnostics(
            """
            module top(input sys_clock, input rst_n, output reg q);
              always @(posedge sys_clock or negedge rst_n) begin
                if (!rst_n) q <= 1'b0;
                else q <= 1'b1;
              end
            endmodule
            """
        )

        assert diagnostics == []
