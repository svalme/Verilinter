import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.width_and_signedness.shift_amount_out_of_range import ShiftAmountOutOfRangeRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "SHIFT_AMOUNT_OUT_OF_RANGE"]


class TestShiftAmountOutOfRangeRule:
    @pytest.fixture
    def rule(self) -> ShiftAmountOutOfRangeRule:
        return ShiftAmountOutOfRangeRule()

    def test_rule_has_correct_code(self, rule: ShiftAmountOutOfRangeRule) -> None:
        assert rule.code == "SHIFT_AMOUNT_OUT_OF_RANGE"

    def test_flags_shift_amount_equal_to_width(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              wire [7:0] y;
              assign y = x << 8;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_negative_shift_amount(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              wire [7:0] y;
              assign y = x >> -1;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_shift_amount_within_range(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              wire [7:0] y;
              assign y = x << 2;
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_variable_shift_amount(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              wire [3:0] n;
              wire [7:0] y;
              assign y = x << n;
            endmodule
            """
        )

        assert diagnostics == []
