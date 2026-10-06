from src.pkg.parser.parse import parse_text
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

    tree = parse_text(code)
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

    def test_flags_nested_arithmetic_expression(self) -> None:
        # The nested product needs 16 bits under the full-product policy.
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

        assert len(diagnostics) == 1

    def test_flags_part_select_assignment_target(self) -> None:
        # Compare against the selected target width rather than the base net.
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

        assert len(diagnostics) == 1

    def test_flags_declarator_initializer_truncation(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire [7:0] a;
              wire [7:0] b;
              wire [7:0] p = a * b;
            endmodule
            """
        )

        assert len(diagnostics) == 1

