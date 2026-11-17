"""The module resolver: what it says about a module an instance names, and what it must not guess."""
from __future__ import annotations

from src.pkg.handlers.register_handlers import *  # noqa: F401,F403
from src.pkg.parser.parse import parse_text
from src.pkg.semantic.module_resolver import ModuleResolver
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.parse_diagnostics import assert_no_parse_errors

SOURCE = """
module child #(parameter W = 4, parameter type T = logic)(input logic clk, output logic [W-1:0] q, inout logic io);
  localparam L = 1;
endmodule
primitive udp(output o, input i);
  table 0 : 1; endtable
endprimitive
"""


def _table(code: str = SOURCE) -> SymbolTable:
    symbol_table = SymbolTable()
    tree = parse_text(code)
    assert_no_parse_errors("tests/semantic/test_module_resolver.py", tree)
    Walker(dispatch).walk(tree.root, tree, Context(scope=symbol_table.global_scope), symbol_table)
    return symbol_table


def _registered(table: SymbolTable) -> None:
    table.module_ports["remote"] = [
        {"file": "other.sv", "ports": [{"name": "a", "direction": "input"}, {"name": "y", "direction": None}]}
    ]


def test_a_walked_module_has_a_scope_and_ports_in_declaration_order() -> None:
    resolver = ModuleResolver(_table())
    assert resolver.scope("child") is not None
    assert resolver.ports("child") == [("clk", "input"), ("q", "output"), ("io", "inout")]


def test_a_registered_module_has_ports_but_no_scope_symbols_or_parameters() -> None:
    table = _table()
    _registered(table)
    resolver = ModuleResolver(table)
    assert resolver.ports("remote") == [("a", "input"), ("y", None)]
    assert resolver.scope("remote") is None
    assert resolver.port_symbols("remote") is None
    assert resolver.parameters("remote") == []


def test_a_walked_module_wins_over_a_registry_entry_of_the_same_name() -> None:
    table = _table()
    table.module_ports["child"] = [{"file": "other.sv", "ports": [{"name": "z", "direction": "input"}]}]
    assert ModuleResolver(table).ports("child") == [("clk", "input"), ("q", "output"), ("io", "inout")]


def test_an_unknown_name_has_no_scope_ports_or_definition() -> None:
    resolver = ModuleResolver(_table())
    assert resolver.scope("missing") is None
    assert resolver.ports("missing") is None
    assert resolver.port_symbols("missing") is None
    assert not resolver.is_defined("missing")


def test_no_name_is_unknown() -> None:
    resolver = ModuleResolver(_table())
    assert resolver.scope(None) is None
    assert resolver.ports("") is None
    assert not resolver.is_defined(None)


def test_a_module_a_registry_entry_and_a_primitive_are_each_defined() -> None:
    table = _table()
    _registered(table)
    table.primitives.add("udp")
    resolver = ModuleResolver(table)
    assert resolver.is_defined("child")
    assert resolver.is_defined("remote")
    assert resolver.is_defined("udp")


def test_port_symbols_are_the_ports_of_a_walked_module_only() -> None:
    symbols = ModuleResolver(_table()).port_symbols("child")
    assert symbols is not None
    assert [symbol.name for symbol in symbols] == ["clk", "q", "io"]


def test_parameters_include_localparams_and_leave_out_type_parameters_by_default() -> None:
    resolver = ModuleResolver(_table())
    assert [symbol.name for symbol in resolver.parameters("child")] == ["W", "L"]


def test_type_parameters_are_included_when_asked_for() -> None:
    names = [symbol.name for symbol in ModuleResolver(_table()).parameters("child", include_types=True)]
    assert names == ["W", "T", "L"]
