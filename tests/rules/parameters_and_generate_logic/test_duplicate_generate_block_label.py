from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.parameters_and_generate_logic.duplicate_generate_block_label import DuplicateGenerateBlockLabelRule


from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/parameters_and_generate_logic/test_duplicate_generate_block_label.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "DUPLICATE_GENERATE_BLOCK_LABEL"]


class TestDuplicateGenerateBlockLabelRule:
    @pytest.fixture
    def rule(self) -> DuplicateGenerateBlockLabelRule:
        return DuplicateGenerateBlockLabelRule()

    def test_rule_has_correct_code(self, rule: DuplicateGenerateBlockLabelRule) -> None:
        assert rule.code == "DUPLICATE_GENERATE_BLOCK_LABEL"

    def test_flags_if_else_branches_sharing_label(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              generate
                if (1) begin : g_block
                  wire w;
                end else begin : g_block
                  wire w2;
                end
              endgenerate
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_distinct_if_else_labels(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              generate
                if (1) begin : g_then
                  wire w;
                end else begin : g_else
                  wire w2;
                end
              endgenerate
            endmodule
            """
        )

        assert diagnostics == []

    def test_flags_case_generate_items_sharing_label(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic sel, output logic y);
              generate
                case (sel)
                  1'b0: begin : g_item
                    assign y = 1'b0;
                  end
                  default: begin : g_item
                    assign y = 1'b1;
                  end
                endcase
              endgenerate
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_unlabeled_branches(self) -> None:
        # Two unlabeled branches aren't a name collision -- MISSING_GENERATE_BLOCK_LABEL's concern.
        diagnostics = _diagnostics(
            """
            module top;
              generate
                if (1) begin
                  wire w;
                end else begin
                  wire w2;
                end
              endgenerate
            endmodule
            """
        )

        assert diagnostics == []
