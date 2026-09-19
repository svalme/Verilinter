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
    NoAssignmentTruncationRule,
)


from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str, rule_code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    assert_no_parse_errors("tests/rules/width_and_signedness/test_no_assignment_width_mismatch.py", tree)
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

    def test_flags_concatenation_with_unsized_literal_member(self) -> None:
        """IEEE 1800 sizes an unsized literal used as a concatenation member
        to exactly 32 bits, not the context-determined width a top-level
        unsized RHS gets -- without that override, this member's unrecoverable
        width would make the *entire* concatenation's width unrecoverable,
        silencing the check instead of reporting the enormous mismatch."""
        diagnostics = _diagnostics(
            """
            module top;
              wire [3:0] a;
              wire [7:0] x;
              assign x = {a, 5};
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )

        assert len(diagnostics) == 1

    def test_flags_replication_of_unsized_literal(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              assign x = {4{1}};
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_concatenation_with_matching_total_width(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [3:0] a;
              wire [3:0] b;
              wire [7:0] x;
              assign x = {a, b};
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )

        assert diagnostics == []

    def test_flags_bit_select_rhs_narrower_than_target(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [3:0] x;
              assign x = a[2];
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_bit_select_rhs_matching_single_bit_target(self) -> None:
        # Boundary: a bit-select is always exactly 1 bit wide.
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire x;
              assign x = a[2];
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )

        assert diagnostics == []

    def test_flags_part_select_rhs_narrower_than_target(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [7:0] x;
              assign x = a[3:0];
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_part_select_rhs_matching_width(self) -> None:
        # Boundary: the part-select's width exactly equals the target's.
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [3:0] x;
              assign x = a[3:0];
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )

        assert diagnostics == []

    def test_flags_mismatch_in_nonblocking_assignment(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk);
              reg [7:0] x;
              reg [3:0] y;
              always @(posedge clk) begin
                x <= y;
              end
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_mismatch_hidden_behind_arithmetic_expression(self) -> None:
        # Documents a known limitation, not a claim of coverage:
        # `simple_expression_width_and_signed` only resolves an identifier,
        # a literal, a select, or a concatenation/replication of those -- an
        # arithmetic RHS like `a + b` isn't recognized at all, so its width
        # is unrecoverable and the real mismatch below (8-bit sum into a
        # 4-bit target) goes silently undetected.
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [7:0] b;
              wire [3:0] x;
              assign x = a + b;
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )

        assert diagnostics == []

    def test_flags_declarator_initializer_width_mismatch(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [3:0] a;
              wire [7:0] b = a;
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )

        assert len(diagnostics) == 1

    def test_parameter_declarator_initializer_not_flagged(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              localparam [7:0] A = 4'h5;
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

    def test_flags_unsigned_target_assigned_signed_identifier(self) -> None:
        # Reverse direction of test_flags_signed_target_assigned_unsigned_identifier.
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              wire signed [7:0] y;
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

    def test_flags_declarator_initializer_signedness_mismatch(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire signed [7:0] b = a;
            endmodule
            """,
            "ASSIGNMENT_SIGNEDNESS_MISMATCH",
        )

        assert len(diagnostics) == 1



class TestNoAssignmentTruncationRule:
    @pytest.fixture
    def rule(self) -> NoAssignmentTruncationRule:
        return NoAssignmentTruncationRule()

    def test_rule_has_correct_code(self, rule: NoAssignmentTruncationRule) -> None:
        assert rule.code == "ASSIGNMENT_TRUNCATION"

    def test_flags_wider_rhs_truncated_into_narrower_target(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              wire [3:0] y;
              assign y = x;
            endmodule
            """,
            "ASSIGNMENT_TRUNCATION",
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_narrower_rhs_into_wider_target(self) -> None:
        # Safe zero/sign-extending direction -- ASSIGNMENT_WIDTH_MISMATCH's
        # concern (any-direction), not this rule's (truncation-only).
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              wire [3:0] y;
              assign x = y;
            endmodule
            """,
            "ASSIGNMENT_TRUNCATION",
        )

        assert diagnostics == []

    def test_does_not_flag_matching_widths(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] x;
              wire [7:0] y;
              assign x = y;
            endmodule
            """,
            "ASSIGNMENT_TRUNCATION",
        )

        assert diagnostics == []

    def test_flags_declarator_initializer_truncation(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [3:0] b = a;
            endmodule
            """,
            "ASSIGNMENT_TRUNCATION",
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_matching_declarator_initializer(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [7:0] b = a;
            endmodule
            """,
            "ASSIGNMENT_TRUNCATION",
        )

        assert diagnostics == []

    def test_flags_parameterized_width_mismatch(self) -> None:
        diagnostics = _diagnostics(
            """
            module top #(parameter WIDTH = 8);
              wire [WIDTH-1:0] x;
              wire [3:0] y;
              assign x = y;
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )
        assert len(diagnostics) == 1

    def test_flags_parameterized_assignment_truncation(self) -> None:
        diagnostics = _diagnostics(
            """
            module top #(parameter WIDTH = 4);
              wire [WIDTH-1:0] x;
              wire [7:0] y;
              assign x = y;
            endmodule
            """,
            "ASSIGNMENT_TRUNCATION",
        )
        assert len(diagnostics) == 1

    def test_does_not_flag_matching_parameterized_width(self) -> None:
        diagnostics = _diagnostics(
            """
            module top #(parameter WIDTH = 8);
              wire [WIDTH-1:0] x;
              wire [7:0] y;
              assign x = y;
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )
        assert diagnostics == []

    def test_does_not_flag_matching_multidim_array_element_assignment(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              logic [7:0][2:0] sel_n;
              logic [31:0] op;
              genvar i;
              assign sel_n[i] = op[i*4 +: 3];
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )
        assert diagnostics == []

    def test_flags_multidim_array_element_assignment_width_mismatch(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              logic [7:0][2:0] sel_n;
              genvar i;
              assign sel_n[i] = 2'b10;
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )
        assert len(diagnostics) == 1

    def test_flags_multidim_array_element_assignment_truncation(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              logic [7:0][2:0] sel_n;
              genvar i;
              assign sel_n[i] = 4'b1010;
            endmodule
            """,
            "ASSIGNMENT_TRUNCATION",
        )
        assert len(diagnostics) == 1

    def test_does_not_flag_matching_multidim_array_element_rhs(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              logic [7:0][2:0] sel_n;
              logic [2:0] out;
              genvar i;
              assign out = sel_n[i];
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )
        assert diagnostics == []

    def test_does_not_flag_matching_part_select_target(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              logic [31:0] data;
              assign data[15:0] = 16'h1234;
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )
        assert diagnostics == []

    def test_flags_part_select_target_width_mismatch(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              logic [31:0] data;
              assign data[15:0] = 8'h12;
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )
        assert len(diagnostics) == 1

    def test_does_not_flag_scalar_element_select_from_multidim_array(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              logic [7:0][2:0] sel_n;
              genvar i, j;
              assign sel_n[i][j] = 1'b0;
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )
        assert diagnostics == []


