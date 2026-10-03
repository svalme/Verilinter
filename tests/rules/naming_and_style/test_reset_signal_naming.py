from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.naming_and_style.reset_signal_naming import ResetSignalNamingRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "RESET_SIGNAL_NAMING"]


class TestResetSignalNamingRule:
    @pytest.fixture
    def rule(self) -> ResetSignalNamingRule:
        return ResetSignalNamingRule()

    def test_rule_has_correct_code(self, rule: ResetSignalNamingRule) -> None:
        assert rule.code == "RESET_SIGNAL_NAMING"

    def test_flags_negedge_reset_without_active_low_suffix(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst, output reg q);
              always @(posedge clk or negedge rst) begin
                if (!rst) q <= 1'b0;
                else q <= 1'b1;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_posedge_reset_with_active_low_suffix(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst_n, output reg q);
              always @(posedge clk or posedge rst_n) begin
                if (rst_n) q <= 1'b0;
                else q <= 1'b1;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_consistent_async_reset_naming(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst_n, output reg q);
              always @(posedge clk or negedge rst_n) begin
                if (!rst_n) q <= 1'b0;
                else q <= 1'b1;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_sync_reset_block(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst, output reg q);
              always @(posedge clk) begin
                if (rst) q <= 1'b0;
                else q <= 1'b1;
              end
            endmodule
            """
        )

        assert diagnostics == []
