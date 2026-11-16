"""Regression tests for nested scope lookup and shift expression width inference."""
from tests.support.lint_harness import run_inline_lint_case


def test_assignment_width_mismatch_inside_for_loop():
    code = """
    module top;
        reg [3:0] target;
        reg [7:0] wide_val;
        initial begin
            for (int i = 0; i < 10; i++) begin
                target = wide_val;
            end
        end
    endmodule
    """
    res = run_inline_lint_case({"top.sv": code})
    codes = [d["code"] for d in res.diagnostics]
    assert "ASSIGNMENT_TRUNCATION" in codes
    assert "ASSIGNMENT_WIDTH_MISMATCH" in codes


def test_assignment_width_mismatch_inside_generate_for():
    code = """
    module top;
        reg [3:0] target;
        wire [7:0] wide_val = 8'd10;
        for (genvar g = 0; g < 2; g++) begin : gen_loop
            initial begin
                target = wide_val;
            end
        end
    endmodule
    """
    res = run_inline_lint_case({"top.sv": code})
    codes = [d["code"] for d in res.diagnostics]
    assert "ASSIGNMENT_TRUNCATION" in codes
    assert "ASSIGNMENT_WIDTH_MISMATCH" in codes


def test_shift_expression_truncation():
    code = """
    module top (
        input wire [3:0] in4,
        output wire [2:0] out3
    );
        assign out3 = in4 << 1;
    endmodule
    """
    res = run_inline_lint_case({"top.sv": code})
    codes = [d["code"] for d in res.diagnostics]
    assert "ASSIGNMENT_TRUNCATION" in codes
    assert "ASSIGNMENT_WIDTH_MISMATCH" in codes


def test_shift_expression_expansion():
    code = """
    module top (
        input wire [3:0] in4,
        output wire [4:0] out5
    );
        assign out5 = in4 << 1;
    endmodule
    """
    res = run_inline_lint_case({"top.sv": code})
    codes = [d["code"] for d in res.diagnostics]
    assert "ASSIGNMENT_TRUNCATION" not in codes
    assert "ASSIGNMENT_WIDTH_MISMATCH" not in codes


def test_shift_left_into_wider_target_with_single_bit_and_wide_slice_operands_is_not_a_mismatch():
    code = """
    module top (
        input wire [31:0] r,
        input wire b,
        input wire [2:0] n,
        output wire [31:0] o1,
        output wire [3:0] o2,
        output wire [7:0] o3
    );
        assign o1 = r[31:12] << 12;
        assign o2 = b << n;
        assign o3 = 1'b1 << n;
    endmodule
    """
    res = run_inline_lint_case({"top.sv": code})
    res.expect_no_code("ASSIGNMENT_WIDTH_MISMATCH")


def test_shift_left_wider_than_the_target_is_still_reported():
    code = """
    module top (input wire [7:0] r, output wire [3:0] o);
        assign o = r << 1;
    endmodule
    """
    res = run_inline_lint_case({"top.sv": code})
    codes = [d["code"] for d in res.diagnostics]
    assert "ASSIGNMENT_WIDTH_MISMATCH" in codes
    assert "ASSIGNMENT_TRUNCATION" in codes


def test_conditional_narrower_than_the_target_is_still_a_mismatch():
    code = """
    module top (input wire s, input wire [3:0] a, b, output wire [7:0] o);
        assign o = s ? a : b;
    endmodule
    """
    res = run_inline_lint_case({"top.sv": code})
    res.expect_code_once("ASSIGNMENT_WIDTH_MISMATCH")


def test_shift_expression_exact_match():
    code = """
    module top (
        input wire [3:0] in4,
        output wire [3:0] out4
    );
        assign out4 = in4 << 1;
    endmodule
    """
    res = run_inline_lint_case({"top.sv": code})
    codes = [d["code"] for d in res.diagnostics]
    assert "ASSIGNMENT_TRUNCATION" not in codes
    assert "ASSIGNMENT_WIDTH_MISMATCH" not in codes


def test_arithmetic_truncation_inside_loop():
    code = """
    module top;
        reg [3:0] target;
        reg [3:0] a;
        reg [3:0] b;
        initial begin
            for (int i = 0; i < 4; i++) begin
                target = a * b;
            end
        end
    endmodule
    """
    res = run_inline_lint_case({"top.sv": code})
    codes = [d["code"] for d in res.diagnostics]
    assert "ARITHMETIC_RESULT_TRUNCATION" in codes


def test_constant_index_out_of_range_inside_loop():
    code = """
    module top;
        reg [3:0] arr;
        reg out;
        initial begin
            for (int i = 0; i < 2; i++) begin
                out = arr[5];
            end
        end
    endmodule
    """
    res = run_inline_lint_case({"top.sv": code})
    codes = [d["code"] for d in res.diagnostics]
    assert "CONSTANT_INDEX_OUT_OF_RANGE" in codes


def test_whole_unpacked_array_and_array_element_assignments_are_not_width_mismatches():
    code = """
    module top (
        output logic [31:0] o [10],
        output logic [31:0] o2 [10],
        input logic [31:0] i [10],
        input logic [31:0] st [2][10]
    );
        assign o = i;
        assign o2 = st[1];
    endmodule
    """
    res = run_inline_lint_case({"top.sv": code})
    res.expect_no_code("ASSIGNMENT_WIDTH_MISMATCH")
    res.expect_no_code("ASSIGNMENT_TRUNCATION")


def test_array_element_wider_than_the_target_is_still_truncation():
    code = """
    module top (output logic [7:0] x, input logic [15:0] one [4]);
        assign x = one[1];
    endmodule
    """
    res = run_inline_lint_case({"top.sv": code})
    res.expect_code_once("ASSIGNMENT_TRUNCATION")


def test_unpacked_array_port_connection_compares_whole_widths():
    code = """
    module child (output logic [33:0] d [2], input logic [33:0] q [2]);
    endmodule
    module top;
        logic [33:0] d [2];
        logic [33:0] q [2];
        child u1 (.d(d), .q);
    endmodule
    """
    res = run_inline_lint_case({"top.sv": code})
    res.expect_no_code("PORT_CONNECTION_WIDTH_MISMATCH")

