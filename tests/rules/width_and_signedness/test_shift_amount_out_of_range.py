from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.width_and_signedness.shift_amount_out_of_range import ShiftAmountOutOfRangeRule


from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/width_and_signedness/test_shift_amount_out_of_range.py", tree)
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

    def test_does_not_flag_shift_amount_at_max_valid(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              wire [7:0] y;
              assign y = x << 7;
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_shift_amount_of_zero(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              wire [7:0] y;
              assign y = x << 0;
            endmodule
            """
        )

        assert diagnostics == []

    def test_flags_logical_right_shift_amount_equal_to_width(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              wire [7:0] y;
              assign y = x >> 8;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_arithmetic_shift_amount_out_of_range(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              wire [7:0] y;
              assign y = x >>> 8;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_when_shifted_operand_is_not_an_identifier(self) -> None:
        # Documents a known limitation: the rule only resolves the shifted
        # operand's width when it is a plain identifier with a known
        # `Symbol.bit_width`. A richer shifted operand -- here `(x + q)` --
        # is silently skipped even though its self-determined width could in
        # principle still make the shift amount out of range.
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              wire [7:0] q;
              wire [7:0] y;
              assign y = (x + q) << 8;
            endmodule
            """
        )

        assert diagnostics == []

    def test_flags_shift_amount_out_of_range_on_part_select(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              wire [3:0] y;
              assign y = x[3:0] << 4;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_parameterized_shift_amount_out_of_range(self) -> None:
        diagnostics = _diagnostics(
            """
            module top #(parameter WIDTH = 8, parameter SHIFT = 8);
              wire [WIDTH-1:0] x;
              wire [WIDTH-1:0] y;
              assign y = x << SHIFT;
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_does_not_flag_valid_parameterized_shift(self) -> None:
        diagnostics = _diagnostics(
            """
            module top #(parameter WIDTH = 8, parameter SHIFT = 4);
              wire [WIDTH-1:0] x;
              wire [WIDTH-1:0] y;
              assign y = x << SHIFT;
            endmodule
            """
        )
        assert diagnostics == []

