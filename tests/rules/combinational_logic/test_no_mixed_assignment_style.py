from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.combinational_logic.no_mixed_assignment_style import NoMixedAssignmentStyleRule


from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/combinational_logic/test_no_mixed_assignment_style.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "NO_MIXED_ASSIGNMENT_STYLE"]


class TestNoMixedAssignmentStyleRule:
    @pytest.fixture
    def rule(self) -> NoMixedAssignmentStyleRule:
        return NoMixedAssignmentStyleRule()

    def test_rule_has_correct_code(self, rule: NoMixedAssignmentStyleRule) -> None:
        assert rule.code == "NO_MIXED_ASSIGNMENT_STYLE"

    def test_rule_has_correct_message(self, rule: NoMixedAssignmentStyleRule) -> None:
        assert rule.message == "Mixed blocking and non-blocking assignments used in the same procedural block"

    def test_flags_blocking_then_nonblocking(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic clk);
              logic a, b;
              always @(posedge clk) begin
                a = 1;
                b <= 1;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_MIXED_ASSIGNMENT_STYLE"

    def test_flags_nonblocking_then_blocking(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic clk);
              logic a, b;
              always @(posedge clk) begin
                a <= 1;
                b = 1;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_all_blocking_block(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic a);
              logic x, y;
              always @(a) begin
                x = a;
                y = a;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_all_nonblocking_block(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic clk);
              logic a, b;
              always @(posedge clk) begin
                a <= 1;
                b <= 1;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_single_assignment_block(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic a);
              logic x;
              always @(a) begin
                x = a;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_reports_once_per_block_even_with_further_mismatches(self) -> None:
        """Only the first assignment whose style differs from the block's first
        assignment is reported -- not every subsequent mismatch too."""
        diagnostics = _diagnostics(
            """
            module top(input logic clk);
              logic a, b, c, d;
              always @(posedge clk) begin
                a <= 1;
                b = 1;
                c <= 1;
                d = 1;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_mixed_block_does_not_leak_into_sibling_clean_block(self) -> None:
        """Regression guard for the ProceduralBlockHandler-computed ctx.data
        optimization: each procedural block's
        mix-trigger fact must not leak into a sibling block's diagnostics."""
        diagnostics = _diagnostics(
            """
            module top(input logic clk);
              logic a, b, c, d;
              always @(posedge clk) begin
                a <= 1;
                b <= 1;
              end
              always @(posedge clk) begin
                c = 1;
                d <= 1;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_continuous_assign(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic a, output logic y);
              assign y = a;
            endmodule
            """
        )

        assert diagnostics == []
