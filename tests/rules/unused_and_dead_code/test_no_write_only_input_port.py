import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol import Symbol
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.unused_and_dead_code.no_write_only_input_port import NoWriteOnlyInputPortRule


WRITE_ONLY_INPUT_CODE = """
module top(input logic a, output logic y);
  logic z;
  always_comb begin
    a = z;
    y = z;
  end
endmodule
"""

READ_INPUT_CODE = """
module top(input logic a, output logic y);
  always_comb begin
    y = a;
  end
endmodule
"""

READ_AND_WRITTEN_INPUT_CODE = """
module top(input logic a, output logic y);
  logic z;
  always_comb begin
    a = z;
    y = a;
  end
endmodule
"""

UNUSED_INPUT_CODE = """
module top(input logic a, output logic y);
  always_comb begin
    y = 1'b0;
  end
endmodule
"""


class TestNoWriteOnlyInputPortRule:
    @pytest.fixture
    def rule(self) -> NoWriteOnlyInputPortRule:
        return NoWriteOnlyInputPortRule()

    def test_rule_has_correct_code(self, rule: NoWriteOnlyInputPortRule) -> None:
        assert rule.code == "NO_WRITE_ONLY_INPUT_PORT"

    def test_flags_input_port_written_but_never_read(self, rule: NoWriteOnlyInputPortRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="a", kind="variable")
        sym.is_port = True
        sym.port_direction = "input"
        sym.add_declaration({"line": 1, "col": 20})
        sym.add_use({"line": 4, "col": 5}, write=True)
        st.global_scope.define(sym)

        diagnostics = rule.run(st)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_WRITE_ONLY_INPUT_PORT"
        assert "a" in diagnostics[0]["message"]

    def test_does_not_flag_input_port_that_is_read(self, rule: NoWriteOnlyInputPortRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="a", kind="variable")
        sym.is_port = True
        sym.port_direction = "input"
        sym.add_declaration({"line": 1, "col": 20})
        sym.add_use({"line": 4, "col": 5}, write=True)
        sym.add_use({"line": 5, "col": 9}, read=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_does_not_flag_output_port(self, rule: NoWriteOnlyInputPortRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="y", kind="variable")
        sym.is_port = True
        sym.port_direction = "output"
        sym.add_declaration({"line": 1, "col": 30})
        sym.add_use({"line": 4, "col": 5}, write=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_does_not_flag_non_port_variable(self, rule: NoWriteOnlyInputPortRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration({"line": 2, "col": 9})
        sym.add_use({"line": 5, "col": 9}, write=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_against_real_parsed_source_write_only(self, rule: NoWriteOnlyInputPortRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(WRITE_ONLY_INPUT_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_WRITE_ONLY_INPUT_PORT"
        assert "a" in diagnostics[0]["message"]

    def test_against_real_parsed_source_normal_read(self, rule: NoWriteOnlyInputPortRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(READ_INPUT_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_against_real_parsed_source_read_and_written(self, rule: NoWriteOnlyInputPortRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(READ_AND_WRITTEN_INPUT_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_against_real_parsed_source_unused_input(self, rule: NoWriteOnlyInputPortRule) -> None:
        """An input port that is never referenced at all is UNUSED_VARIABLE's concern, not this rule's."""
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(UNUSED_INPUT_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []
