import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.sequential_logic.no_blocking_sequential_logic import (
    NoBlockingAssignmentInSequentialRule,
)

from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    assert_no_parse_errors(
        "tests/rules/sequential_logic/test_no_blocking_sequential_logic.py", tree
    )
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "NO_BLOCKING_SEQUENTIAL"]


class TestNoBlockingAssignmentInSequentialRule:
    @pytest.fixture
    def rule(self) -> NoBlockingAssignmentInSequentialRule:
        return NoBlockingAssignmentInSequentialRule()

    def test_rule_has_correct_code(self, rule: NoBlockingAssignmentInSequentialRule) -> None:
        assert rule.code == "NO_BLOCKING_SEQUENTIAL"

    def test_flags_blocking_assignment_in_clocked_always(self) -> None:
        code = """
        module test(input clk, input d, output reg q);
            always @(posedge clk) begin
                q = d;
            end
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 1
        assert diags[0]["code"] == "NO_BLOCKING_SEQUENTIAL"

    def test_allows_blocking_assignment_in_combinational_always(self) -> None:
        code = """
        module test(input a, input b, output reg y);
            always @* begin
                y = a & b;
            end
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 0

    def test_allows_for_loop_header_assignments_in_sequential_block(self) -> None:
        code = """
        module test(input clk, input [7:0] d, output reg [7:0] q);
            integer i;
            always @(posedge clk) begin
                for (i = 0; i < 8; i = i + 1) begin
                    q[i] <= d[i];
                end
            end
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 0

    def test_flags_blocking_assignment_inside_for_loop_body(self) -> None:
        code = """
        module test(input clk, input [7:0] d, output reg [7:0] q);
            integer i;
            always @(posedge clk) begin
                for (i = 0; i < 8; i = i + 1) begin
                    q[i] = d[i];
                end
            end
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 1
        assert diags[0]["code"] == "NO_BLOCKING_SEQUENTIAL"
