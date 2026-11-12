from __future__ import annotations

import pytest

from src.pkg.handlers.register_handlers import *  # noqa: F401,F403
from src.pkg.parser.parse import parse_text
from src.pkg.semantic.symbol_serialization import use_event_from_dict
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.semantic.write_region import normalize_region, regions_may_overlap, span_step
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.parse_diagnostics import assert_no_parse_errors


def _regions(body: str, name: str, decls: str = "logic [7:0] v; logic [3:0] i;") -> list[tuple]:
    """The write regions recorded for `name`, in source order, for writes only."""
    table = SymbolTable()
    tree = parse_text(f"module m; {decls} {body} endmodule")
    assert_no_parse_errors("tests/semantic/test_write_region.py", tree)
    Walker(dispatch).walk(tree.root, tree, Context(scope=table.global_scope), table)
    scope = table.lookup_module("m")
    assert scope is not None
    symbol = scope.lookup(name)
    assert symbol is not None
    return [event.get("write_region", ()) for event in symbol.use_events if event["write"]]


class TestRegionsOfWrites:
    def test_whole_symbol_write_has_an_empty_region(self) -> None:
        assert _regions("assign v = 8'h0;", "v") == [()]

    def test_bit_select_with_constant_index(self) -> None:
        assert _regions("assign v[3] = 1'b0;", "v") == [(("index", 3),)]

    def test_index_from_parameter_expression(self) -> None:
        assert _regions("localparam P = 2; assign v[P+1] = 1'b0;", "v") == [(("index", 3),)]

    def test_index_that_is_not_constant_is_unknown(self) -> None:
        assert _regions("assign v[i] = 1'b0;", "v") == [(("index", None),)]

    def test_simple_range_is_ordered_low_to_high(self) -> None:
        assert _regions("assign v[7:4] = 4'h0;", "v") == [(("range", 4, 7),)]

    def test_ascending_and_descending_indexed_part_selects(self) -> None:
        assert _regions("assign v[2 +: 3] = 3'h0;", "v") == [(("range", 2, 4),)]
        assert _regions("assign v[6 -: 3] = 3'h0;", "v") == [(("range", 4, 6),)]

    def test_indexed_part_select_with_unknown_base_is_an_unknown_range(self) -> None:
        assert _regions("assign v[i +: 2] = 2'h0;", "v") == [(("range", None, None),)]

    def test_several_selectors_keep_their_order(self) -> None:
        regions = _regions("assign w[1][3:2] = 2'h0;", "w", decls="logic [3:0][7:0] w;")
        assert regions == [(("index", 1), ("range", 2, 3))]

    def test_struct_member_and_its_selectors(self) -> None:
        decls = "typedef struct packed {logic a; logic [2:0] b;} s_t; s_t s;"
        assert _regions("assign s.a = 1'b0;", "s", decls) == [(("field", "a"),)]
        assert _regions("assign s.b[1] = 1'b0;", "s", decls) == [(("field", "b"), ("index", 1))]

    def test_array_element_then_member(self) -> None:
        decls = "typedef struct packed {logic a; logic [2:0] b;} s_t; s_t t [2];"
        assert _regions("assign t[1].b[2] = 1'b0;", "t", decls) == [(("index", 1), ("field", "b"), ("index", 2))]

    def test_procedural_write_and_concatenated_targets(self) -> None:
        body = "always_comb begin v[0] = 1'b0; {v[1], v[2]} = 2'b0; end"
        assert _regions(body, "v") == [(("index", 0),), (("index", 1),), (("index", 2),)]

    def test_reads_carry_no_region(self) -> None:
        table = SymbolTable()
        tree = parse_text("module m; logic [7:0] v; logic x; assign x = v[3]; endmodule")
        Walker(dispatch).walk(tree.root, tree, Context(scope=table.global_scope), table)
        symbol = table.lookup_module("m").lookup("v")
        assert all("write_region" not in event for event in symbol.use_events)


class TestRegionsMayOverlap:
    @pytest.mark.parametrize(
        "a, b",
        [
            ((("index", 0),), (("index", 1),)),
            ((("range", 0, 3),), (("range", 4, 7),)),
            ((("index", 8),), (("range", 0, 7),)),
            ((("index", 1), ("index", 5)), (("index", 1), ("index", 6))),
            ((("index", 1), ("index", None)), (("index", 2), ("index", None))),
        ],
    )
    def test_provably_disjoint(self, a: tuple, b: tuple) -> None:
        assert not regions_may_overlap(a, b)
        assert not regions_may_overlap(b, a)

    @pytest.mark.parametrize(
        "a, b",
        [
            ((), ()),
            ((), (("index", 0),)),
            ((("index", 3),), (("index", 3),)),
            ((("range", 0, 4),), (("range", 4, 7),)),
            ((("index", None),), (("index", 1),)),
            ((("range", None, None),), (("range", 0, 3),)),
            ((("index", 3),), (("range", 0, 7),)),
            ((("index", 1),), (("field", "a"),)),
        ],
    )
    def test_possibly_overlapping(self, a: tuple, b: tuple) -> None:
        assert regions_may_overlap(a, b)
        assert regions_may_overlap(b, a)

    def test_distinct_members_overlap_unless_the_caller_says_they_are_disjoint(self) -> None:
        a, b = (("field", "x"),), (("field", "y"),)
        assert regions_may_overlap(a, b)
        assert not regions_may_overlap(a, b, distinct_members_disjoint=True)
        assert regions_may_overlap(a, a, distinct_members_disjoint=True)


class TestRegionSerialization:
    def test_region_survives_a_json_round_trip_as_tuples(self) -> None:
        event = use_event_from_dict(
            {"location": None, "read": False, "write": True, "write_region": [["index", 1], ["field", "a"]]}
        )
        assert event["write_region"] == (("index", 1), ("field", "a"))

    def test_event_without_a_region_has_none(self) -> None:
        assert "write_region" not in use_event_from_dict({"location": None, "read": True, "write": False})

    def test_normalize_accepts_none(self) -> None:
        assert normalize_region(None) == ()


class TestSpanAndNeverSteps:
    def test_span_step_merges_adjacent_values_and_keeps_gaps(self) -> None:
        assert span_step([(0, 0), (1, 1), (2, 2)]) == ("range", 0, 2)
        assert span_step([(0, 0), (2, 2)]) == ("span", ((0, 0), (2, 2)))
        assert span_step([(3, 3)]) == ("index", 3)

    def test_spans_with_no_common_value_are_disjoint(self) -> None:
        even = (span_step([(0, 0), (2, 2), (4, 4)]),)
        odd = (span_step([(1, 1), (3, 3), (5, 5)]),)
        assert not regions_may_overlap(even, odd)
        assert regions_may_overlap(even, (("index", 2),))
        assert not regions_may_overlap(even, (("index", 3),))

    def test_never_overlaps_nothing(self) -> None:
        assert not regions_may_overlap((("never",),), ())
        assert not regions_may_overlap((), (("never",),))

    def test_span_survives_a_json_round_trip(self) -> None:
        event = use_event_from_dict(
            {"location": None, "read": False, "write": True, "write_region": [["span", [[0, 0], [2, 2]]]]}
        )
        assert event["write_region"] == (("span", ((0, 0), (2, 2))),)


class TestRegionsInsideGenerateLoops:
    def test_loop_index_gives_the_set_of_values(self) -> None:
        regions = _regions(
            "for (genvar k = 0; k < 4; k++) begin : g assign v[k*2] = 1'b0; end", "v"
        )
        assert regions == [(("span", ((0, 0), (2, 2), (4, 4), (6, 6))),)]

    def test_bounds_that_are_not_constants_leave_the_index_unknown(self) -> None:
        regions = _regions("for (genvar k = 0; k < N; k++) begin : g assign v[k] = 1'b0; end", "v")
        assert regions == [(("index", None),)]

    def test_branch_no_value_selects_gives_a_never_region(self) -> None:
        regions = _regions("localparam EN = 0; if (EN) begin : g assign v[0] = 1'b0; end", "v")
        assert regions == [(("never",),)]
