import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.width_and_signedness.explicit_xz_literal import ExplicitXZLiteralRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
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
