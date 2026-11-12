from src.pkg.parser.parse import parse_text
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *

from tests.support.parse_diagnostics import assert_no_parse_errors

_CODE = """
module child(input logic [7:0] d, output logic [7:0] q); assign q = d; endmodule
module top #(parameter N = 1)(input logic [7:0] d, output logic [7:0] q);
    if (N == 1) begin : g
        child u (.d, .q);
    end
endmodule
"""


class TestShorthandPortInGenerate:
    def test_signal_of_enclosing_scope_has_a_known_width(self) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        tree = parse_text(_CODE)
        assert_no_parse_errors("tests/rules/test_shorthand_port_in_generate.py", tree)
        Walker(dispatch).walk(tree.root, tree, ctx, symbol_table)
        connections = symbol_table.instantiations[0].connections
        assert [(c.port_name, c.expr_width) for c in connections] == [("d", 8), ("q", 8)]
