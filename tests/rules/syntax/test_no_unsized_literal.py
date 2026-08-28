import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.syntax.no_unsized_literal import NoUnsizedLiteralRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
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
