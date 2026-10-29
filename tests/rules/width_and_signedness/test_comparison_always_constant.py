from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.width_and_signedness.comparison_always_constant import (
    ComparisonAlwaysConstantRule,
)
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(condition: str) -> list[dict]:
    code = f"""
    module top;
      bit [2:0] u;
      reg [3:0] r;
      int s;
      initial begin
        if ({condition}) $stop;
      end
    endmodule
    """
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/width_and_signedness/test_comparison_always_constant.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "COMPARISON_ALWAYS_CONSTANT"]


class TestComparisonAlwaysConstantRule:
    def test_rule_metadata(self) -> None:
        rule = ComparisonAlwaysConstantRule()
        assert rule.code == "COMPARISON_ALWAYS_CONSTANT"
        assert rule.category == "rtl_correctness"

    @pytest.mark.parametrize(
        "condition",
        ["u < 0", "u >= 0", "u > 3'b111", "u > 7", "u <= 7", "r <= 15", "0 > u", "7 < u", "15 >= r"],
    )
    def test_flags_comparison_at_range_limit(self, condition: str) -> None:
        assert len(_diagnostics(condition)) == 1

    @pytest.mark.parametrize(
        "condition",
        ["u > 6", "u < 7", "u >= 1", "u <= 6", "r < 15", "u == 0", "u != 7", "s < 0", "s >= 0", "u < r", "u > 8"],
    )
    def test_ignores_comparison_that_can_vary_or_is_not_a_boundary(self, condition: str) -> None:
        assert _diagnostics(condition) == []
