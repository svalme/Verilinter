from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.width_and_signedness.literal_width_overflow import LiteralWidthOverflowRule


from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/width_and_signedness/test_literal_width_overflow.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "LITERAL_WIDTH_OVERFLOW"]


class TestLiteralWidthOverflowRule:
    @pytest.fixture
    def rule(self) -> LiteralWidthOverflowRule:
        return LiteralWidthOverflowRule()

    def test_rule_has_correct_code(self, rule: LiteralWidthOverflowRule) -> None:
        assert rule.code == "LITERAL_WIDTH_OVERFLOW"

    def test_flags_hex_literal_that_overflows_declared_width(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [3:0] x;
              assign x = 4'hFF;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_decimal_literal_that_overflows_declared_width(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [2:0] x;
              assign x = 3'd9;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_literal_that_fits(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              assign x = 8'hFF;
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_literal_with_x_digits(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [3:0] x;
              assign x = 4'bxxxx;
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_signed_literal(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [3:0] x;
              assign x = 4'shF;
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_unsized_literal(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [3:0] x;
              assign x = 5;
            endmodule
            """
        )

        assert diagnostics == []

    def test_flags_binary_literal_that_overflows_declared_width(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [2:0] x;
              assign x = 3'b1111;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_octal_literal_that_overflows_declared_width(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [2:0] x;
              assign x = 3'o10;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_value_that_exactly_fits_declared_width(self) -> None:
        # Boundary: 3'b111's value (7) needs exactly 3 bits, matching the
        # declared width -- one bit below `test_flags_decimal_literal_that_
        # overflows_declared_width`'s "just above" case.
        diagnostics = _diagnostics(
            """
            module top;
              wire [2:0] x;
              assign x = 3'b111;
            endmodule
            """
        )

        assert diagnostics == []

    def test_flags_overflow_in_nonblocking_procedural_assignment(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk);
              reg [2:0] x;
              always @(posedge clk) begin
                x <= 3'd9;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_overflow_with_underscores_in_value(self) -> None:
        # Confirms the leading `_`-stripping (`value_text.replace("_", "")`)
        # runs before the radix parse: 4'b1111_1's value is 5 bits (31), one
        # over its declared 4.
        diagnostics = _diagnostics(
            """
            module top;
              wire [3:0] x;
              assign x = 4'b1111_1;
            endmodule
            """
        )

        assert len(diagnostics) == 1
