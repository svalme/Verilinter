from pathlib import Path

import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.semantic.symbol import Symbol
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.symbol.undeclared_variable import UndeclaredVariableRule

DATA = Path(__file__).parent.parent.parent / "data"


class TestUndeclaredVariableRule:
    """Test cases for the UndeclaredVariableRule."""

    @pytest.fixture
    def rule(self) -> UndeclaredVariableRule:
        return UndeclaredVariableRule()

    def test_rule_has_correct_code(self, rule: UndeclaredVariableRule) -> None:
        assert rule.code == "UNDECLARED_VARIABLE"

    def test_flags_symbol_used_but_never_declared(self, rule: UndeclaredVariableRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="a", kind="variable")
        sym.is_implicit = True
        sym.add_use({"line": 4, "col": 5}, read=True)
        st.global_scope.define(sym)

        diagnostics = rule.run(st)

        assert len(diagnostics) == 1
        assert diagnostics[0]["line"] == 4
        assert diagnostics[0]["col"] == 5
        assert "a" in diagnostics[0]["message"]

    def test_does_not_flag_symbol_with_a_declaration(self, rule: UndeclaredVariableRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="a", kind="variable")
        sym.add_declaration({"line": 2, "col": 8})
        sym.add_use({"line": 4, "col": 5}, read=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_does_not_flag_declared_but_unused_symbol(self, rule: UndeclaredVariableRule) -> None:
        """No uses and no declarations shouldn't be reachable, but declared-only symbols
        (handled by UnusedVariableRule) must not also trip this rule."""
        st = SymbolTable()
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration({"line": 2, "col": 8})
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_no_symbols_returns_no_diagnostics(self, rule: UndeclaredVariableRule) -> None:
        assert rule.run(SymbolTable()) == []

    def test_against_real_parsed_file(self, rule: UndeclaredVariableRule) -> None:
        """simple.v references a, b, c, d, y, z, sel, out without ever declaring them."""
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        path = DATA / "simple.v"
        symbol_table.set_current_file(str(path))
        tree = sl.SyntaxTree.fromFile(str(path))
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        flagged_names = {d["message"].split("'")[1] for d in diagnostics}
        assert flagged_names == {"a", "b", "c", "d", "y", "z", "sel", "out"}
