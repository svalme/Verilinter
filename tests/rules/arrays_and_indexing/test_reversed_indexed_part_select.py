from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.arrays_and_indexing.reversed_indexed_part_select import ReversedIndexedPartSelectRule

from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/arrays_and_indexing/test_reversed_indexed_part_select.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "REVERSED_INDEXED_PART_SELECT"]


class TestReversedIndexedPartSelectRule:
    @pytest.fixture
    def rule(self) -> ReversedIndexedPartSelectRule:
        return ReversedIndexedPartSelectRule()

    def test_rule_has_correct_code(self, rule: ReversedIndexedPartSelectRule) -> None:
        assert rule.code == "REVERSED_INDEXED_PART_SELECT"

    def test_allows_valid_indexed_part_selects(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [7:0] r;
              wire [1:0] a = r[2 +: 2];
              wire [1:0] b = r[4 -: 2];
            endmodule
            """
        )
        assert len(diagnostics) == 0

    def test_allows_valid_simple_slices(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [7:0] r;
              wire [1:0] a = r[2 : 1];
              wire [3:0] b = r[3 : 0];
            endmodule
            """
        )
        assert len(diagnostics) == 0

    def test_allows_spaced_unary_slices(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [7:0] r;
              wire [1:0] a = r[2 : +1];
              wire [1:0] b = r[2 : -1];
            endmodule
            """
        )
        assert len(diagnostics) == 0

    def test_flags_reversed_colon_plus_with_space(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [3:0] r = 4'b1010;
              wire [1:0] z = r[2 :+ 1];
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "REVERSED_INDEXED_PART_SELECT"

    def test_flags_reversed_colon_plus_without_space(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [3:0] r = 4'b1010;
              wire [1:0] z = r[2 :+1];
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "REVERSED_INDEXED_PART_SELECT"

    def test_flags_reversed_colon_minus_with_space(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [3:0] r = 4'b1010;
              wire [1:0] z = r[2 :- 1];
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "REVERSED_INDEXED_PART_SELECT"

    def test_flags_reversed_colon_minus_without_space(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [3:0] r = 4'b1010;
              wire [1:0] z = r[2 :-1];
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "REVERSED_INDEXED_PART_SELECT"
