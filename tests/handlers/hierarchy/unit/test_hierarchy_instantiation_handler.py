import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *

CODE = """
module top;
  foo_mod u_foo();
  bar_mod #(.WIDTH(8)) u_bar(.clk(clk));
  baz_mod u_baz(.*);
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
        assert names == ["foo_mod", "bar_mod", "baz_mod"]

    def test_module_reference_carries_a_real_location(self, walked: tuple[Walker, SymbolTable]) -> None:
        _, symbol_table = walked

        _, loc = symbol_table.module_references[0]
        assert loc["line"] == 3

    def test_records_instantiation_connection_details(self, walked: tuple[Walker, SymbolTable]) -> None:
        _, symbol_table = walked

        assert len(symbol_table.instantiations) == 3
        first = symbol_table.instantiations[0]
        second = symbol_table.instantiations[1]
        third = symbol_table.instantiations[2]

        assert first["instance_name"] == "u_foo"
        assert first["connection_style"] == "empty"
        assert first["connections"] == []

        assert second["instance_name"] == "u_bar"
        assert second["connection_style"] == "named"
        assert second["connections"][0]["port_name"] == "clk"
        assert second["connections"][0]["expr_text"] == "clk"

        assert third["instance_name"] == "u_baz"
        assert third["connection_style"] == "wildcard"
        assert third["connections"][0]["kind"] == "wildcard"

    def test_records_typed_domain_models(self, walked: tuple[Walker, SymbolTable]) -> None:
        from src.pkg.semantic.models import InstanceRecord, ParameterOverride, PortConnection

        _, symbol_table = walked
        assert len(symbol_table.instantiations) == 3

        second = symbol_table.instantiations[1]
        assert isinstance(second, InstanceRecord)
        assert second.instance_name == "u_bar"
        assert second.child_module == "bar_mod"
        assert second.connection_style == "named"
        assert len(second.connections) == 1
        assert isinstance(second.connections[0], PortConnection)
        assert second.connections[0].port_name == "clk"
        assert second.connections[0].expr_text == "clk"
        assert len(second.parameter_overrides) == 1
        assert isinstance(second.parameter_overrides[0], ParameterOverride)
        assert second.parameter_overrides[0].param_name == "WIDTH"

