import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol import Symbol
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.symbol.no_undriven_signal import NoUndrivenSignalRule


UNDRIVEN_SIGNAL_CODE = """
module top(input logic clk);
  logic x;
  logic y;
  always_comb begin
    y = x;
  end
endmodule
"""

DRIVEN_SIGNAL_CODE = """
module top(input logic clk);
  logic x;
  logic y;
  always_comb begin
    x = clk;
    y = x;
  end
endmodule
"""

INITIALIZED_SIGNAL_CODE = """
module top;
  int x = 1;
  int y;
  always_comb begin
    y = x;
  end
endmodule
"""


class TestNoUndrivenSignalRule:
    @pytest.fixture
    def rule(self) -> NoUndrivenSignalRule:
        return NoUndrivenSignalRule()

    def test_rule_has_correct_code(self, rule: NoUndrivenSignalRule) -> None:
        assert rule.code == "NO_UNDRIVEN_SIGNAL"

    def test_flags_read_but_never_written_variable(self, rule: NoUndrivenSignalRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration({"line": 2, "col": 9})
        sym.add_use({"line": 5, "col": 9}, read=True)
        st.global_scope.define(sym)

        diagnostics = rule.run(st)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_UNDRIVEN_SIGNAL"
        assert diagnostics[0]["line"] == 2
        assert "x" in diagnostics[0]["message"]

    def test_does_not_flag_written_variable(self, rule: NoUndrivenSignalRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration({"line": 2, "col": 9})
        sym.add_use({"line": 4, "col": 5}, write=True)
        sym.add_use({"line": 5, "col": 9}, read=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_does_not_flag_input_port(self, rule: NoUndrivenSignalRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="clk", kind="variable")
        sym.is_port = True
        sym.add_declaration({"line": 1, "col": 24})
        sym.add_use({"line": 5, "col": 9}, read=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_initializer_counts_as_drive(self, rule: NoUndrivenSignalRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(INITIALIZED_SIGNAL_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_against_real_parsed_source(self, rule: NoUndrivenSignalRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(UNDRIVEN_SIGNAL_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_UNDRIVEN_SIGNAL"
        assert "x" in diagnostics[0]["message"]

    def test_does_not_flag_when_signal_is_driven(self, rule: NoUndrivenSignalRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(DRIVEN_SIGNAL_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []
