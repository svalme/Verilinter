from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.maintainability_and_complexity.deeply_nested_block import DeeplyNestedBlockRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "DEEPLY_NESTED_BLOCK"]


class TestDeeplyNestedBlockRule:
    @pytest.fixture
    def rule(self) -> DeeplyNestedBlockRule:
        return DeeplyNestedBlockRule()

    def test_rule_has_correct_code(self, rule: DeeplyNestedBlockRule) -> None:
        assert rule.code == "DEEPLY_NESTED_BLOCK"

    def test_flags_block_that_first_crosses_threshold(self) -> None:
        # always(1) -> if-begin(2) -> if-begin(3) -> if-begin(4) -> if-begin(5, crosses)
        diagnostics = _diagnostics(
            """
            module top(input a, input b, input c, input d, output reg y);
              always @(*) begin
                if (a) begin
                  if (b) begin
                    if (c) begin
                      if (d) begin
                        y = 1'b1;
                      end
                    end
                  end
                end
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_shallow_nesting(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input a, output reg y);
              always @(*) begin
                if (a) begin
                  y = 1'b1;
                end
              end
            endmodule
            """
        )

        assert diagnostics == []
