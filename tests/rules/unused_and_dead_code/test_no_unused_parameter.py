import pyslang as sl
import pytest

from src.pkg.handlers.register_handlers import *
from src.pkg.rules.unused_and_dead_code.no_unused_parameter import NoUnusedParameterRule
from src.pkg.semantic.symbol import Symbol
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker


UNUSED_PARAMETER_CODE = """
module top(input logic a, output logic y);
  parameter UNUSED_WIDTH = 8;
  assign y = a;
endmodule
"""

USED_PARAMETER_CODE = """
module top(input logic a, output logic [3:0] y);
  parameter WIDTH = 4;
  assign y = {WIDTH{a}};
endmodule
"""

UNUSED_LOCALPARAM_CODE = """
module top(input logic a, output logic y);
  localparam UNUSED_DEPTH = 4;
  assign y = a;
endmodule
"""

UNUSED_ORDINARY_VARIABLE_CODE = """
module top(input logic a, output logic y);
  logic unused_var;
  assign y = a;
endmodule
"""


class TestNoUnusedParameterRule:
    @pytest.fixture
    def rule(self) -> NoUnusedParameterRule:
        return NoUnusedParameterRule()

    def test_rule_has_correct_code(self, rule: NoUnusedParameterRule) -> None:
        assert rule.code == "NO_UNUSED_PARAMETER"

    def test_flags_unused_parameter(self, rule: NoUnusedParameterRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="WIDTH", kind="parameter")
        sym.add_declaration({"line": 2, "col": 13})
        sym.add_use({"line": 2, "col": 13}, write=True)
        st.global_scope.define(sym)

        diagnostics = rule.run(st)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_UNUSED_PARAMETER"
        assert "WIDTH" in diagnostics[0]["message"]

    def test_does_not_flag_parameter_that_is_read(self, rule: NoUnusedParameterRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="WIDTH", kind="parameter")
        sym.add_declaration({"line": 2, "col": 13})
        sym.add_use({"line": 2, "col": 13}, write=True)
        sym.add_use({"line": 4, "col": 9}, read=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_does_not_flag_ordinary_variable(self, rule: NoUnusedParameterRule) -> None:
        """`NO_UNUSED_PARAMETER` is scoped to `kind == "parameter"`; an ordinary
        unused variable is `UNUSED_VARIABLE`'s concern, not this rule's."""
        st = SymbolTable()
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration({"line": 2, "col": 9})
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_against_real_parsed_source_unused_parameter(self, rule: NoUnusedParameterRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(UNUSED_PARAMETER_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_UNUSED_PARAMETER"
        assert "UNUSED_WIDTH" in diagnostics[0]["message"]

    def test_against_real_parsed_source_used_parameter(self, rule: NoUnusedParameterRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(USED_PARAMETER_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_against_real_parsed_source_unused_localparam(self, rule: NoUnusedParameterRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(UNUSED_LOCALPARAM_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_UNUSED_PARAMETER"
        assert "UNUSED_DEPTH" in diagnostics[0]["message"]

    def test_against_real_parsed_source_does_not_flag_ordinary_variable(
        self, rule: NoUnusedParameterRule
    ) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(UNUSED_ORDINARY_VARIABLE_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []
