from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.maintainability_and_complexity.infinite_loop import InfiniteLoopRule

from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/maintainability_and_complexity/test_infinite_loop.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "INFINITELOOP"]


class TestInfiniteLoopRule:
    @pytest.fixture
    def rule(self) -> InfiniteLoopRule:
        return InfiniteLoopRule()

    def test_rule_has_correct_code(self, rule: InfiniteLoopRule) -> None:
        assert rule.code == "INFINITELOOP"

    def test_flags_empty_forever_loop(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              initial begin
                forever begin
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "INFINITELOOP"

    def test_flags_forever_loop_without_exit_or_timing(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [7:0] count;
              initial begin
                forever begin
                  count = count + 1;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "INFINITELOOP"

    def test_flags_while_one_loop(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [7:0] count;
              initial begin
                while (1) begin
                  count = count + 1;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "INFINITELOOP"

    def test_flags_while_literal_vector_true(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [7:0] count;
              initial begin
                while (1'b1) begin
                  count = count + 1;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "INFINITELOOP"

    def test_flags_for_loop_with_omitted_condition(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [7:0] count;
              initial begin
                for (int i = 0; ; i++) begin
                  count = count + 1;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "INFINITELOOP"

    def test_flags_for_loop_with_constant_true_condition(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [7:0] count;
              initial begin
                for (int i = 0; 1; i++) begin
                  count = count + 1;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "INFINITELOOP"

    def test_flags_do_while_constant_true_loop(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [7:0] count;
              initial begin
                do begin
                  count = count + 1;
                end while (1);
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "INFINITELOOP"

    def test_flags_outer_loop_when_break_is_in_inner_loop(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [7:0] count;
              initial begin
                forever begin
                  while (count < 10) begin
                    break;
                  end
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "INFINITELOOP"

    def test_allows_variable_condition_while_loop(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg running;
              reg [7:0] count;
              initial begin
                while (running) begin
                  count = count + 1;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 0

    def test_allows_standard_for_loop(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [7:0] count;
              initial begin
                for (int i = 0; i < 16; i++) begin
                  count = count + 1;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 0

    def test_allows_loop_with_break(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [7:0] count;
              initial begin
                while (1) begin
                  if (count == 8) break;
                  count = count + 1;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 0

    def test_allows_loop_with_return(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              function automatic int find_item();
                while (1) begin
                  return 42;
                end
              endfunction
            endmodule
            """
        )
        assert len(diagnostics) == 0

    def test_allows_loop_with_timing_delay(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg clk;
              initial begin
                forever begin
                  #5 clk = ~clk;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 0

    def test_allows_loop_with_event_control(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg clk;
              reg [7:0] count;
              initial begin
                forever begin
                  @(posedge clk);
                  count = count + 1;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 0

    def test_allows_loop_with_wait_statement(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg ready;
              initial begin
                forever begin
                  wait (ready);
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 0

    def test_allows_loop_with_finish(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              initial begin
                forever begin
                  $finish;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 0
