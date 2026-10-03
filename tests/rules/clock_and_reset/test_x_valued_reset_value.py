from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.clock_and_reset.x_valued_reset_value import AsyncResetXZValueRule


from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/clock_and_reset/test_x_valued_reset_value.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "ASYNC_RESET_XZ_VALUE"]


class TestAsyncResetXZValueRule:
    @pytest.fixture
    def rule(self) -> AsyncResetXZValueRule:
        return AsyncResetXZValueRule()

    def test_rule_has_correct_code(self, rule: AsyncResetXZValueRule) -> None:
        assert rule.code == "ASYNC_RESET_XZ_VALUE"

    def test_flags_x_in_async_reset_if_branch(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst, output reg q);
              always @(posedge clk or posedge rst) begin
                if (rst)
                  q <= 1'bx;
                else
                  q <= 1'b0;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_x_in_async_reset_else_branch(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst, output reg q);
              always @(posedge clk or posedge rst) begin
                if (rst)
                  q <= 1'b0;
                else
                  q <= 1'bx;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_sync_reset_block(self) -> None:
        # The reset signal isn't in the sensitivity list here, so it has no
        # structural marker distinguishing it from an ordinary data-path if,
        # so it is deliberately out of scope.
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst, output reg q);
              always @(posedge clk) begin
                if (rst)
                  q <= 1'bx;
                else
                  q <= 1'b0;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_flags_x_with_negedge_active_low_reset_polarity(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst_n, output reg q);
              always @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                  q <= 1'bx;
                else
                  q <= 1'b0;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_z_literal_in_async_reset_conditional(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst, output reg q);
              always @(posedge clk or posedge rst) begin
                if (rst)
                  q <= 1'bz;
                else
                  q <= 1'b0;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_x_assigned_with_blocking_assignment(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst, output reg q);
              always @(posedge clk or posedge rst) begin
                if (rst)
                  q = 1'bx;
                else
                  q = 1'b0;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_unrelated_if_outside_reset_conditional(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst, input en, output reg q, output reg y);
              always @(posedge clk or posedge rst) begin
                if (rst)
                  q <= 1'b0;
                else
                  q <= 1'b1;

                if (en)
                  y <= 1'bx;
              end
            endmodule
            """
        )

        assert diagnostics == []
