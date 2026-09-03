import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.width_and_signedness.literal_width_overflow import LiteralWidthOverflowRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
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
