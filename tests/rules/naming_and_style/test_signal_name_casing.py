import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.naming_and_style.signal_name_casing import SignalNameCasingRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "SIGNAL_NAME_CASING"]


class TestSignalNameCasingRule:
    @pytest.fixture
    def rule(self) -> SignalNameCasingRule:
        return SignalNameCasingRule()

    def test_rule_has_correct_code(self, rule: SignalNameCasingRule) -> None:
        assert rule.code == "SIGNAL_NAME_CASING"

    def test_flags_camel_case_wire_name(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire myWire;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_lower_snake_case_wire_name(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire my_wire;
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_parameter_declaration(self) -> None:
        # Parameters have their own convention -- PARAMETER_NAME_CASING's concern.
        diagnostics = _diagnostics(
            """
            module top;
              parameter myParam = 1;
            endmodule
            """
        )

        assert diagnostics == []
