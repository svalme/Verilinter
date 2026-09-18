"""Boundary and unsupported-shape coverage for the three module-level rules in
`port_connection_width_mismatch.py` (`PORT_CONNECTION_WIDTH_MISMATCH`,
`PORT_CONNECTION_WIDTH_UNKNOWN`, `PORT_CONNECTION_SIGNEDNESS_MISMATCH`).
Complements `tests/rules/test_connection_rules.py`'s "any diagnostic with this
code" checks against large multi-rule fixtures: this file probes each rule's
own `connection_analysis.py` logic directly, using the same
`simple_expression_width_and_signed` resolver as `ASSIGNMENT_WIDTH_MISMATCH`
(see `test_no_assignment_width_mismatch.py`), applied here to port-connection
expressions instead of assignment RHS expressions.
"""

from __future__ import annotations

from collections.abc import Callable

from ...support.lint_harness import LintCaseResult


class TestPortConnectionWidthMismatchRule:
    def test_flags_ordered_connection_narrower_than_port(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [3:0] a);
                endmodule
                module top;
                  wire [7:0] x;
                  child u1(x);
                endmodule
                """
            }
        )

        result.expect_code_once("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_does_not_flag_exact_width_match(
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

        result.expect_no_code("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_flags_named_connection_narrower_than_port(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [3:0] a, input [3:0] b);
                endmodule
                module top;
                  wire [3:0] x;
                  wire [7:0] y;
                  child u1(.a(x), .b(y));
                endmodule
                """
            }
        )

        result.expect_code_once("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_flags_bit_select_connection_narrower_than_port(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [3:0] a);
                endmodule
                module top;
                  wire [7:0] x;
                  child u1(.a(x[2]));
                endmodule
                """
            }
        )

        result.expect_code_once("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_does_not_flag_bit_select_connection_matching_single_bit_port(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        # Boundary: a bit-select is always exactly 1 bit wide.
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input a);
                endmodule
                module top;
                  wire [7:0] x;
                  child u1(.a(x[2]));
                endmodule
                """
            }
        )

        result.expect_no_code("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_flags_part_select_connection_narrower_than_port(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [7:0] a);
                endmodule
                module top;
                  wire [7:0] x;
                  child u1(.a(x[3:0]));
                endmodule
                """
            }
        )

        result.expect_code_once("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_does_not_flag_part_select_connection_matching_width(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        # Boundary: the part-select's width exactly equals the port's.
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [3:0] a);
                endmodule
                module top;
                  wire [7:0] x;
                  child u1(.a(x[3:0]));
                endmodule
                """
            }
        )

        result.expect_no_code("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_flags_sized_literal_connection_mismatched_width(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [3:0] a);
                endmodule
                module top;
                  child u1(.a(8'hFF));
                endmodule
                """
            }
        )

        result.expect_code_once("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_does_not_flag_sized_literal_connection_matching_width(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [3:0] a);
                endmodule
                module top;
                  child u1(.a(4'hF));
                endmodule
                """
            }
        )

        result.expect_no_code("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_flags_mismatch_on_an_output_port_connection(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        # Direction plays no role in `width_mismatch_details` -- confirms the
        # rule checks every bound port, not only inputs.
        result = lint_inline_case(
            {
                "top.sv": """
                module child(output [7:0] y);
                endmodule
                module top;
                  wire [3:0] x;
                  child u1(.y(x));
                endmodule
                """
            }
        )

        result.expect_code_once("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_does_not_flag_concatenation_connection_matching_width(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [7:0] a);
                endmodule
                module top;
                  wire [3:0] p, q;
                  child u1(.a({p, q}));
                endmodule
                """
            }
        )

        result.expect_no_code("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_does_not_flag_an_unconnected_ordered_port(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        # `bound_port_pairs` yields `conn is None` for a trailing ordered port
        # with no connection at all; `width_mismatch_details` skips it outright.
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [3:0] a, input [3:0] b);
                endmodule
                module top;
                  wire [3:0] x;
                  child u1(x);
                endmodule
                """
            }
        )

        result.expect_no_code("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_named_parameter_override_matches_instance_width(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child #(parameter WIDTH = 64) (input [WIDTH-1:0] in);
                endmodule
                module top;
                  wire [3:0] sig4;
                  child #(.WIDTH(4)) u1(.in(sig4));
                endmodule
                """
            }
        )
        result.expect_no_code("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_named_parameter_override_flags_width_mismatch(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child #(parameter WIDTH = 64) (input [WIDTH-1:0] in);
                endmodule
                module top;
                  wire [7:0] sig8;
                  child #(.WIDTH(4)) u1(.in(sig8));
                endmodule
                """
            }
        )
        result.expect_code_once("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_ordered_parameter_override_matches_instance_width(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child #(parameter WIDTH = 64) (input [WIDTH-1:0] in);
                endmodule
                module top;
                  wire [3:0] sig4;
                  child #(4) u1(.in(sig4));
                endmodule
                """
            }
        )
        result.expect_no_code("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_ordered_parameter_override_flags_width_mismatch(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child #(parameter WIDTH = 64) (input [WIDTH-1:0] in);
                endmodule
                module top;
                  wire [7:0] sig8;
                  child #(4) u1(.in(sig8));
                endmodule
                """
            }
        )
        result.expect_code_once("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_dependent_parameter_recalculation(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child #(parameter WIDTH = 8) (input [TOTAL-1:0] in);
                  localparam TOTAL = WIDTH + 4;
                endmodule
                module top;
                  wire [19:0] sig20;
                  wire [11:0] sig12;
                  child #(.WIDTH(16)) u1(.in(sig20));
                  child #(.WIDTH(16)) u2(.in(sig12));
                endmodule
                """
            }
        )
        # u1 matches 16 + 4 = 20 bits; u2 has 12 bits connected to 20-bit port (mismatch)
        result.expect_code_once("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_parent_parameter_passed_to_override(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child #(parameter WIDTH = 8) (input [WIDTH-1:0] in);
                endmodule
                module top #(parameter TOP_W = 16) ();
                  wire [15:0] bus16;
                  child #(.WIDTH(TOP_W)) u1(.in(bus16));
                endmodule
                """
            }
        )
        result.expect_no_code("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_cross_file_parameter_override_propagation(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "child.sv": """
                module child #(parameter WIDTH = 64) (input [WIDTH-1:0] in);
                endmodule
                """,
                "top.sv": """
                module top;
                  wire [3:0] sig4;
                  wire [7:0] sig8;
                  child #(.WIDTH(4)) u1(.in(sig4));
                  child #(.WIDTH(4)) u2(.in(sig8));
                endmodule
                """,
            }
        )
        result.expect_code_once("PORT_CONNECTION_WIDTH_MISMATCH")


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

    def test_flags_arithmetic_expression_connection(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        # `simple_expression_width_and_signed` only resolves an identifier, a
        # literal, a select, or a concatenation/replication of those -- an
        # arithmetic connection expression like `p + q` isn't recognized at
        # all. Unlike `ASSIGNMENT_WIDTH_MISMATCH` (which silently produces no
        # diagnostic for the same unresolvable shape), this surfaces the gap
        # explicitly as an unknown-width connection rather than staying silent.
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

        result.expect_code_once("PORT_CONNECTION_WIDTH_UNKNOWN")

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


class TestPortConnectionSignednessMismatchRule:
    def test_flags_signed_port_connected_to_unsigned_identifier(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input signed [3:0] a);
                endmodule
                module top;
                  wire [3:0] x;
                  child u1(.a(x));
                endmodule
                """
            }
        )

        result.expect_code_once("PORT_CONNECTION_SIGNEDNESS_MISMATCH")

    def test_flags_unsigned_port_connected_to_signed_literal(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        # Reverse direction of test_flags_signed_port_connected_to_unsigned_identifier,
        # and via a signed literal (`'s`) rather than a signed identifier.
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input [3:0] a);
                endmodule
                module top;
                  child u1(.a(4'sb0101));
                endmodule
                """
            }
        )

        result.expect_code_once("PORT_CONNECTION_SIGNEDNESS_MISMATCH")

    def test_does_not_flag_matching_signedness(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input signed [3:0] a);
                endmodule
                module top;
                  wire signed [3:0] x;
                  child u1(.a(x));
                endmodule
                """
            }
        )

        result.expect_no_code("PORT_CONNECTION_SIGNEDNESS_MISMATCH")

    def test_does_not_flag_bit_select_connection_to_a_signed_port(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        # Documents a known limitation: a bit-select always resolves to
        # `(1, None)` in `simple_expression_width_and_signed` -- the unknown
        # signedness means this rule's `expr_signed is None` guard skips the
        # connection entirely, even connected to a signed port from an
        # otherwise-unsigned source.
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input signed a);
                endmodule
                module top;
                  wire [7:0] x;
                  child u1(.a(x[2]));
                endmodule
                """
            }
        )

        result.expect_no_code("PORT_CONNECTION_SIGNEDNESS_MISMATCH")

    def test_does_not_flag_when_connection_signedness_is_unresolvable(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        # An undeclared identifier resolves to `(None, None)`: this rule's
        # `expr_signed is None` guard skips it silently (no match, no
        # mismatch), distinct from `PORT_CONNECTION_WIDTH_UNKNOWN`, which does
        # fire for the same connection since it only requires the width half
        # to be unresolved.
        result = lint_inline_case(
            {
                "top.sv": """
                module child(input signed [3:0] a);
                endmodule
                module top;
                  child u1(.a(undeclared_sig));
                endmodule
                """
            }
        )

        result.expect_no_code("PORT_CONNECTION_SIGNEDNESS_MISMATCH")
