from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.width_and_signedness.explicit_xz_literal import ExplicitXZLiteralRule


from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/width_and_signedness/test_explicit_xz_literal.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "EXPLICIT_XZ_LITERAL"]


class TestExplicitXZLiteralRule:
    @pytest.fixture
    def rule(self) -> ExplicitXZLiteralRule:
        return ExplicitXZLiteralRule()

    def test_rule_has_correct_code(self, rule: ExplicitXZLiteralRule) -> None:
        assert rule.code == "EXPLICIT_XZ_LITERAL"

    def test_flags_unbased_unsized_x_literal(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(output y);
              assign y = 'x;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_unbased_unsized_z_literal(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(output y);
              assign y = 'z;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_sized_literal_with_xz_bits(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(output [3:0] y);
              assign y = 4'bx01z;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_unbased_unsized_0_literal(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(output y);
              assign y = '0;
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_unbased_unsized_1_literal(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(output y);
              assign y = '1;
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_fully_numeric_sized_literal(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(output [3:0] y);
              assign y = 4'hF;
            endmodule
            """
        )

        assert diagnostics == []

    def test_flags_hex_literal_with_x_digit(self) -> None:
        # Different radix than the already-covered binary `4'bx01z` case --
        # each hex digit stands for 4 bits, so a single `x` digit still
        # counts as an explicit X value.
        diagnostics = _diagnostics(
            """
            module top(output [3:0] y);
              assign y = 4'hx;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_literal_with_question_mark_wildcard_bit(self) -> None:
        # `?` is a legal literal-digit synonym for `z`, and is checked
        # alongside `x`/`z` by `is_explicit_xz_literal`.
        diagnostics = _diagnostics(
            """
            module top(output [3:0] y);
              assign y = 4'b10?1;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_literal_used_as_case_item_not_only_assigned_values(self) -> None:
        # Unlike NO_UNSIZED_LITERAL (which only fires on a literal in direct
        # assignment-RHS position), this rule has no context restriction: any
        # explicit X/Z literal anywhere -- including a case item, not an
        # assigned value -- is flagged.
        diagnostics = _diagnostics(
            """
            module top(input [1:0] a, output reg y);
              always @(*) begin
                case (a)
                  2'bx1: y = 1'b1;
                  default: y = 1'b0;
                endcase
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1
