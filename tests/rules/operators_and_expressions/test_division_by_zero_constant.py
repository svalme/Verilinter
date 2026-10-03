from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.operators_and_expressions.division_by_zero_constant import DivisionByZeroConstantRule


from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/operators_and_expressions/test_division_by_zero_constant.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "DIVISION_BY_ZERO_CONSTANT"]


class TestDivisionByZeroConstantRule:
    @pytest.fixture
    def rule(self) -> DivisionByZeroConstantRule:
        return DivisionByZeroConstantRule()

    def test_rule_has_correct_code(self, rule: DivisionByZeroConstantRule) -> None:
        assert rule.code == "DIVISION_BY_ZERO_CONSTANT"

    def test_flags_division_by_unsized_zero(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              wire [7:0] y;
              assign y = x / 0;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_modulo_by_sized_zero(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              wire [7:0] y;
              assign y = x % 4'd0;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_division_by_nonzero_constant(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              wire [7:0] y;
              assign y = x / 2;
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_division_by_variable(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              wire [7:0] n;
              wire [7:0] y;
              assign y = x / n;
            endmodule
            """
        )

        assert diagnostics == []
