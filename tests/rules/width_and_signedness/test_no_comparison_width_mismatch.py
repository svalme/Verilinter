import pyslang as sl
import pytest

from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.width_and_signedness.no_comparison_width_mismatch import (
    ComparisonWidthMismatchRule,
)
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    assert_no_parse_errors(
        "tests/rules/width_and_signedness/test_no_comparison_width_mismatch.py", tree
    )
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [
        d for d in rule_runner.run(walker.results) if d["code"] == "COMPARISON_WIDTH_MISMATCH"
    ]


class TestComparisonWidthMismatchRule:
    @pytest.fixture
    def rule(self) -> ComparisonWidthMismatchRule:
        return ComparisonWidthMismatchRule()

    def test_rule_metadata(self, rule: ComparisonWidthMismatchRule) -> None:
        assert rule.code == "COMPARISON_WIDTH_MISMATCH"
        assert rule.category == "rtl_correctness"

    def test_sized_literal_matching_width(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [3:0] a;
              wire res;
              assign res = (a == 4'd5);
            endmodule
            """
        )
        assert len(diagnostics) == 0

    def test_sized_literal_mismatched_width(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [3:0] a;
              wire res;
              assign res = (a == 5'd5);
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_signal_to_signal_matching_width(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [3:0] a;
              wire [3:0] b;
              wire res;
              assign res = (a == b);
            endmodule
            """
        )
        assert len(diagnostics) == 0

    def test_signal_to_signal_mismatched_width(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [3:0] a;
              wire [4:0] b;
              wire res;
              assign res = (a == b);
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_relational_operators(self) -> None:
        for op in ("<", "<=", ">", ">=", "!="):
            diagnostics = _diagnostics(
                f"""
                module top;
                  wire [3:0] a;
                  wire [4:0] b;
                  wire res;
                  assign res = (a {op} b);
                endmodule
                """
            )
            assert len(diagnostics) == 1, f"Failed for operator {op}"

    def test_case_and_wildcard_equality_operators(self) -> None:
        for op in ("===", "!==", "==?", "!=?"):
            diagnostics = _diagnostics(
                f"""
                module top;
                  wire [3:0] a;
                  wire [4:0] b;
                  wire res;
                  assign res = (a {op} b);
                endmodule
                """
            )
            assert len(diagnostics) == 1, f"Failed for operator {op}"

    def test_in_range_unsized_literal_not_flagged(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [3:0] a;
              wire res1, res2;
              assign res1 = (a == 0);
              assign res2 = (a == 15);
            endmodule
            """
        )
        assert len(diagnostics) == 0

    def test_out_of_range_unsized_literal_flagged(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [3:0] a;
              wire res;
              assign res = (a == 16);
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_negative_literal_against_unsigned_operand_flagged(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [3:0] a;
              wire res;
              assign res = (a == -1);
            endmodule
            """
        )
        assert len(diagnostics) == 1

    def test_signed_operand_in_range_not_flagged(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire signed [3:0] a;
              wire res1, res2, res3;
              assign res1 = (a == -8);
              assign res2 = (a == -1);
              assign res3 = (a == 7);
            endmodule
            """
        )
        assert len(diagnostics) == 0

    def test_signed_operand_out_of_range_flagged(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire signed [3:0] a;
              wire res1, res2;
              assign res1 = (a == -9);
              assign res2 = (a == 8);
            endmodule
            """
        )
        assert len(diagnostics) == 2

    def test_int_keyword_matching_width(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              int a;
              wire signed [31:0] b;
              wire res;
              assign res = (a == b);
            endmodule
            """
        )
        assert len(diagnostics) == 0

    def test_slice_matching_and_mismatching(self) -> None:
        diagnostics_match = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [3:0] b;
              wire res;
              assign res = (a[3:0] == b);
            endmodule
            """
        )
        assert len(diagnostics_match) == 0

        diagnostics_mismatch = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [3:0] b;
              wire res;
              assign res = (a[4:0] == b);
            endmodule
            """
        )
        assert len(diagnostics_mismatch) == 1

    def test_concatenation_operand(self) -> None:
        diagnostics_match = _diagnostics(
            """
            module top;
              wire [1:0] a, b;
              wire [3:0] c;
              wire res;
              assign res = ({a, b} == c);
            endmodule
            """
        )
        assert len(diagnostics_match) == 0

        diagnostics_mismatch = _diagnostics(
            """
            module top;
              wire [1:0] a, b;
              wire [4:0] c;
              wire res;
              assign res = ({a, b} == c);
            endmodule
            """
        )
        assert len(diagnostics_mismatch) == 1

    def test_literal_on_lhs(self) -> None:
        diagnostics_sized = _diagnostics(
            """
            module top;
              wire [3:0] a;
              wire res;
              assign res = (5'd0 == a);
            endmodule
            """
        )
        assert len(diagnostics_sized) == 1

        diagnostics_out_of_range = _diagnostics(
            """
            module top;
              wire [3:0] a;
              wire res;
              assign res = (16 == a);
            endmodule
            """
        )
        assert len(diagnostics_out_of_range) == 1

        diagnostics_in_range = _diagnostics(
            """
            module top;
              wire [3:0] a;
              wire res;
              assign res = (0 == a);
            endmodule
            """
        )
        assert len(diagnostics_in_range) == 0
