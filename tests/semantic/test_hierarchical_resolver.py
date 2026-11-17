"""The hierarchical-name resolver: what a path resolves to and what it must not."""
from __future__ import annotations

from src.pkg.handlers.register_handlers import *  # noqa: F401,F403
from src.pkg.parser.parse import parse_text
from src.pkg.semantic.hierarchical_resolver import HierarchicalNameResolver
from src.pkg.semantic.scope import Scope
from src.pkg.semantic.scope_kinds import ScopeKind
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.parse_diagnostics import assert_no_parse_errors


def _walk(code: str) -> SymbolTable:
    symbol_table = SymbolTable()
    tree = parse_text(code)
    assert_no_parse_errors("tests/semantic/test_hierarchical_resolver.py", tree)
    Walker(dispatch).walk(tree.root, tree, Context(scope=symbol_table.global_scope), symbol_table)
    return symbol_table


def _top(table: SymbolTable) -> Scope:
    scope = table.lookup_module("top")
    assert scope is not None
    return scope


def _resolve(table: SymbolTable, segments: list[str], member: str, from_scope: Scope | None = None):
    return HierarchicalNameResolver(table).resolve(from_scope or _top(table), segments, member)


GEN = """
module top(output logic o);
  logic x;
  if (1) begin : g
    logic x;
    logic y;
  end
  for (genvar i = 0; i < 2; i++) begin : lp
    logic z;
  end
  always_comb begin : blk
    logic t;
    t = 1'b0;
  end
  assign o = 1'b0;
endmodule
"""


class TestStartingPoints:
    def test_generate_block_label(self) -> None:
        table = _walk(GEN)
        target = _resolve(table, ["g"], "y")
        assert target is not None and target.symbol.name == "y" and target.scope.kind == ScopeKind.GENERATE_BLOCK

    def test_loop_generate_label_is_found_through_the_loop_scope(self) -> None:
        table = _walk(GEN)
        target = _resolve(table, ["lp"], "z")
        assert target is not None and target.symbol.name == "z"

    def test_named_procedural_block(self) -> None:
        table = _walk(GEN)
        target = _resolve(table, ["blk"], "t")
        assert target is not None and target.symbol.name == "t"

    def test_instance_of_a_module_in_the_same_source(self) -> None:
        table = _walk("module child(input logic a); logic inner; endmodule\n"
                      "module top; child u(.a(1'b0)); endmodule")
        target = _resolve(table, ["u"], "inner")
        assert target is not None and target.scope is table.lookup_module("child")

    def test_enclosing_module_by_name(self) -> None:
        table = _walk("module top; logic p; endmodule\nmodule child; endmodule")
        child = table.lookup_module("child")
        target = _resolve(table, ["top"], "p", child)
        assert target is not None and target.scope is table.lookup_module("top")

    def test_root_path_starts_at_a_module_name(self) -> None:
        table = _walk("module top; logic p; endmodule\nmodule child; endmodule")
        target = _resolve(table, ["$root", "top"], "p", table.lookup_module("child"))
        assert target is not None and target.symbol.name == "p"


class TestLaterSegments:
    def test_two_instances_deep(self) -> None:
        table = _walk("module leaf(input logic a); logic inner; endmodule\n"
                      "module mid; leaf v(.a(1'b0)); endmodule\n"
                      "module top; mid u(); endmodule")
        target = _resolve(table, ["u", "v"], "inner")
        assert target is not None and target.scope is table.lookup_module("leaf")

    def test_nested_generate_blocks(self) -> None:
        table = _walk("module top; if (1) begin : g1 if (1) begin : g2 logic x; end end endmodule")
        target = _resolve(table, ["g1", "g2"], "x")
        assert target is not None and target.symbol.name == "x"


class TestMustNotResolve:
    def test_member_is_looked_up_in_the_named_scope_only(self) -> None:
        table = _walk(GEN)
        target = _resolve(table, ["g"], "x")
        assert target is not None and target.scope.kind == ScopeKind.GENERATE_BLOCK
        assert target.symbol is not _top(table).lookup("x")

    def test_a_member_the_scope_does_not_declare_is_not_taken_from_outside(self) -> None:
        table = _walk(GEN)
        assert _resolve(table, ["g"], "o") is None

    def test_unknown_first_segment(self) -> None:
        assert _resolve(_walk(GEN), ["nope"], "x") is None

    def test_unknown_later_segment(self) -> None:
        assert _resolve(_walk(GEN), ["g", "nope"], "x") is None

    def test_struct_variable_is_a_member_select_not_a_path(self) -> None:
        table = _walk("module top; struct packed { logic x; } s; endmodule")
        assert _resolve(table, ["s"], "x") is None

    def test_instance_of_a_module_that_was_not_analysed(self) -> None:
        table = _walk("module top; undefined_mod u(.a(1'b0)); endmodule")
        assert _resolve(table, ["u"], "inner") is None

    def test_empty_path(self) -> None:
        assert _resolve(_walk(GEN), [], "x") is None

    def test_root_alone_names_nothing(self) -> None:
        assert _resolve(_walk(GEN), ["$root"], "x") is None


class TestUsesAreRecorded:
    def test_read_through_a_path_marks_the_member_read(self) -> None:
        table = _walk("module top(output logic o); if (1) begin : g logic x; end assign o = g.x; endmodule")
        target = _resolve(table, ["g"], "x")
        assert target is not None and target.symbol.is_read and not target.symbol.is_written

    def test_write_through_a_path_marks_the_member_written(self) -> None:
        table = _walk("module top(output logic o); if (1) begin : g logic x; end assign g.x = 1'b1; endmodule")
        target = _resolve(table, ["g"], "x")
        assert target is not None and target.symbol.is_written and not target.symbol.is_read

    def test_path_to_a_name_that_does_not_exist_records_nothing(self) -> None:
        table = _walk("module top(output logic o); if (1) begin : g logic x; end assign o = g.nope; endmodule")
        target = _resolve(table, ["g"], "x")
        assert target is not None and not target.symbol.is_read
