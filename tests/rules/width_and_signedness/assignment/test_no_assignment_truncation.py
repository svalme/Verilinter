"""ASSIGNMENT_TRUNCATION."""
import pytest
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.width_and_signedness.no_assignment_width_mismatch import NoAssignmentTruncationRule
from tests.support.assignment_width_helpers import _diagnostics


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

    def test_does_not_flag_matching_unpacked_array_element_assignment(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [7:0] mem [0:255];
              genvar i;
              assign mem[i] = 8'h55;
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )
        assert diagnostics == []

    def test_flags_mismatched_unpacked_array_element_assignment(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg [7:0] mem [0:255];
              genvar i;
              assign mem[i] = 4'h5;
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )
        assert len(diagnostics) == 1

    def test_does_not_flag_matching_unpacked_array_element_rhs(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              logic [5:0] bitcnt_partial [32];
              logic [5:0] bitcnt_result;
              assign bitcnt_result = bitcnt_partial[31];
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )
        assert diagnostics == []

    def test_flags_mismatched_unpacked_array_element_rhs(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              logic [5:0] bitcnt_partial [32];
              logic [7:0] bitcnt_result;
              assign bitcnt_result = bitcnt_partial[31];
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )
        assert len(diagnostics) == 1

    def test_does_not_flag_multidim_unpacked_array_element_assignment(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              logic [31:0] arr [2][4];
              assign arr[0][1] = 32'd42;
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )
        assert diagnostics == []

    def test_does_not_flag_sliced_element_of_unpacked_array(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              logic [31:0] arr [4];
              assign arr[0][7:0] = 8'hFF;
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )
        assert diagnostics == []

    def test_does_not_flag_scalar_declaration_with_comment_brackets(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              // Pseudocode: shift_amt[4:0] = 32;
              logic shift_left;
              always @(*) begin
                shift_left = 1'b1;
              end
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )
        assert diagnostics == []

    def test_does_not_flag_matching_ansi_unpacked_port_element_assignment(self) -> None:
        diagnostics = _diagnostics(
            """
            module top (
              input logic [31:0] imd_val_q_i [2]
            );
              logic [31:0] unused_val;
              assign unused_val = imd_val_q_i[1];
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )
        assert diagnostics == []

    def test_flags_unpacked_array_narrow_index_select(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              logic [31:0] array [5];
              bit [1:0] rd_addr;
              wire [31:0] rd_value = array[rd_addr];
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )
        assert len(diagnostics) == 1

    def test_does_not_flag_unpacked_array_correct_index_width(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              logic [31:0] array [5];
              bit [1:0] rd_addr;
              wire [31:0] rd_value = array[{1'b0, rd_addr}];
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )
        assert diagnostics == []

    def test_flags_unpacked_array_narrow_index_select_on_lhs(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              logic [31:0] array [5];
              bit [1:0] wr_addr;
              always_comb begin
                array[wr_addr] = 32'h0;
              end
            endmodule
            """,
            "ASSIGNMENT_WIDTH_MISMATCH",
        )
        assert len(diagnostics) == 1
