from pathlib import Path

from src.pkg.parser.parse import parse_file, parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.semantic.symbol import Symbol
from src.pkg.semantic.resolution import ResolutionStatus, UnresolvedReference
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.declarations_and_types.undeclared_variable import UndeclaredVariableRule
from tests.support.parse_diagnostics import assert_no_parse_errors

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
        sym.add_use({"line": 4, "col": 5}, read=True)
        st.global_scope.define(sym)
        st.unresolved_references.append(
            UnresolvedReference("a", ResolutionStatus.UNRESOLVED_UNDECLARED, {"line": 4, "col": 5}, sym)
        )

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

    def test_does_not_flag_implicit_net_symbols(self, rule: UndeclaredVariableRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="a", kind="implicit_net")
        sym.add_use({"line": 4, "col": 5}, read=True)
        st.global_scope.define(sym)
        st.unresolved_references.append(
            UnresolvedReference("a", ResolutionStatus.UNRESOLVED_IMPLICIT_NET, {"line": 4, "col": 5}, sym)
        )

        assert rule.run(st) == []

    def test_does_not_flag_a_symbol_that_was_not_recorded_as_unresolved(self, rule: UndeclaredVariableRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="a", kind="variable")
        sym.add_use({"line": 4, "col": 5}, read=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_does_not_flag_a_name_unresolvable_from_this_file(self, rule: UndeclaredVariableRule) -> None:
        st = SymbolTable()
        st.unresolved_references.append(
            UnresolvedReference("FOO", ResolutionStatus.UNRESOLVABLE_HERE, {"line": 4, "col": 5})
        )

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
        """Parsed unresolved identifiers are currently modeled as implicit nets and
        reported by NoImplicitNetRule instead of this broader undeclared rule."""
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        path = DATA / "simple.v"
        symbol_table.set_current_file(str(path))
        tree = parse_file(str(path))
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_flags_unresolved_identifier_when_file_uses_default_nettype_none(self, rule: UndeclaredVariableRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        path = DATA / "default_nettype_none.v"
        symbol_table.set_current_file(str(path))
        symbol_table.set_current_file_default_nettype_none(True)
        tree = parse_file(str(path))
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        flagged_names = {d["message"].split("'")[1] for d in diagnostics}
        assert flagged_names == {"missing_sig"}


def _walk_symbols(code: str) -> SymbolTable:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/declarations_and_types/test_undeclared_variable.py", tree)
    Walker(dispatch).walk(tree.root, tree, ctx, symbol_table)
    return symbol_table


class TestGenvarDeclarations:
    def test_genvar_declaration_is_not_reported_when_default_nettype_is_none(self) -> None:
        table = _walk_symbols(
            """
            `default_nettype none
            module m #(parameter L = 2) (input x);
              genvar i, n;
              generate
                for (i = 0; i < L; i = i + 1) begin : g
                  for (n = 0; n < L; n = n + 1) begin : h
                    wire w;
                  end
                end
              endgenerate
            endmodule
            `default_nettype wire
            """
        )

        assert UndeclaredVariableRule().run(table) == []

