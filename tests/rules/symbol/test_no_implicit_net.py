from pathlib import Path

import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.semantic.symbol import Symbol
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.symbol.no_implicit_net import NoImplicitNetRule

DATA = Path(__file__).parent.parent.parent / "data"


class TestNoImplicitNetRule:
    @pytest.fixture
    def rule(self) -> NoImplicitNetRule:
        return NoImplicitNetRule()

    def test_rule_has_correct_code(self, rule: NoImplicitNetRule) -> None:
        assert rule.code == "NO_IMPLICIT_NET"

    def test_flags_implicit_net_symbol(self, rule: NoImplicitNetRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="a", kind="implicit_net")
        sym.is_implicit = True
        sym.add_use({"line": 4, "col": 5}, read=True)
        st.global_scope.define(sym)

        diagnostics = rule.run(st)

        assert len(diagnostics) == 1
        assert diagnostics[0]["line"] == 4
        assert diagnostics[0]["col"] == 5
        assert "a" in diagnostics[0]["message"]

    def test_does_not_flag_declared_symbol(self, rule: NoImplicitNetRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="a", kind="variable")
        sym.add_declaration({"line": 2, "col": 8})
        sym.add_use({"line": 4, "col": 5}, read=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_does_not_flag_non_implicit_undeclared_symbol(self, rule: NoImplicitNetRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="a", kind="variable")
        sym.add_use({"line": 4, "col": 5}, read=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_against_real_parsed_file(self, rule: NoImplicitNetRule) -> None:
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

    def test_does_not_flag_when_file_uses_default_nettype_none(self, rule: NoImplicitNetRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        path = DATA / "default_nettype_none.v"
        symbol_table.set_current_file(str(path))
        symbol_table.set_current_file_default_nettype_none(True)
        tree = sl.SyntaxTree.fromFile(str(path))
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []
