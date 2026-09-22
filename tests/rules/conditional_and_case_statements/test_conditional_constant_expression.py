import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.conditional_and_case_statements.conditional_constant_expression import (
    ConditionalConstantExpressionRule,
)

from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    assert_no_parse_errors(
        "tests/rules/conditional_and_case_statements/test_conditional_constant_expression.py",
        tree,
    )
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "CONDITIONAL_CONSTANT_EXPRESSION"]


class TestConditionalConstantExpressionRule:
    @pytest.fixture
    def rule(self) -> ConditionalConstantExpressionRule:
        return ConditionalConstantExpressionRule()

    def test_rule_has_correct_code(self, rule: ConditionalConstantExpressionRule) -> None:
        assert rule.code == "CONDITIONAL_CONSTANT_EXPRESSION"

    def test_flags_constant_0_procedural_if(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input a, output reg y);
              always @(*) begin
                if (0) begin
                  y = a;
                end else begin
                  y = ~a;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_flags_constant_1_procedural_if(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input a, output reg y);
              always @(*) begin
                if (1) begin
                  y = a;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_flags_constant_sized_vector_0(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input a, output reg y);
              always @(*) begin
                if (1'b0) begin
                  y = a;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_flags_constant_sized_vector_1(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input a, output reg y);
              always @(*) begin
                if (1'b1) begin
                  y = a;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_flags_constant_unbased_0(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input a, output reg y);
              always @(*) begin
                if ('0) begin
                  y = a;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_flags_constant_unbased_1(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input a, output reg y);
              always @(*) begin
                if ('1) begin
                  y = a;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_flags_constant_expression_equality(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input a, output reg y);
              always @(*) begin
                if (1 == 0) begin
                  y = a;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_flags_constant_expression_logical_and(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input a, output reg y);
              always @(*) begin
                if (1'b1 && 1'b0) begin
                  y = a;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_flags_else_if_constant(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input a, output reg y);
              always @(*) begin
                if (a) begin
                  y = 1'b1;
                end else if (0) begin
                  y = 1'b0;
                end else begin
                  y = 1'b1;
                end
              end
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_does_not_flag_dynamic_condition(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input a, output reg y);
              always @(*) begin
                if (a) begin
                  y = 1'b1;
                end else begin
                  y = 1'b0;
                end
              end
            endmodule
            """
        )
        assert diagnostics == []

    def test_does_not_flag_generate_if_constant(self) -> None:
        diagnostics = _diagnostics(
            """
            module top #(parameter ENABLE = 1) (input a, output y);
              if (ENABLE == 1) begin : gen_blk
                assign y = a;
              end else begin : gen_blk
                assign y = ~a;
              end
            endmodule
            """
        )
        assert diagnostics == []
