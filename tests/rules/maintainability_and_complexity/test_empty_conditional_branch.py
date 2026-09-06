import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.maintainability_and_complexity.empty_conditional_branch import EmptyConditionalBranchRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "EMPTY_CONDITIONAL_BRANCH"]


class TestEmptyConditionalBranchRule:
    @pytest.fixture
    def rule(self) -> EmptyConditionalBranchRule:
        return EmptyConditionalBranchRule()

    def test_rule_has_correct_code(self, rule: EmptyConditionalBranchRule) -> None:
        assert rule.code == "EMPTY_CONDITIONAL_BRANCH"

    def test_flags_empty_if_branch_as_bare_semicolon(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input a, output reg y);
              always @(*) begin
                if (a) ;
                else y = 1'b1;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_empty_else_branch_as_begin_end(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input a, output reg y);
              always @(*) begin
                if (a) y = 1'b1;
                else begin end
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_empty_case_item_body(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic sel, output logic y);
              always_comb begin
                case (sel)
                  1'b0: ;
                  default: y = 1'b1;
                endcase
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_non_empty_branches(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input a, output reg y);
              always @(*) begin
                if (a) y = 1'b1;
                else y = 1'b0;
              end
            endmodule
            """
        )

        assert diagnostics == []
