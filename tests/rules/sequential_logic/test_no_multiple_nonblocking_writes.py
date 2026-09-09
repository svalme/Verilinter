import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.sequential_logic.no_multiple_nonblocking_writes import (
    NoMultipleNonblockingWritesRule,
)

from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    assert_no_parse_errors(
        "tests/rules/sequential_logic/test_no_multiple_nonblocking_writes.py", tree
    )
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "NO_MULTIPLE_NONBLOCKING_WRITES"]


class TestNoMultipleNonblockingWritesRule:
    @pytest.fixture
    def rule(self) -> NoMultipleNonblockingWritesRule:
        return NoMultipleNonblockingWritesRule()

    def test_rule_has_correct_code(self, rule: NoMultipleNonblockingWritesRule) -> None:
        assert rule.code == "NO_MULTIPLE_NONBLOCKING_WRITES"

    def test_flags_unconditional_sibling_writes(self) -> None:
        """The canonical bug: two straight-line writes to the same target in the
        same block -- the second unconditionally overwrites the first, making the
        first dead."""
        diagnostics = _diagnostics(
            """
            module top(input logic clk, input logic a, input logic b, output logic y);
              always_ff @(posedge clk) begin
                y <= a;
                y <= b;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_unconditional_sibling_writes_nested_in_one_branch(self) -> None:
        """Same bug shape, one level deeper: both writes are still direct siblings
        of each other, just inside an `if` body rather than the block's top level."""
        diagnostics = _diagnostics(
            """
            module top(input logic clk, input logic en, input logic a, input logic b, output logic y);
              always_ff @(posedge clk) begin
                if (en) begin
                  y <= a;
                  y <= b;
                end
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_if_else_reset_pattern(self) -> None:
        """The standard `if (reset) ... else
        ...` register idiom writes the same target from two mutually exclusive
        branches -- only one ever executes per cycle, so this must not fire."""
        diagnostics = _diagnostics(
            """
            module top(input logic clk, input logic rst_n, input logic d, output logic q);
              always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n) q <= 1'b0;
                else q <= d;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_else_if_chain(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic clk, input logic rst_n, input logic a, output logic q);
              always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n) q <= 1'b0;
                else if (a) q <= 1'b1;
                else q <= 1'b0;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_default_then_conditional_override(self) -> None:
        """The standard "default assignment" idiom: an unconditional write followed
        by a conditionally *nested* override of the same target. Both can execute
        in the same cycle by design (the override winning is the intended
        behavior), unlike the unconditional-sibling case this rule targets."""
        diagnostics = _diagnostics(
            """
            module top(input logic clk, input logic en, input logic d, output logic q);
              always_ff @(posedge clk) begin
                q <= q;
                if (en) q <= d;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_case_items_writing_same_target(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic clk, input logic [1:0] sel, output logic y);
              always_ff @(posedge clk) begin
                case (sel)
                  2'b00: y <= 1'b0;
                  2'b01: y <= 1'b1;
                  default: y <= 1'b0;
                endcase
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_writes_to_different_targets(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic clk, input logic a, input logic b, output logic x, output logic y);
              always_ff @(posedge clk) begin
                x <= a;
                y <= b;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_report_returns_correct_format(self, rule: NoMultipleNonblockingWritesRule) -> None:
        from unittest.mock import Mock

        from src.pkg.vnodes.base_vnode import BaseVNode

        vnode = Mock(spec=BaseVNode)
        vnode.location = {"line": 6, "col": 5}
        result = rule.report(vnode)

        assert result["line"] == 6
        assert result["col"] == 5
        assert result["message"] == "Multiple non-blocking writes to the same target in one procedural block"
