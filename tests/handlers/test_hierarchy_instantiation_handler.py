import pyslang as sl
import pytest

from src.pkg.ast.context import Context
from src.pkg.ast.dispatch import dispatch
from src.pkg.ast.symbol_table import SymbolTable
from src.pkg.ast.walker import Walker
from src.pkg.handlers.register_handlers import *

CODE = """
module top;
  foo_mod u_foo();
  bar_mod #(.WIDTH(8)) u_bar(.clk(clk));
endmodule
"""


@pytest.fixture
def walked() -> tuple[Walker, SymbolTable]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(CODE)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return walker, symbol_table


class TestHierarchyInstantiationHandler:
    def test_registers_instance_symbols(self, walked: tuple[Walker, SymbolTable]) -> None:
        _, symbol_table = walked

        top_scope = symbol_table.lookup_module("top")
        assert top_scope is not None
        assert top_scope.lookup("u_foo") is not None
        assert top_scope.lookup("u_bar") is not None
        assert top_scope.lookup("u_foo").kind == "instance"

    def test_registers_module_type_references(self, walked: tuple[Walker, SymbolTable]) -> None:
        _, symbol_table = walked

        names = [name for name, _loc in symbol_table.module_references]
        assert names == ["foo_mod", "bar_mod"]

    def test_module_reference_carries_a_real_location(self, walked: tuple[Walker, SymbolTable]) -> None:
        _, symbol_table = walked

        _, loc = symbol_table.module_references[0]
        assert loc["line"] == 3
