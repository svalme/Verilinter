import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.width_and_signedness.no_assignment_width_mismatch import (
    NoAssignmentWidthMismatchRule,
    NoAssignmentSignednessMismatchRule,
)


def _diagnostics(code: str, rule_code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == rule_code]


class TestNoAssignmentWidthMismatchRule:
    @pytest.fixture
    def rule(self) -> NoAssignmentWidthMismatchRule:
        return NoAssignmentWidthMismatchRule()

    def test_rule_has_correct_code(self, rule: NoAssignmentWidthMismatchRule) -> None:
        assert rule.code == "ASSIGNMENT_WIDTH_MISMATCH"

    def test_flags_narrower_identifier_assigned_to_wider_target(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              wire [3:0] y;
              assign x = y;
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )

        assert len(diagnostics) == 1

    def test_flags_mismatched_sized_literal(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [7:0] x;
              always @(*) begin
                x = 4'hF;
              end
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_matching_widths(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              wire [7:0] y;
              assign x = y;
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )

        assert diagnostics == []

    def test_does_not_flag_unsized_literal_rhs(self) -> None:
        """An unsized literal has no recoverable width -- NO_UNSIZED_LITERAL's
        concern, not this rule's; must not double-report."""
        diagnostics = _diagnostics(
            """
            module top;
              reg [7:0] x;
              always @(*) begin
                x = 5;
              end
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )

        assert diagnostics == []

    def test_does_not_flag_for_loop_header(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [3:0] i;
              reg x;
              always @(*) begin
                for (i = 0; i < 4; i = i + 1) begin
                  x = 1'b1;
                end
              end
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )

        assert diagnostics == []


class TestNoAssignmentSignednessMismatchRule:
    @pytest.fixture
    def rule(self) -> NoAssignmentSignednessMismatchRule:
        return NoAssignmentSignednessMismatchRule()

    def test_rule_has_correct_code(self, rule: NoAssignmentSignednessMismatchRule) -> None:
        assert rule.code == "ASSIGNMENT_SIGNEDNESS_MISMATCH"

    def test_flags_signed_target_assigned_unsigned_identifier(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire signed [7:0] x;
              wire [7:0] y;
              assign x = y;
            endmodule
            """,
            "ASSIGNMENT_SIGNEDNESS_MISMATCH",
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_matching_signedness(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire signed [7:0] x;
              wire signed [7:0] y;
              assign x = y;
            endmodule
            """,
            "ASSIGNMENT_SIGNEDNESS_MISMATCH",
        )

        assert diagnostics == []
