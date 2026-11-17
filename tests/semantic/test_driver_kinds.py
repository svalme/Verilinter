"""The kind of each driver, recorded from the syntax of the block that owns the writes."""
from __future__ import annotations

from src.pkg.handlers.register_handlers import *  # noqa: F401,F403
from src.pkg.parser.parse import parse_text
from src.pkg.semantic.driver_kind import DriverKind
from src.pkg.semantic.driver_resolver import DriverResolver
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.parse_diagnostics import assert_no_parse_errors


def _kinds_of(code: str, name: str = "v") -> list[DriverKind]:
    symbol_table = SymbolTable()
    tree = parse_text(code)
    assert_no_parse_errors("tests/semantic/test_driver_kinds.py", tree)
    Walker(dispatch).walk(tree.root, tree, Context(scope=symbol_table.global_scope), symbol_table)
    module = symbol_table.lookup_module("top")
    assert module is not None
    symbol = module.lookup(name)
    assert symbol is not None
    resolver = DriverResolver(symbol_table)
    kinds = [resolver.kind_of(driver.id) for driver in resolver.drivers(symbol)]
    assert None not in kinds
    return kinds  # type: ignore[return-value]


def test_a_continuous_assign_is_a_continuous_driver() -> None:
    assert _kinds_of("module top(input in); wire v; assign v = in; endmodule") == [DriverKind.CONTINUOUS]


def test_a_tristate_continuous_assign_is_still_a_continuous_driver() -> None:
    code = "module top(input en, input in); wire v; assign v = en ? in : 1'bz; endmodule"
    assert _kinds_of(code) == [DriverKind.CONTINUOUS]


def test_always_comb_and_a_level_sensitive_always_are_combinational() -> None:
    comb = "module top(input in); logic v; always_comb v = in; endmodule"
    level = "module top(input in); logic v; always @* v = in; endmodule"
    assert _kinds_of(comb) == [DriverKind.COMBINATIONAL]
    assert _kinds_of(level) == [DriverKind.COMBINATIONAL]


def test_a_clocked_block_is_sequential() -> None:
    ff = "module top(input clk, input d); logic v; always_ff @(posedge clk) v <= d; endmodule"
    legacy = "module top(input clk, input d); reg v; always @(posedge clk) v <= d; endmodule"
    assert _kinds_of(ff) == [DriverKind.SEQUENTIAL]
    assert _kinds_of(legacy) == [DriverKind.SEQUENTIAL]


def test_always_latch_is_an_always_driver_that_is_neither_combinational_nor_sequential() -> None:
    code = "module top(input en, input d); logic v; always_latch if (en) v = d; endmodule"
    assert _kinds_of(code) == [DriverKind.ALWAYS]


def test_an_initial_block_is_an_initial_driver() -> None:
    assert _kinds_of("module top; logic v; initial v = 1'b0; endmodule") == [DriverKind.INITIAL]


def test_a_final_block_is_not_a_procedural_always_driver() -> None:
    kinds = _kinds_of("module top; logic v; final v = 1'b0; endmodule")
    assert kinds == [DriverKind.OTHER]
    assert not kinds[0].is_procedural_always


def test_only_always_blocks_are_procedural_always_drivers() -> None:
    always = {DriverKind.SEQUENTIAL, DriverKind.COMBINATIONAL, DriverKind.ALWAYS}
    assert {kind for kind in DriverKind if kind.is_procedural_always} == always


def test_an_unrecorded_driver_has_no_kind() -> None:
    resolver = DriverResolver(SymbolTable())
    assert resolver.kind_of("instance:f.sv:1:1:u0:q") is None
    assert resolver.kind_of(None) is None
