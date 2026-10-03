from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.conditional_and_case_statements.case_overlapping_items import (
    CaseOverlappingItemsRule,
)

from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    assert_no_parse_errors(
        "tests/rules/conditional_and_case_statements/test_case_overlapping_items.py",
        tree,
    )
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "CASE_OVERLAPPING_ITEMS"]


class TestCaseOverlappingItemsRule:
    @pytest.fixture
    def rule(self) -> CaseOverlappingItemsRule:
        return CaseOverlappingItemsRule()

    def test_rule_has_correct_code(self, rule: CaseOverlappingItemsRule) -> None:
        assert rule.code == "CASE_OVERLAPPING_ITEMS"

    def test_flags_numeric_duplicate_standard_case(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input [3:0] sel, output reg y);
              always @(*) begin
                case (sel)
                  4'd2: y = 1;
                  4'b0010: y = 0;
                  default: y = 0;
                endcase
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_flags_duplicate_items_in_same_branch(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input [3:0] sel, output reg y);
              always @(*) begin
                case (sel)
                  4'd2, 4'd2: y = 1;
                  default: y = 0;
                endcase
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_flags_casez_wildcard_overlap(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input [2:0] sel, output reg y);
              always @(*) begin
                casez (sel)
                  3'b00?: y = 1;
                  3'b001: y = 0;
                  default: y = 0;
                endcase
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_flags_casez_multi_item_overlap(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input [2:0] sel, output reg y);
              always @(*) begin
                casez (sel)
                  3'b11?, 3'b???: y = 1;
                  default: y = 0;
                endcase
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_flags_casex_wildcard_overlap(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input [2:0] sel, output reg y);
              always @(*) begin
                casex (sel)
                  3'b0x1: y = 1;
                  3'b001: y = 0;
                  default: y = 0;
                endcase
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_does_not_flag_disjoint_values(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input [3:0] sel, output reg y);
              always @(*) begin
                case (sel)
                  4'd1: y = 1;
                  4'd2: y = 0;
                  default: y = 0;
                endcase
              end
            endmodule
            """
        )
        assert diagnostics == []

    def test_does_not_flag_disjoint_wildcards(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input [1:0] sel, output reg y);
              always @(*) begin
                casez (sel)
                  2'b0?: y = 1;
                  2'b1?: y = 0;
                  default: y = 0;
                endcase
              end
            endmodule
            """
        )
        assert diagnostics == []
