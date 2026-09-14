"""Regression tests for cast expressions: literal, parameter-width, and typedef cast shapes."""
import pytest
from tests.support.lint_harness import run_inline_lint_case


def test_literal_width_cast_does_not_flag_implicit_net():
    result = run_inline_lint_case({
        "top.sv": """
        module top(output logic [7:0] y_o);
          assign y_o = 8'(1'b0);
        endmodule
        """
    })
    result.expect_no_code("NO_IMPLICIT_NET")


def test_parenthesized_literal_width_cast_does_not_flag_implicit_net():
    result = run_inline_lint_case({
        "top.sv": """
        module top(output logic [15:0] y_o);
          assign y_o = (16)'(1'b1);
        endmodule
        """
    })
    result.expect_no_code("NO_IMPLICIT_NET")


def test_parameter_width_cast_reads_parameter_and_no_implicit_net():
    result = run_inline_lint_case({
        "top.sv": """
        module top #(parameter int WIDTH = 8) (output logic [WIDTH-1:0] y_o);
          assign y_o = (WIDTH)'(1'b0);
        endmodule
        """
    })
    result.expect_no_code("NO_IMPLICIT_NET")
    result.expect_no_code("NO_UNUSED_PARAMETER")


def test_undeclared_cast_prefix_flags_implicit_net():
    result = run_inline_lint_case({
        "top.sv": """
        module top(output logic [7:0] y_o);
          assign y_o = undeclared_width'(1'b0);
        endmodule
        """
    })
    result.expect_code_once("NO_IMPLICIT_NET")
    result.expect_message_contains("NO_IMPLICIT_NET", "undeclared_width")


@pytest.mark.xfail(
    reason="Type-namespace support for typedef cast prefixes (e.g. pmp_cfg_t'(1'b0)) is tracked in ACTION_ITEMS.md #2.3"
)
def test_typedef_cast_prefix_does_not_flag_implicit_net():
    result = run_inline_lint_case({
        "top.sv": """
        module top(output logic [7:0] y_o);
          typedef logic [7:0] my_byte_t;
          assign y_o = my_byte_t'(1'b0);
        endmodule
        """
    })
    result.expect_no_code("NO_IMPLICIT_NET")
