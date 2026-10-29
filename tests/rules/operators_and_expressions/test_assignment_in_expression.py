import pytest

from src.pkg.handlers.register_handlers import *
from src.pkg.parser.parse import parse_text
from src.pkg.rules.operators_and_expressions.assignment_in_expression import AssignmentInExpressionRule
from src.pkg.rules.register_rules import rule_runner
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/operators_and_expressions/test_assignment_in_expression.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "ASSIGNEQEXPR"]


class TestAssignmentInExpressionRule:
    def test_rule_has_correct_code(self) -> None:
        assert AssignmentInExpressionRule().code == "ASSIGNEQEXPR"

    def test_flags_assignments_in_conditional_expression(self) -> None:
        code = """
module m(input b, output d, output e);
  assign d = (e = 1) ? 1 : (e = 0) ? b : 0;
endmodule
"""
        assert len(_diagnostics(code)) == 2

    def test_flags_assignment_in_if_condition(self) -> None:
        code = """
module m(input a, output reg x, output reg y);
  always @* begin
    if ((x = a)) y = 1;
    else y = 0;
  end
endmodule
"""
        assert len(_diagnostics(code)) == 1

    @pytest.mark.parametrize(
        "body",
        [
            "assign w = a;",
            "always @* begin x = a; x += 1; end",
            "always @* for (i = 0; i < 3; i = i + 1) x = a;",
            "always @* for (i = 0, x = 1; i < 3; i++, y = 0) x = a;",
            "always @* begin force x = a; release x; end",
            "initial begin #1 x = 1; @(posedge a) x = 0; end",
            "task t; i = 1; endtask",
        ],
    )
    def test_ignores_assignment_statements(self, body: str) -> None:
        code = f"module m(input a); wire w; integer i; reg x, y; {body} endmodule"
        assert _diagnostics(code) == []

    def test_ignores_equality_comparison(self) -> None:
        code = "module m(input a, output d); assign d = (a == 1) ? 1 : 0; endmodule"
        assert _diagnostics(code) == []

    def test_ignores_nonblocking_assignment(self) -> None:
        code = "module m(input clk, input a, output reg q); always @(posedge clk) q <= a; endmodule"
        assert _diagnostics(code) == []
