import pyslang as sl
import pytest

from src.pkg.ast.context import Context
from src.pkg.ast.dispatch import dispatch
from src.pkg.ast.symbol_table import SymbolTable, Symbol
from src.pkg.ast.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.symbol.redeclared_variable import RedeclaredVariableRule

REDECLARED_CODE = """
module dup;
  real x;
  real x;
endmodule
"""


class TestRedeclaredVariableRule:
    """Test cases for the RedeclaredVariableRule."""

    @pytest.fixture
    def rule(self) -> RedeclaredVariableRule:
        return RedeclaredVariableRule()

    def test_flags_symbol_with_multiple_declarations(self, rule: RedeclaredVariableRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration({"line": 2, "col": 8})
        sym.add_declaration({"line": 3, "col": 8})
        st.global_scope.define(sym)

        diagnostics = rule.run(st)

        assert len(diagnostics) == 1
        assert diagnostics[0]["line"] == 3
        assert diagnostics[0]["col"] == 8
        assert "x" in diagnostics[0]["message"]
        assert "line 2" in diagnostics[0]["message"]

    def test_does_not_flag_single_declaration(self, rule: RedeclaredVariableRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration({"line": 2, "col": 8})
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_does_not_flag_implicit_symbol(self, rule: RedeclaredVariableRule) -> None:
        """A symbol first seen as a use (implicit) shouldn't be reported as redeclared
        even if it later picks up multiple use-derived location entries."""
        st = SymbolTable()
        sym = Symbol(name="a", kind="variable")
        sym.is_implicit = True
        sym.add_declaration({"line": 1, "col": 1})
        sym.add_declaration({"line": 2, "col": 1})
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_three_declarations_flags_second_and_third(self, rule: RedeclaredVariableRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration({"line": 1, "col": 1})
        sym.add_declaration({"line": 2, "col": 1})
        sym.add_declaration({"line": 3, "col": 1})
        st.global_scope.define(sym)

        diagnostics = rule.run(st)
        assert len(diagnostics) == 2
        assert [d["line"] for d in diagnostics] == [2, 3]

    def test_no_symbols_returns_no_diagnostics(self, rule: RedeclaredVariableRule) -> None:
        assert rule.run(SymbolTable()) == []

    def test_against_real_parsed_source(self, rule: RedeclaredVariableRule) -> None:
        """`real x;` declared twice in the same module scope."""
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(REDECLARED_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert "Redeclared symbol 'x'" in diagnostics[0]["message"]
