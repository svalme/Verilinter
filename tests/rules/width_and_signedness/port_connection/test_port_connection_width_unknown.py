"""PORT_CONNECTION_WIDTH_UNKNOWN."""
from collections.abc import Callable
from ....support.lint_harness import LintCaseResult


class TestPortConnectionWidthUnknownRule:
    def test_flags_unsized_literal_connection(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        # An unsized decimal literal resolves to `(None, False)`: its width is
        # context-determined and unrecoverable from the connection expression
        # alone, same limitation as `NO_UNSIZED_LITERAL`'s target audits.
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [3:0] a);
                endmodule
                module top;
                  child u1(.a(5));
                endmodule
                """
            }
        )

        result.expect_code_once("PORT_CONNECTION_WIDTH_UNKNOWN")

    def test_arithmetic_expression_of_known_operands_is_sized(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        # The connected expression is sized by `natural_expression_width_and_signed`,
        # so `p + q` of two 4-bit operands is 4 bits and matches the 4-bit port.
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [3:0] a);
                endmodule
                module top;
                  wire [3:0] p, q;
                  child u1(.a(p + q));
                endmodule
                """
            }
        )

        result.expect_no_code("PORT_CONNECTION_WIDTH_UNKNOWN")

    def test_logical_and_bitwise_connection_of_one_bit_operands_is_sized(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input a, input b);
                endmodule
                module top;
                  wire v, iso;
                  child u1(.a(v & !iso), .b(v && !iso));
                endmodule
                """
            }
        )

        result.expect_no_code("PORT_CONNECTION_WIDTH_UNKNOWN")

    def test_named_empty_connection_is_not_width_unknown(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [3:0] a, output [3:0] y, output z);
                endmodule
                module top;
                  wire [3:0] p;
                  child u1(.a(p), .y(), .z());
                endmodule
                """
            }
        )

        result.expect_no_code("PORT_CONNECTION_WIDTH_UNKNOWN")

    def test_arithmetic_connection_narrower_than_the_port_is_extended(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        # `p + q` is evaluated at the 5-bit port's width, so nothing is lost.
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [4:0] a, input [4:0] b, input [7:0] c);
                endmodule
                module top;
                  wire [3:0] p, q;
                  child u1(.a(p + q), .b(p << 1), .c(p * q));
                endmodule
                """
            }
        )

        result.expect_no_code("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_conditional_and_bitwise_connection_narrower_than_the_port_is_still_a_mismatch(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        # Neither can need more bits than its operands, so this is the same extension a plain signal gets.
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [4:0] a, input [4:0] b);
                endmodule
                module top;
                  wire [3:0] p, q;
                  wire s;
                  child u1(.a(s ? p : q), .b(p | q));
                endmodule
                """
            }
        )

        result.expect_code_count("PORT_CONNECTION_WIDTH_MISMATCH", 2)

    def test_ordered_arithmetic_connection_narrower_than_the_port_is_extended(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [4:0] a);
                endmodule
                module top;
                  wire [3:0] p, q;
                  child u1(p + q);
                endmodule
                """
            }
        )

        result.expect_no_code("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_plain_signal_narrower_than_the_port_is_still_a_mismatch(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [4:0] a);
                endmodule
                module top;
                  wire [3:0] p;
                  child u1(.a(p));
                endmodule
                """
            }
        )

        result.expect_code_once("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_arithmetic_connection_wider_than_the_port_is_still_a_mismatch(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        # The 4 x 4 bit product has 8 bits of capacity; a 4-bit port loses the upper half.
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [3:0] a);
                endmodule
                module top;
                  wire [3:0] p, q;
                  child u1(.a(p * q));
                endmodule
                """
            }
        )

        result.expect_code_once("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_flags_undeclared_identifier_connection(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [3:0] a);
                endmodule
                module top;
                  child u1(.a(undeclared_sig));
                endmodule
                """
            }
        )

        result.expect_code_once("PORT_CONNECTION_WIDTH_UNKNOWN")

    def test_flags_parameterized_port_width_without_default(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        # A parameterized port whose parameter has no default value (and no instance
        # override) has an unresolvable bit width (bit_width is None), so this
        # rule surfaces the gap explicitly as PORT_CONNECTION_WIDTH_UNKNOWN.
        result = lint_inline_case(
            {
                "top.sv": """
                module child #(parameter WIDTH) (input [WIDTH-1:0] a);
                endmodule
                module top;
                  wire [3:0] x;
                  child u1(.a(x));
                endmodule
                """
            }
        )

        result.expect_code_once("PORT_CONNECTION_WIDTH_UNKNOWN")

    def test_resolves_parameterized_port_width_with_default(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        # When a parameter has a default value, constant folding resolves the
        # port width (WIDTH = 4 -> [3:0] -> 4 bits), matching wire [3:0] x without
        # raising PORT_CONNECTION_WIDTH_UNKNOWN.
        result = lint_inline_case(
            {
                "top.sv": """
                module child #(parameter WIDTH = 4) (input [WIDTH-1:0] a);
                endmodule
                module top;
                  wire [3:0] x;
                  child u1(.a(x));
                endmodule
                """
            }
        )

        assert "PORT_CONNECTION_WIDTH_UNKNOWN" not in [d["code"] for d in result.diagnostics]

    def test_does_not_flag_an_unconnected_ordered_port(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        # Documents an asymmetry: an ordered/positional gap (`u1(x, , z)`)
        # produces an "empty" connection that this rule explicitly excludes,
        # while the equivalent named form (`.b()`, see the class below) does
        # not carry that exclusion and fires instead.
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [3:0] a, input [3:0] b, input [3:0] c);
                endmodule
                module top;
                  wire [3:0] x, z;
                  child u1(x, , z);
                endmodule
                """
            }
        )

        result.expect_no_code("PORT_CONNECTION_WIDTH_UNKNOWN")

    def test_does_not_flag_when_both_widths_are_known_and_match(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [3:0] a);
                endmodule
                module top;
                  wire [3:0] x;
                  child u1(.a(x));
                endmodule
                """
            }
        )

        result.expect_no_code("PORT_CONNECTION_WIDTH_UNKNOWN")


class TestPortConnectionWidthUnknownForTypeParameters:
    def test_port_typed_by_a_type_parameter_is_not_reported_as_unknown_width(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child #(parameter type data_t = logic) (input data_t a_i);
                endmodule
                module top (input logic [7:0] x_i);
                  child u_child (.a_i(x_i));
                endmodule
                """
            }
        )

        result.expect_no_code("PORT_CONNECTION_WIDTH_UNKNOWN")

    def test_port_with_an_unresolved_parameter_width_is_still_reported(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child #(parameter WIDTH) (input [WIDTH-1:0] d_i);
                endmodule
                module top;
                  logic [7:0] b;
                  child u_child (.d_i(b));
                endmodule
                """
            }
        )

        result.expect_code_once("PORT_CONNECTION_WIDTH_UNKNOWN")
