import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.conditional_and_case_statements.casex_casez_wildcard_case_item import (
    CasexCasezWildcardCaseItemRule,
)


from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    assert_no_parse_errors("tests/rules/conditional_and_case_statements/test_casex_casez_wildcard_case_item.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "CASEX_CASEZ_WILDCARD_CASE_ITEM"]


class TestCasexCasezWildcardCaseItemRule:
    @pytest.fixture
    def rule(self) -> CasexCasezWildcardCaseItemRule:
        return CasexCasezWildcardCaseItemRule()

    def test_rule_has_correct_code(self, rule: CasexCasezWildcardCaseItemRule) -> None:
        assert rule.code == "CASEX_CASEZ_WILDCARD_CASE_ITEM"

    def test_flags_all_x_item_in_casex(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input [3:0] sel, output reg y);
              always @(*) begin
                casex(sel)
                  4'bxxxx: y = 1;
                  default: y = 0;
                endcase
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_all_z_item_in_casez(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input [3:0] sel, output reg y);
              always @(*) begin
                casez(sel)
                  4'bzzzz: y = 1;
                  default: y = 0;
                endcase
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_all_x_item_in_casez(self) -> None:
        # x is not a wildcard in casez -- only z/? are -- so this item does
        # not actually match every value the way it would in casex.
        diagnostics = _diagnostics(
            """
            module top(input [3:0] sel, output reg y);
              always @(*) begin
                casez(sel)
                  4'bxxxx: y = 1;
                  default: y = 0;
                endcase
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_plain_case(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input [3:0] sel, output reg y);
              always @(*) begin
                case(sel)
                  4'bxxxx: y = 1;
                  default: y = 0;
                endcase
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_mixed_item(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input [3:0] sel, output reg y);
              always @(*) begin
                casex(sel)
                  4'bx01z: y = 1;
                  default: y = 0;
                endcase
              end
            endmodule
            """
        )

        assert diagnostics == []
