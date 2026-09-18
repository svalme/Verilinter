import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.combinational_logic.no_multiple_drivers import NoMultipleDriversRule
from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    assert_no_parse_errors("tests/rules/combinational_logic/test_clocking_multidriven.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    rule = NoMultipleDriversRule()
    return rule.run(symbol_table)


class TestClockingMultiDriven:
    def test_continuous_assign_and_clocking_output_conflict(self) -> None:
        code = """
        module top(input wire clk);
            logic sig;
            clocking cb @(posedge clk);
                output sig;
            endclocking
            assign sig = 1'b1;
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 1
        assert "Variable 'sig' is written from multiple drivers" in diags[0]["message"]

    def test_always_and_clocking_output_conflict(self) -> None:
        code = """
        module top(input wire clk);
            logic sig;
            clocking cb @(posedge clk);
                output sig;
            endclocking
            always @(posedge clk) sig <= 1'b1;
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 1
        assert "Variable 'sig' is written from multiple drivers" in diags[0]["message"]

    def test_two_clocking_blocks_conflict(self) -> None:
        code = """
        module top(input wire clk);
            logic sig;
            clocking cb1 @(posedge clk);
                output sig;
            endclocking
            clocking cb2 @(posedge clk);
                output sig;
            endclocking
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 1
        assert "Variable 'sig' is written from multiple drivers" in diags[0]["message"]

    def test_clocking_only_clean(self) -> None:
        code = """
        module top(input wire clk);
            logic sig;
            clocking cb @(posedge clk);
                output sig;
            endclocking
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 0

    def test_clocking_input_clean(self) -> None:
        code = """
        module top(input wire clk);
            logic sig;
            assign sig = 1'b1;
            clocking cb @(posedge clk);
                input sig;
            endclocking
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 0
