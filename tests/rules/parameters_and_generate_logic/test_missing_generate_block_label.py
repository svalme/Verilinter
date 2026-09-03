import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.parameters_and_generate_logic.missing_generate_block_label import MissingGenerateBlockLabelRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "MISSING_GENERATE_BLOCK_LABEL"]


class TestMissingGenerateBlockLabelRule:
    @pytest.fixture
    def rule(self) -> MissingGenerateBlockLabelRule:
        return MissingGenerateBlockLabelRule()

    def test_rule_has_correct_code(self, rule: MissingGenerateBlockLabelRule) -> None:
        assert rule.code == "MISSING_GENERATE_BLOCK_LABEL"

    def test_flags_unlabeled_loop_generate_block(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              genvar i;
              generate
                for (i = 0; i < 4; i = i + 1) begin
                  wire w;
                end
              endgenerate
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_labeled_loop_generate_block(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              genvar i;
              generate
                for (i = 0; i < 4; i = i + 1) begin : g_bit
                  wire w;
                end
              endgenerate
            endmodule
            """
        )

        assert diagnostics == []

    def test_flags_each_unlabeled_if_generate_branch(self) -> None:
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

        assert len(diagnostics) == 2

    def test_does_not_flag_labeled_if_generate_branches(self) -> None:
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

    def test_flags_unlabeled_case_generate_items(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic sel, output logic y);
              generate
                case (sel)
                  1'b0: begin
                    assign y = 1'b0;
                  end
                  default: begin
                    assign y = 1'b1;
                  end
                endcase
              endgenerate
            endmodule
            """
        )

        assert len(diagnostics) == 2

    def test_does_not_flag_generate_body_with_no_begin_end(self) -> None:
        # An unwrapped single-statement generate body (no `begin`/`end`) never
        # becomes a GenerateBlockSyntax, so it is a known, undetected case here.
        diagnostics = _diagnostics(
            """
            module top;
              generate
                if (1)
                  wire w;
              endgenerate
            endmodule
            """
        )

        assert diagnostics == []
