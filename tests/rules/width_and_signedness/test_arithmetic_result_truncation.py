import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.width_and_signedness.arithmetic_result_truncation import ArithmeticResultTruncationRule


from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    assert_no_parse_errors("tests/rules/width_and_signedness/test_arithmetic_result_truncation.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "ARITHMETIC_RESULT_TRUNCATION"]


class TestArithmeticResultTruncationRule:
    @pytest.fixture
    def rule(self) -> ArithmeticResultTruncationRule:
        return ArithmeticResultTruncationRule()

    def test_rule_has_correct_code(self, rule: ArithmeticResultTruncationRule) -> None:
        assert rule.code == "ARITHMETIC_RESULT_TRUNCATION"

    def test_flags_multiply_result_wider_than_target(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [7:0] b;
              wire [7:0] p;
              assign p = a * b;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_add_result_wider_than_target(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [3:0] b;
              wire [3:0] s;
              assign s = a + b;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_multiply_result_that_fits(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [7:0] b;
              wire [15:0] p;
              assign p = a * b;
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_add_result_that_fits(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [7:0] b;
              wire [7:0] s;
              assign s = a + b;
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_when_operand_width_unknown(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [7:0] p;
              assign p = a * (b + c);
            endmodule
            """
        )

        assert diagnostics == []

    def test_flags_subtract_result_wider_than_target(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [3:0] b;
              wire [3:0] s;
              assign s = a - b;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_subtract_result_that_fits(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [7:0] b;
              wire [7:0] s;
              assign s = a - b;
            endmodule
            """
        )

        assert diagnostics == []

    def test_flags_nonblocking_assignment_in_procedural_block(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic clk);
              logic [7:0] a;
              logic [7:0] b;
              logic [7:0] p;
              always_ff @(posedge clk) begin
                p <= a * b;
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_nested_arithmetic_expression(self) -> None:
        # Documents a known limitation, not a claim of coverage: `_natural_
        # result_width` only recognizes a direct `+`/`-`/`*` binary RHS, so
        # nesting one arithmetic operation inside another (here `a * b + c`,
        # whose true 9-bit result still overflows the 8-bit target) makes the
        # inner `a * b` operand's width unrecoverable and silently skips the
        # whole expression rather than guessing at it.
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [7:0] b;
              wire [7:0] c;
              wire [7:0] p;
              assign p = a * b + c;
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_bit_select_assignment_target(self) -> None:
        # Documents a known limitation: the rule only resolves a plain
        # identifier assignment target via `identifier_name`/`ctx.scope().
        # lookup`, so a bit-select or part-select target (`p[7:0] = ...`) is
        # silently skipped even though the same truncation can occur there.
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [7:0] b;
              wire [15:0] p;
              assign p[7:0] = a * b;
            endmodule
            """
        )

        assert diagnostics == []
