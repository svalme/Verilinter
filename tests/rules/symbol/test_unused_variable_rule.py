from pathlib import Path

import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.semantic.symbol import Symbol
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.symbol.unused_variable_rule import UnusedVariableRule

DATA = Path(__file__).parent.parent.parent / "data"


class TestUnusedVariableRule:
    """Test cases for the UnusedVariableRule."""

    @pytest.fixture
    def rule(self) -> UnusedVariableRule:
        return UnusedVariableRule()

    def test_flags_declared_but_never_used_variable(self, rule: UnusedVariableRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration({"line": 2, "col": 8})
        st.global_scope.define(sym)

        diagnostics = rule.run(st)

        assert len(diagnostics) == 1
        assert diagnostics[0]["line"] == 2
        assert diagnostics[0]["col"] == 8
        assert "x" in diagnostics[0]["message"]

    def test_does_not_flag_variable_that_is_used(self, rule: UnusedVariableRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration({"line": 2, "col": 8})
        sym.add_use({"line": 5, "col": 3}, read=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_does_not_flag_non_variable_symbols(self, rule: UnusedVariableRule) -> None:
        """An unused module instance shouldn't be reported as an unused variable."""
        st = SymbolTable()
        sym = Symbol(name="inst0", kind="instance")
        sym.add_declaration({"line": 3, "col": 1})
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_no_symbols_returns_no_diagnostics(self, rule: UnusedVariableRule) -> None:
        assert rule.run(SymbolTable()) == []

    def test_against_real_parsed_file(self, rule: UnusedVariableRule) -> None:
        """simple.v declares `real x;` and never references it again."""
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        path = DATA / "simple.v"
        symbol_table.set_current_file(str(path))
        tree = sl.SyntaxTree.fromFile(str(path))
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert diagnostics[0]["message"] == "Unused variable 'x'"
