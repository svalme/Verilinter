import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.arrays_and_indexing.constant_index_out_of_range import ConstantIndexOutOfRangeRule


from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    assert_no_parse_errors("tests/rules/arrays_and_indexing/test_constant_index_out_of_range.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "CONSTANT_INDEX_OUT_OF_RANGE"]


class TestConstantIndexOutOfRangeRule:
    @pytest.fixture
    def rule(self) -> ConstantIndexOutOfRangeRule:
        return ConstantIndexOutOfRangeRule()

    def test_rule_has_correct_code(self, rule: ConstantIndexOutOfRangeRule) -> None:
        assert rule.code == "CONSTANT_INDEX_OUT_OF_RANGE"

    def test_flags_bit_select_index_at_width(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire b;
              assign b = a[8];
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_simple_range_upper_bound_out_of_range(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [1:0] b;
              assign b = a[9:8];
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_indexed_part_select_width_exceeding_declared_width(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [15:0] b;
              assign b = a[0+:16];
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_bit_select_within_range(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire b;
              assign b = a[2];
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_simple_range_within_range(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [3:0] b;
              assign b = a[6:3];
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_variable_index(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [3:0] i;
              wire b;
              assign b = a[i];
            endmodule
            """
        )

        assert diagnostics == []
