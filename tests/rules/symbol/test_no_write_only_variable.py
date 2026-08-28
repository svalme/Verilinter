import pyslang as sl
import pytest

from src.pkg.handlers.register_handlers import *
from src.pkg.rules.symbol.no_write_only_variable import NoWriteOnlyVariableRule
from src.pkg.semantic.symbol import Symbol
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker


WRITE_ONLY_VARIABLE_CODE = """
module top(input logic a, output logic y);
  logic x;
  always_comb begin
    x = a;
    y = 1'b0;
  end
endmodule
"""

READ_AND_WRITTEN_VARIABLE_CODE = """
module top(input logic a, output logic y);
  logic x;
  always_comb begin
    x = a;
    y = x;
  end
endmodule
"""

UNUSED_VARIABLE_CODE = """
module top;
  logic x;
endmodule
"""


class TestNoWriteOnlyVariableRule:
    @pytest.fixture
    def rule(self) -> NoWriteOnlyVariableRule:
        return NoWriteOnlyVariableRule()

    def test_rule_has_correct_code(self, rule: NoWriteOnlyVariableRule) -> None:
        assert rule.code == "NO_WRITE_ONLY_VARIABLE"

    def test_flags_written_but_unread_variable(self, rule: NoWriteOnlyVariableRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration({"line": 2, "col": 9})
        sym.add_use({"line": 4, "col": 5}, write=True)
        st.global_scope.define(sym)

        diagnostics = rule.run(st)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_WRITE_ONLY_VARIABLE"
        assert "x" in diagnostics[0]["message"]

    def test_does_not_flag_variable_that_is_read(self, rule: NoWriteOnlyVariableRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration({"line": 2, "col": 9})
        sym.add_use({"line": 4, "col": 5}, write=True)
        sym.add_use({"line": 5, "col": 9}, read=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_does_not_flag_unused_variable(self, rule: NoWriteOnlyVariableRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration({"line": 2, "col": 9})
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_does_not_flag_unused_parameter(self, rule: NoWriteOnlyVariableRule) -> None:
        """Regression test: a `parameter`'s own initializer registers as a write
        event, so an unused parameter has `is_written=True, is_read=False` -- the
        exact shape this rule looks for. Parameters carry their own
        `kind == "parameter"` classification, so this rule does not report an
        unused parameter as "written but never read", which would be
        misleading: a parameter isn't procedurally written, and
        `NO_UNUSED_PARAMETER` is the accurately-worded diagnostic for this
        shape."""
        st = SymbolTable()
        sym = Symbol(name="WIDTH", kind="parameter")
        sym.add_declaration({"line": 2, "col": 13})
        sym.add_use({"line": 2, "col": 13}, write=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_does_not_flag_port(self, rule: NoWriteOnlyVariableRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="a", kind="variable")
        sym.is_port = True
        sym.port_direction = "input"
        sym.add_declaration({"line": 1, "col": 24})
        sym.add_use({"line": 4, "col": 5}, write=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_against_real_parsed_source_write_only(self, rule: NoWriteOnlyVariableRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(WRITE_ONLY_VARIABLE_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_WRITE_ONLY_VARIABLE"
        assert "x" in diagnostics[0]["message"]

    def test_against_real_parsed_source_read_and_written(self, rule: NoWriteOnlyVariableRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(READ_AND_WRITTEN_VARIABLE_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_against_real_parsed_source_unused_variable(self, rule: NoWriteOnlyVariableRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(UNUSED_VARIABLE_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []
