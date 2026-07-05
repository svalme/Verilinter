import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.module.undefined_module import UndefinedModuleRule

CODE = """
module top;
  foo_mod u_foo();
endmodule

module foo_mod;
endmodule
"""


class TestUndefinedModuleRule:
    """Test cases for the UndefinedModuleRule."""

    @pytest.fixture
    def rule(self) -> UndefinedModuleRule:
        return UndefinedModuleRule()

    def test_flags_reference_to_a_module_that_was_never_defined(self, rule: UndefinedModuleRule) -> None:
        st = SymbolTable()
        st.register_module_reference("missing_mod", {"line": 3, "col": 3, "file": "a.v"})

        diagnostics = rule.run(st)

        assert len(diagnostics) == 1
        assert diagnostics[0]["line"] == 3
        assert diagnostics[0]["col"] == 3
        assert diagnostics[0]["file"] == "a.v"
        assert "missing_mod" in diagnostics[0]["message"]

    def test_does_not_flag_reference_to_a_defined_module(self, rule: UndefinedModuleRule) -> None:
        st = SymbolTable()
        scope = st.new_scope(kind="module", name="foo_mod")
        st.register_module("foo_mod", scope)
        st.register_module_reference("foo_mod", {"line": 3, "col": 3, "file": "a.v"})

        assert rule.run(st) == []

    def test_flags_each_undefined_reference_separately(self, rule: UndefinedModuleRule) -> None:
        st = SymbolTable()
        st.register_module_reference("missing_mod", {"line": 3, "col": 3, "file": "a.v"})
        st.register_module_reference("missing_mod", {"line": 8, "col": 3, "file": "a.v"})

        diagnostics = rule.run(st)
        assert len(diagnostics) == 2
        assert [d["line"] for d in diagnostics] == [3, 8]

    def test_no_references_returns_no_diagnostics(self, rule: UndefinedModuleRule) -> None:
        assert rule.run(SymbolTable()) == []

    def test_against_real_parsed_source(self, rule: UndefinedModuleRule) -> None:
        """`top` instantiates `foo_mod`, which is defined in the same source."""
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_against_real_parsed_source_with_missing_module(self, rule: UndefinedModuleRule) -> None:
        code = """
        module top;
          missing_mod u_missing();
        endmodule
        """
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(code)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)
        assert len(diagnostics) == 1
        assert "missing_mod" in diagnostics[0]["message"]
