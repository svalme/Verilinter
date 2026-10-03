from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.arrays_and_indexing.indexed_part_select_width import IndexedPartSelectWidthRule

from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/arrays_and_indexing/test_indexed_part_select_width.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "INDEXED_PART_SELECT_WIDTH"]


class TestIndexedPartSelectWidthRule:
    @pytest.fixture
    def rule(self) -> IndexedPartSelectWidthRule:
        return IndexedPartSelectWidthRule()

    def test_rule_has_correct_code(self, rule: IndexedPartSelectWidthRule) -> None:
        assert rule.code == "INDEXED_PART_SELECT_WIDTH"

    def test_allows_valid_positive_constant_width(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [15:0] r;
              wire [3:0] a = r[0 +: 4];
              wire [3:0] b = r[7 -: 4];
            endmodule
            """
        )
        assert len(diagnostics) == 0

    def test_allows_valid_localparam_width(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              localparam WIDTH = 8;
              reg [31:0] r;
              wire [7:0] a = r[0 +: WIDTH];
              wire [7:0] b = r[15 -: WIDTH];
            endmodule
            """
        )
        assert len(diagnostics) == 0

    def test_allows_valid_parameter_width(self) -> None:
        diagnostics = _diagnostics(
            """
            module top #(parameter WIDTH = 4) (
              input wire [15:0] in_data,
              output wire [3:0] out_data
            );
              assign out_data = in_data[0 +: WIDTH];
            endmodule
            """
        )
        assert len(diagnostics) == 0

    def test_allows_valid_folded_constant_expression_width(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              localparam BASE_W = 2;
              reg [15:0] r;
              wire [7:0] a = r[0 +: (BASE_W * 4)];
            endmodule
            """
        )
        assert len(diagnostics) == 0

    def test_flags_zero_width_ascending(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [15:0] r;
              wire [3:0] a = r[0 +: 0];
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "INDEXED_PART_SELECT_WIDTH"

    def test_flags_zero_width_descending(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [15:0] r;
              wire [3:0] a = r[7 -: 0];
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "INDEXED_PART_SELECT_WIDTH"

    def test_flags_negative_width_ascending(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [15:0] r;
              wire [3:0] a = r[0 +: -4];
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "INDEXED_PART_SELECT_WIDTH"

    def test_flags_negative_width_descending(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [15:0] r;
              wire [3:0] a = r[7 -: -1];
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "INDEXED_PART_SELECT_WIDTH"

    def test_flags_constant_expression_evaluating_to_zero_or_negative(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [15:0] r;
              wire [3:0] a = r[0 +: (4 - 4)];
              wire [3:0] b = r[7 -: (2 - 5)];
            endmodule
            """
        )
        assert len(diagnostics) == 2

    def test_flags_dynamic_variable_width_ascending(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [15:0] r;
              wire [3:0] w;
              wire [3:0] a = r[0 +: w];
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "INDEXED_PART_SELECT_WIDTH"

    def test_flags_dynamic_variable_width_descending(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [15:0] r;
              reg [3:0] w;
              wire [3:0] a = r[7 -: w];
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "INDEXED_PART_SELECT_WIDTH"

    def test_flags_expression_with_dynamic_variable(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [15:0] r;
              wire [3:0] w;
              wire [3:0] a = r[0 +: (w + 1)];
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "INDEXED_PART_SELECT_WIDTH"
