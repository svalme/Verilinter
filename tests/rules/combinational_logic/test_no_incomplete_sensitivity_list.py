import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.combinational_logic.no_incomplete_sensitivity_list import NoIncompleteSensitivityListRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "NO_INCOMPLETE_SENSITIVITY_LIST"]


class TestNoIncompleteSensitivityListRule:
    @pytest.fixture
    def rule(self) -> NoIncompleteSensitivityListRule:
        return NoIncompleteSensitivityListRule()

    def test_rule_has_correct_code(self, rule: NoIncompleteSensitivityListRule) -> None:
        assert rule.code == "NO_INCOMPLETE_SENSITIVITY_LIST"

    def test_flags_signal_read_but_missing_from_list(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic a, input logic b, input logic c);
              logic y;
              always @(a or b) begin
                y = a + b + c;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_INCOMPLETE_SENSITIVITY_LIST"
        assert "c" in diagnostics[0]["message"]

    def test_does_not_flag_signals_that_are_in_the_list(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic a, input logic b);
              logic y;
              always @(a or b) begin
                y = a + b;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_write_only_target(self) -> None:
        """`y` is only ever assigned (never read) in the block, so it doesn't need
        to be in the sensitivity list -- only the RHS signal `a` does, and it is."""
        diagnostics = _diagnostics(
            """
            module top(input logic a);
              logic y;
              always @(a) begin
                y = a;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_always_ff_block(self) -> None:
        """always_ff's partial list (clock/reset only) is the normal, intended pattern."""
        diagnostics = _diagnostics(
            """
            module top(input logic clk, input logic rst_n, input logic d);
              logic q;
              always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n) q <= 0;
                else q <= d;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_legacy_posedge_always_block(self) -> None:
        """Plain `always @(posedge clk)` is edge-sensitive just like always_ff and
        should be exempt the same way, even though it isn't the always_ff keyword."""
        diagnostics = _diagnostics(
            """
            module top(input logic clk, input logic d);
              logic q;
              always @(posedge clk) begin
                q <= d;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_wildcard_sensitivity_list(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic a);
              logic y;
              always @* begin
                y = a;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_always_comb_block(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic a);
              logic y;
              always_comb begin
                y = a;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_reports_once_per_missing_signal_even_if_read_multiple_times(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic a, input logic c);
              logic y, z;
              always @(a) begin
                y = a + c;
                z = c - 1;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1
        assert "c" in diagnostics[0]["message"]

    def test_flags_multiple_distinct_missing_signals(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic a, input logic c, input logic e);
              logic y;
              always @(a) begin
                y = a + c + e;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 2
        names = {d["message"].split("'")[1] for d in diagnostics}
        assert names == {"c", "e"}
