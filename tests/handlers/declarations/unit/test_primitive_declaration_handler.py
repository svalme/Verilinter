from src.pkg.parser.parse import parse_text
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *

CODE = """
primitive my_udp(o, a, b);
  output o;
  input a, b;
  table
    00 : 0;
    01 : 1;
    10 : 1;
    11 : 1;
  endtable
endprimitive
"""


class TestPrimitiveDeclarationHandler:
    def test_registers_primitive_name_on_symbol_table(self) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text(CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert "my_udp" in symbol_table.primitives

    def test_does_not_register_unrelated_module_as_primitive(self) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text("module top; endmodule")
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert symbol_table.primitives == set()
