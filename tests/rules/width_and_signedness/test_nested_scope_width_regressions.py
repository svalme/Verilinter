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
    assert "ASSIGNMENT_WIDTH_MISMATCH" in codes


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
