import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.operators_and_expressions.xz_equality_comparison import XZEqualityComparisonRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "XZ_EQUALITY_COMPARISON"]


class TestXZEqualityComparisonRule:
    @pytest.fixture
    def rule(self) -> XZEqualityComparisonRule:
        return XZEqualityComparisonRule()

    def test_rule_has_correct_code(self, rule: XZEqualityComparisonRule) -> None:
        assert rule.code == "XZ_EQUALITY_COMPARISON"

    def test_flags_equality_against_x_literal(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input a, output y);
              assign y = (a == 1'bx);
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_inequality_against_z_literal_on_left(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input [3:0] b, output y);
              assign y = (4'bzzzz != b);
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_case_equality(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input a, output y);
              assign y = (a === 1'bx);
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_wildcard_equality(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input [3:0] a, input [3:0] b, output y);
              assign y = (a ==? b);
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_ordinary_numeric_equality(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input [3:0] a, output y);
              assign y = (a == 4'h0);
            endmodule
            """
        )

        assert diagnostics == []
