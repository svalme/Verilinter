from __future__ import annotations

from src.pkg.handlers.register_handlers import *  # noqa: F401,F403
from src.pkg.parser.parse import parse_text
from src.pkg.parser.syntax import assignment_record
from src.pkg.semantic.models.assignment_record import AssignmentKind, AssignmentRecord
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.parse_diagnostics import assert_no_parse_errors

DECLARATIONS = """
  typedef struct packed {logic a; logic [2:0] b;} s_t;
  logic clk; logic [7:0] v; logic [7:0] w; logic [3:0] i; logic x; logic y;
  logic [7:0] m [4]; s_t s; s_t t [2];
"""


def _records(body: str, declarations: str = DECLARATIONS) -> list[AssignmentRecord]:
    table = SymbolTable()
    walker = Walker(dispatch)
    tree = parse_text(f"module top; {declarations} {body} endmodule")
    assert_no_parse_errors("tests/semantic/test_assignment_record.py", tree)
    walker.walk(tree.root, tree, Context(scope=table.global_scope), table)
    records = [assignment_record(ctx, vnode) for vnode, ctx in walker.results]
    return [record for record in records if record is not None]


def _only(body: str, declarations: str = DECLARATIONS) -> AssignmentRecord:
    records = _records(body, declarations)
    assert len(records) == 1, records
    return records[0]


class TestKinds:
    def test_continuous_assign(self) -> None:
        assert _only("assign x = y;").kind == AssignmentKind.CONTINUOUS

    def test_blocking_and_nonblocking(self) -> None:
        assert _only("always_comb x = y;").kind == AssignmentKind.BLOCKING
        assert _only("always_ff @(posedge clk) x <= y;").kind == AssignmentKind.NONBLOCKING

    def test_compound_assignment(self) -> None:
        assert _only("always_comb w += 8'h1;").kind == AssignmentKind.COMPOUND

    def test_declaration_initializer(self) -> None:
        record = _only("logic z = 1'b0;")
        assert record.kind == AssignmentKind.INITIALIZER
        assert record.targets[0].base_symbol.name == "z"

    def test_parameters_and_plain_declarations_have_no_record(self) -> None:
        assert _records("parameter P = 3; localparam Q = 4; logic plain;") == []


class TestTargets:
    def test_whole_symbol_target(self) -> None:
        (target,) = _only("assign v = w;").targets
        assert target.base_symbol.name == "v"
        assert target.write_region == ()
        assert not target.is_sliced

    def test_selected_target_keeps_selectors_and_region(self) -> None:
        record = _only("assign v[3:0] = w[7:4];")
        (target,) = record.targets
        assert target.base_symbol.name == "v"
        assert target.is_sliced and len(target.selectors) == 1
        assert target.write_region == (("range", 0, 3),)
        assert target.bit_width == 4

    def test_element_and_bit_of_an_array(self) -> None:
        (target,) = _only("assign m[2][1] = x;").targets
        assert target.write_region == (("index", 2), ("index", 1))

    def test_struct_member_target(self) -> None:
        (target,) = _only("assign s.a = x;").targets
        assert target.base_symbol.name == "s"
        assert target.write_region == (("field", "a"),)
        assert target.is_sliced and target.bit_width is None

    def test_array_element_then_member(self) -> None:
        (target,) = _only("assign t[1].b[2] = x;").targets
        assert target.base_symbol.name == "t"
        assert target.write_region == (("index", 1), ("field", "b"), ("index", 2))

    def test_concatenated_target_gives_one_target_per_member_in_order(self) -> None:
        record = _only("assign {x, v[7:4], y} = 6'h0;")
        assert [t.base_symbol.name for t in record.targets] == ["x", "v", "y"]
        assert record.targets[1].write_region == (("range", 4, 7),)

    def test_undeclared_name_is_a_target_on_the_placeholder_symbol(self) -> None:
        (target,) = _only("assign missing = x;").targets
        assert target.base_symbol is not None and not target.base_symbol.is_declared
        assert target.write_region == ()


class TestRecordFields:
    def test_rhs_is_the_right_hand_side_node(self) -> None:
        record = _only("assign x = y & x;")
        assert getattr(record.rhs, "kind", None) is not None
        assert "y" in str(record.rhs)

    def test_driver_and_statement_identity_match_the_use_events(self) -> None:
        table = SymbolTable()
        walker = Walker(dispatch)
        tree = parse_text(f"module top; {DECLARATIONS} always_comb x = y; endmodule")
        walker.walk(tree.root, tree, Context(scope=table.global_scope), table)
        record = next(r for r in (assignment_record(c, v) for v, c in walker.results) if r is not None)
        event = next(e for e in table.lookup_module("top").lookup("x").use_events if e["write"])
        assert record.driver_id == event["driver_id"]
        assert record.driver_location == event["driver_location"]
        assert record.statement_id == event["statement_id"]

    def test_a_record_is_built_once_per_node(self) -> None:
        table = SymbolTable()
        walker = Walker(dispatch)
        tree = parse_text(f"module top; {DECLARATIONS} assign x = y; endmodule")
        walker.walk(tree.root, tree, Context(scope=table.global_scope), table)
        pairs = [(v, c) for v, c in walker.results if assignment_record(c, v) is not None]
        vnode, ctx = pairs[0]
        assert assignment_record(ctx, vnode) is assignment_record(ctx, vnode)

    def test_a_node_that_is_not_an_assignment_has_no_record(self) -> None:
        table = SymbolTable()
        walker = Walker(dispatch)
        tree = parse_text("module top; logic x; endmodule")
        walker.walk(tree.root, tree, Context(scope=table.global_scope), table)
        assert all(assignment_record(c, v) is None for v, c in walker.results)


class TestCombinedTarget:
    def test_single_reference_is_returned_as_it_is(self) -> None:
        record = _only("assign v[3:0] = w[7:4];")
        assert record.combined_target() is record.targets[0]

    def test_concatenation_adds_the_member_widths(self) -> None:
        target = _only("assign {x, v[7:4], y} = 6'h0;").combined_target()
        assert target.is_concatenated and target.bit_width == 6
        assert len(target.elements) == 3

    def test_concatenation_with_a_member_of_unknown_width_cannot_be_sized(self) -> None:
        assert _only("assign {s, x} = 2'h0;").combined_target() is None

    def test_undeclared_target_is_a_target_of_unknown_width(self) -> None:
        record = _only("assign x = y;", declarations="logic y;")
        assert record.combined_target().bit_width is None

