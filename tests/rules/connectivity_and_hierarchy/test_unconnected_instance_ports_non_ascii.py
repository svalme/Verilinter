"""A non-ASCII character earlier in a file must not shift the text read for later port connections."""

from __future__ import annotations

from collections.abc import Callable

from ...support.lint_harness import LintCaseResult


class TestNonAsciiSource:
    def test_connected_ports_after_a_non_ascii_comment_are_not_reported(
        self, lint_inline_case: Callable[[dict[str, str]], LintCaseResult]
    ) -> None:
        result = lint_inline_case(
            {
                "top.sv": """
                // Copyright © 2026 — Example Authors “quoted”
                module child(input logic clk_i, input logic en_i, output logic clk_o);
                endmodule
                module top(input logic clk, input logic en, output logic out);
                  child u_child (
                    .clk_i ( clk ),
                    .en_i  ( en ),
                    .clk_o ( out )
                  );
                endmodule
                """
            }
        )

        result.expect_no_code("NO_UNCONNECTED_INSTANCE_PORTS")
