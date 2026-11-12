import pytest

from src.pkg.handlers.register_handlers import *  # noqa: F401,F403
from src.pkg.parser.parse import parse_text
from src.pkg.rules.register_rules import rule_runner
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(statement: str) -> list[dict]:
    code = f"""
    module top(input logic clk);
      logic [7:0] r;
      logic [7:0] q [3:0];
      logic [1:0] i;
      logic [1:0] j;
      always_ff @(posedge clk) begin
        {statement}
      end
    endmodule
    """
    symbol_table = SymbolTable()
    walker = Walker(dispatch)
    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/combinational_logic/test_no_self_assignment.py", tree)
    walker.walk(tree.root, tree, Context(scope=symbol_table.global_scope), symbol_table)
    return [d for d in rule_runner.run(walker.results) if d["code"] == "NO_SELF_ASSIGNMENT"]


class TestNoSelfAssignment:
    @pytest.mark.parametrize("statement", ["r <= r;", "r[3] <= r[3];", "q[i] <= q[i];", "r[3:0] <= r[3:0];", "q[0][1] <= q[0][1];"])
    def test_flags_a_target_assigned_to_itself(self, statement: str) -> None:
        assert len(_diagnostics(statement)) == 1

    @pytest.mark.parametrize(
        "statement",
        [
            "q[i] <= q[i-1];",
            "q[1] <= q[0];",
            "q[i] <= q[j];",
            "r[3:0] <= r[7:4];",
            "r[0] <= r[1];",
            "r <= r[3:0];",
            "q[0][1] <= q[0][2];",
        ],
    )
    def test_ignores_a_different_part_of_the_same_variable(self, statement: str) -> None:
        assert _diagnostics(statement) == []
