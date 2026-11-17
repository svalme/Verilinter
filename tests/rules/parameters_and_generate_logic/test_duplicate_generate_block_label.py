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

    def test_does_not_flag_if_else_branches_sharing_label(self) -> None:
        # Only one branch of an if-generate is elaborated, so the branches never coexist.
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

        assert diagnostics == []

    def test_flags_two_separate_if_generates_sharing_label_even_with_exclusive_conditions(self) -> None:
        diagnostics = _diagnostics(
            """
            module top #(parameter P = 1);
              if (P) begin : g_block
                wire w;
              end
              if (!P) begin : g_block
                wire w2;
              end
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

    def test_does_not_flag_case_generate_items_sharing_label(self) -> None:
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

        assert diagnostics == []

    def test_does_not_flag_every_branch_of_an_else_if_chain_sharing_a_label(self) -> None:
        diagnostics = _diagnostics(
            """
            module top #(parameter P = 1, Q = 1);
              if (P) begin : g_block
                wire a;
              end else if (Q) begin : g_block
                wire b;
              end else begin : g_block
                wire c;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_flags_a_construct_that_reuses_a_label_of_an_else_if_chain(self) -> None:
        diagnostics = _diagnostics(
            """
            module top #(parameter P = 1, Q = 1);
              if (P) begin : g_block
                wire a;
              end else if (Q) begin : g_block
                wire b;
              end
              if (Q) begin : g_block
                wire c;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_constructs_of_different_kinds_sharing_a_label(self) -> None:
        loop = _diagnostics(
            """
            module top #(parameter N = 2);
              for (genvar i = 0; i < N; i++) begin : g_lane
                wire w;
              end
              if (N == 2) begin : g_lane
                wire w2;
              end
            endmodule
            """
        )
        bare = _diagnostics(
            """
            module top #(parameter P = 1);
              begin : g_part
                wire w;
              end
              if (P) begin : g_part
                wire w2;
              end
            endmodule
            """
        )
        case_and_if = _diagnostics(
            """
            module top #(parameter P = 1);
              case (P)
                0: begin : g_part
                  wire w;
                end
                default: begin : g_other
                  wire w3;
                end
              endcase
              if (P) begin : g_part
                wire w2;
              end
            endmodule
            """
        )

        assert len(loop) == 1
        assert len(bare) == 1
        assert len(case_and_if) == 1

    def test_flags_constructs_in_two_generate_regions_of_one_module(self) -> None:
        diagnostics = _diagnostics(
            """
            module top #(parameter P = 1);
              generate
                if (P) begin : g_block
                  wire w;
                end
              endgenerate
              generate
                if (!P) begin : g_block
                  wire w2;
                end
              endgenerate
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_each_later_construct_that_reuses_a_label(self) -> None:
        diagnostics = _diagnostics(
            """
            module top #(parameter P = 1);
              if (P) begin : g_block
                wire a;
              end
              if (P) begin : g_block
                wire b;
              end
              if (P) begin : g_block
                wire c;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 2

    def test_does_not_flag_the_same_label_in_a_nested_scope_or_another_module(self) -> None:
        nested = _diagnostics(
            """
            module top #(parameter P = 1);
              if (P) begin : g_block
                if (P) begin : g_block
                  wire w;
                end
              end
            endmodule
            """
        )
        other_module = _diagnostics(
            """
            module first #(parameter P = 1);
              if (P) begin : g_block
                wire w;
              end
            endmodule
            module second #(parameter P = 1);
              if (P) begin : g_block
                wire w;
              end
            endmodule
            """
        )

        assert nested == []
        assert other_module == []

    def test_flags_two_constructs_sharing_a_label_inside_one_generate_block(self) -> None:
        diagnostics = _diagnostics(
            """
            module top #(parameter P = 1);
              if (P) begin : g_outer
                if (P) begin : g_inner
                  wire a;
                end
                if (P) begin : g_inner
                  wire b;
                end
              end
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
