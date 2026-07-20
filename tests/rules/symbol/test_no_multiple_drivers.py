import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol import Symbol
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.symbol.no_multiple_drivers import NoMultipleDriversRule


MULTIPLE_DRIVERS_CODE = """
module top(input logic clk, input logic rst_n);
  logic x;
  always_ff @(posedge clk) begin
    x <= 1'b1;
  end
  always_ff @(negedge rst_n) begin
    x <= 1'b0;
  end
endmodule
"""

SINGLE_DRIVER_CODE = """
module top(input logic clk);
  logic x;
  always_ff @(posedge clk) begin
    x <= 1'b1;
    x <= 1'b0;
  end
endmodule
"""

DECLARATION_AND_SINGLE_BLOCK_CODE = """
module top(input logic clk);
  int x = 0;
  always_ff @(posedge clk) begin
    x <= 1;
  end
endmodule
"""


class TestNoMultipleDriversRule:
    @pytest.fixture
    def rule(self) -> NoMultipleDriversRule:
        return NoMultipleDriversRule()

    def test_rule_has_correct_code(self, rule: NoMultipleDriversRule) -> None:
        assert rule.code == "NO_MULTIPLE_DRIVERS"

    def test_flags_symbol_written_from_two_driver_sources(self, rule: NoMultipleDriversRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration({"line": 2, "col": 9})
        sym.add_use(
            {"line": 4, "col": 5},
            write=True,
            driver_id="always:a.sv:3:3",
            driver_location={"line": 3, "col": 3, "file": "a.sv"},
        )
        sym.add_use(
            {"line": 7, "col": 5},
            write=True,
            driver_id="always:a.sv:6:3",
            driver_location={"line": 6, "col": 3, "file": "a.sv"},
        )
        st.global_scope.define(sym)

        diagnostics = rule.run(st)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_MULTIPLE_DRIVERS"
        assert diagnostics[0]["line"] == 7
        assert "x" in diagnostics[0]["message"]
        assert "line 3" in diagnostics[0]["message"]

    def test_does_not_flag_same_driver_block_writing_multiple_times(self, rule: NoMultipleDriversRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration({"line": 2, "col": 9})
        sym.add_use(
            {"line": 4, "col": 5},
            write=True,
            driver_id="always:a.sv:3:3",
            driver_location={"line": 3, "col": 3, "file": "a.sv"},
        )
        sym.add_use(
            {"line": 5, "col": 5},
            write=True,
            driver_id="always:a.sv:3:3",
            driver_location={"line": 3, "col": 3, "file": "a.sv"},
        )
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_does_not_flag_initializer_plus_one_procedural_driver(self, rule: NoMultipleDriversRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(DECLARATION_AND_SINGLE_BLOCK_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_against_real_parsed_source(self, rule: NoMultipleDriversRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(MULTIPLE_DRIVERS_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_MULTIPLE_DRIVERS"
        assert "x" in diagnostics[0]["message"]

    def test_single_driver_source_does_not_flag(self, rule: NoMultipleDriversRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(SINGLE_DRIVER_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []
