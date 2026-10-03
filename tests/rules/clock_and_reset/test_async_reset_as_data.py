from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.handlers.register_handlers import *
from src.pkg.rules.clock_and_reset.async_reset_as_data import AsyncResetAsDataRule
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
    assert_no_parse_errors("tests/rules/clock_and_reset/test_async_reset_as_data.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "ASYNC_RESET_AS_DATA"]


class TestAsyncResetAsDataRule:
    @pytest.fixture
    def rule(self) -> AsyncResetAsDataRule:
        return AsyncResetAsDataRule()

    def test_rule_metadata(self, rule: AsyncResetAsDataRule) -> None:
        assert rule.code == "ASYNC_RESET_AS_DATA"
        assert rule.category == "rtl_correctness"
        assert "rtl_strict" in rule.default_profiles

    def test_clean_async_reset_usage_passes(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst_n, input d, output reg q);
              always @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                  q <= 1'b0;
                else
                  q <= d;
              end
            endmodule
            """
        )
        assert diagnostics == []

    def test_passing_async_reset_to_submodule_port_passes(self) -> None:
        diagnostics = _diagnostics(
            """
            module child(input clk, input rst_n);
              always @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin end
              end
            endmodule

            module top(input clk, input rst_n);
              always @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin end
              end

              child u_child (
                .clk(clk),
                .rst_n(rst_n)
              );
            endmodule
            """
        )
        assert diagnostics == []

    def test_flags_async_reset_in_continuous_assignment_rhs(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst_n, input a, input b, output wire y, output reg q);
              always @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                  q <= 1'b0;
                else
                  q <= a;
              end

              assign y = rst_n ? a : b;
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert "Asynchronous reset signal read as a data operand" in diagnostics[0]["message"]

    def test_flags_async_reset_in_procedural_datapath_rhs(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst_n, input d, output reg q, output reg [1:0] state);
              always @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                  q <= 1'b0;
                else begin
                  q <= d;
                  state <= {rst_n, d};
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_flags_async_reset_read_inside_reset_branch_body(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst_n, input d, output reg q);
              always @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                  q <= rst_n;
                else
                  q <= d;
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_pure_synchronous_reset_is_not_flagged(self) -> None:
        # Synchronous resets (like a plain `resetn`) are data signals and never
        # edge-qualified in sensitivity lists; they must NOT be flagged when read in data expressions.
        diagnostics = _diagnostics(
            """
            module top(input clk, input resetn, input d, output reg q, output wire y);
              always @(posedge clk) begin
                if (!resetn)
                  q <= 1'b0;
                else
                  q <= d;
              end

              assign y = resetn & d;
            endmodule
            """
        )
        assert diagnostics == []

    def test_flags_async_reset_in_non_reset_conditional(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst_n, input en, output reg q);
              always @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                  q <= 1'b0;
                else begin
                  if (rst_n && en)
                    q <= 1'b1;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_display_system_task_with_async_reset_is_not_flagged(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst_n, input d, output reg q);
              always @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                  $display("Reset active, rst_n is %b", rst_n);
                  q <= 1'b0;
                end else begin
                  q <= d;
                end
              end
            endmodule
            """
        )
        assert diagnostics == []
