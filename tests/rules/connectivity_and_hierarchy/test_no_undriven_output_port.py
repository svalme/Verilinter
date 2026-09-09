import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol import Symbol
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.connectivity_and_hierarchy.no_undriven_output_port import NoUndrivenOutputPortRule
from tests.support.parse_diagnostics import assert_no_parse_errors


UNDRIVEN_OUTPUT_CODE = """
module top(input logic clk, output logic y);
  logic z;
  always_comb begin
    z = y;
  end
endmodule
"""

DRIVEN_OUTPUT_CODE = """
module top(input logic clk, output logic y);
  logic z;
  always_comb begin
    y = clk;
    z = y;
  end
endmodule
"""

UNUSED_OUTPUT_CODE = """
module top(input logic clk, output logic y);
  logic z;
  always_comb begin
    z = clk;
  end
endmodule
"""


class TestNoUndrivenOutputPortRule:
    @pytest.fixture
    def rule(self) -> NoUndrivenOutputPortRule:
        return NoUndrivenOutputPortRule()

    def test_rule_has_correct_code(self, rule: NoUndrivenOutputPortRule) -> None:
        assert rule.code == "NO_UNDRIVEN_OUTPUT_PORT"

    def test_flags_output_port_read_but_never_written(self, rule: NoUndrivenOutputPortRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="y", kind="variable")
        sym.is_port = True
        sym.port_direction = "output"
        sym.add_declaration({"line": 1, "col": 30})
        sym.add_use({"line": 5, "col": 9}, read=True)
        st.global_scope.define(sym)

        diagnostics = rule.run(st)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_UNDRIVEN_OUTPUT_PORT"
        assert "y" in diagnostics[0]["message"]

    def test_does_not_flag_output_port_that_is_written(self, rule: NoUndrivenOutputPortRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="y", kind="variable")
        sym.is_port = True
        sym.port_direction = "output"
        sym.add_declaration({"line": 1, "col": 30})
        sym.add_use({"line": 4, "col": 5}, write=True)
        sym.add_use({"line": 5, "col": 9}, read=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_does_not_flag_input_port(self, rule: NoUndrivenOutputPortRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="clk", kind="variable")
        sym.is_port = True
        sym.port_direction = "input"
        sym.add_declaration({"line": 1, "col": 24})
        sym.add_use({"line": 5, "col": 9}, read=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_does_not_flag_non_port_variable(self, rule: NoUndrivenOutputPortRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration({"line": 2, "col": 9})
        sym.add_use({"line": 5, "col": 9}, read=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_against_real_parsed_source_undriven(self, rule: NoUndrivenOutputPortRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(UNDRIVEN_OUTPUT_CODE)
        assert_no_parse_errors("tests/rules/connectivity_and_hierarchy/test_no_undriven_output_port.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_UNDRIVEN_OUTPUT_PORT"
        assert "y" in diagnostics[0]["message"]

    def test_against_real_parsed_source_driven(self, rule: NoUndrivenOutputPortRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(DRIVEN_OUTPUT_CODE)
        assert_no_parse_errors("tests/rules/connectivity_and_hierarchy/test_no_undriven_output_port.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_against_real_parsed_source_unused_output(self, rule: NoUndrivenOutputPortRule) -> None:
        """An output port that is never referenced at all is UNUSED_VARIABLE's concern, not this rule's."""
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(UNUSED_OUTPUT_CODE)
        assert_no_parse_errors("tests/rules/connectivity_and_hierarchy/test_no_undriven_output_port.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []
