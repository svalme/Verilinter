from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.width_and_signedness.comparison_signedness_mismatch import ComparisonSignednessMismatchRule
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(condition: str) -> list[dict]:
    code = f"""
    module top;
      wire [3:0] u;
      wire [3:0] v;
      wire [7:0] w;
      wire signed [3:0] s;
      wire signed [7:0] sw;
      parameter P = 1;
      wire out;
      assign out = ({condition});
    endmodule
    """
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/width_and_signedness/test_comparison_signedness_mismatch.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "COMPARISON_SIGNEDNESS_MISMATCH"]


class TestComparisonSignednessMismatchRule:
    def test_rule_metadata(self) -> None:
        rule = ComparisonSignednessMismatchRule()
        assert rule.code == "COMPARISON_SIGNEDNESS_MISMATCH"
        assert rule.category == "rtl_correctness"

    @pytest.mark.parametrize("condition", ['u < s', 's >= u', 'u > sw', 'u == sw', 'w != s'])
    def test_flags(self, condition: str) -> None:
        assert len(_diagnostics(condition)) == 1

    @pytest.mark.parametrize("condition", ['u < v', 's < sw', 'u == s', 's < 0', "u < 4'd3", 'u == v', 'u < w', 's < 5', 'u < P', 'P > u'])
    def test_ignores(self, condition: str) -> None:
        assert _diagnostics(condition) == []
