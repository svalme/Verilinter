import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.width_and_signedness.no_unsized_literal import NoUnsizedLiteralRule


from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    assert_no_parse_errors("tests/rules/width_and_signedness/test_no_unsized_literal.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "NO_UNSIZED_LITERAL"]


class TestNoUnsizedLiteralRule:
    @pytest.fixture
    def rule(self) -> NoUnsizedLiteralRule:
        return NoUnsizedLiteralRule()

    def test_rule_has_correct_code(self, rule: NoUnsizedLiteralRule) -> None:
        assert rule.code == "NO_UNSIZED_LITERAL"

    def test_flags_unsized_literal_in_continuous_assign(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              assign x = 5;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_unsized_literal_in_procedural_assignment(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [7:0] x;
              always @(*) begin
                x = 5;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_unsized_literal_in_nonblocking_assignment(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic clk);
              reg [7:0] x;
              always @(posedge clk) begin
                x <= 5;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_sized_literal(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [7:0] x;
              always @(*) begin
                x = 8'd5;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_unbased_unsized_literal(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg x;
              always @(*) begin
                x = '0;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_parameter_initializer(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              parameter P = 5;
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_procedural_for_loop_header(self) -> None:
        """The loop init/step clauses (`i = 0`, `i = i + 1`) parse as ordinary
        AssignmentExpression nodes parented by ForLoopStatementSyntax -- this
        rule must not flag them even though the shape otherwise matches."""
        diagnostics = _diagnostics(
            """
            module top;
              reg [3:0] i;
              reg x;
              always @(*) begin
                for (i = 0; i < 4; i = i + 1) begin
                  x = 8'd1;
                end
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_flags_body_assignment_inside_for_loop(self) -> None:
        """Only the loop header itself is exempt -- an unsized literal assigned
        inside the loop body is still a real finding."""
        diagnostics = _diagnostics(
            """
            module top;
              reg [3:0] i;
              reg x;
              always @(*) begin
                for (i = 0; i < 4; i = i + 1) begin
                  x = 1;
                end
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_unsized_literal_as_concatenation_member(self) -> None:
        # Documents a known limitation: the check requires the literal to be
        # the assignment's direct `.right` node, so an unsized literal nested
        # inside a concatenation (`{a, 5}`) is silently skipped here, unlike
        # ASSIGNMENT_WIDTH_MISMATCH's dedicated concatenation-member handling.
        diagnostics = _diagnostics(
            """
            module top;
              wire [3:0] a;
              wire [7:0] x;
              assign x = {a, 5};
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_unsized_literal_under_unary_minus(self) -> None:
        # Documents a known limitation: `-5`'s top-level node is a unary-minus
        # expression, not the literal itself, so the direct-RHS check never
        # sees an INTEGER_LITERAL_EXPRESSION_KIND node here at all.
        diagnostics = _diagnostics(
            """
            module top;
              reg signed [7:0] x;
              always @(*) begin
                x = -5;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_flags_unsized_literal_in_both_if_and_else_branches(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [7:0] x;
              reg sel;
              always @(*) begin
                if (sel)
                  x = 5;
                else
                  x = 6;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 2
