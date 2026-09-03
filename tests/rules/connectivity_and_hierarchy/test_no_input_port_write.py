import pyslang as sl
import pytest

from src.pkg.handlers.register_handlers import *
from src.pkg.rules.connectivity_and_hierarchy.no_input_port_write import NoInputPortWriteRule
from src.pkg.semantic.symbol import Symbol
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker


WRITE_INPUT_CODE = """
module top(input logic a, output logic y);
  logic z;
  always_comb begin
    a = z;
    y = z;
  end
endmodule
"""

READ_INPUT_ONLY_CODE = """
module top(input logic a, output logic y);
  always_comb begin
    y = a;
  end
endmodule
"""

READ_AND_WRITE_INPUT_CODE = """
module top(input logic a, output logic y);
  logic z;
  always_comb begin
    y = a;
    a = z;
  end
endmodule
"""


class TestNoInputPortWriteRule:
    @pytest.fixture
    def rule(self) -> NoInputPortWriteRule:
        return NoInputPortWriteRule()

    def test_rule_has_correct_code(self, rule: NoInputPortWriteRule) -> None:
        assert rule.code == "NO_INPUT_PORT_WRITE"

    def test_flags_written_input_port(self, rule: NoInputPortWriteRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="a", kind="variable")
        sym.is_port = True
        sym.port_direction = "input"
        sym.add_declaration({"line": 1, "col": 20})
        sym.add_use({"line": 4, "col": 5}, write=True)
        st.global_scope.define(sym)

        diagnostics = rule.run(st)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_INPUT_PORT_WRITE"
        assert "a" in diagnostics[0]["message"]

    def test_does_not_flag_read_only_input_port(self, rule: NoInputPortWriteRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="a", kind="variable")
        sym.is_port = True
        sym.port_direction = "input"
        sym.add_declaration({"line": 1, "col": 20})
        sym.add_use({"line": 4, "col": 9}, read=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_does_not_flag_output_port(self, rule: NoInputPortWriteRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="y", kind="variable")
        sym.is_port = True
        sym.port_direction = "output"
        sym.add_declaration({"line": 1, "col": 30})
        sym.add_use({"line": 4, "col": 5}, write=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_against_real_parsed_source_write_input(self, rule: NoInputPortWriteRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(WRITE_INPUT_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_INPUT_PORT_WRITE"
        assert "a" in diagnostics[0]["message"]

    def test_against_real_parsed_source_read_only_input(self, rule: NoInputPortWriteRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(READ_INPUT_ONLY_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_against_real_parsed_source_read_and_write_input(self, rule: NoInputPortWriteRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(READ_AND_WRITE_INPUT_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_INPUT_PORT_WRITE"
