from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.naming_and_style.parameter_name_casing import ParameterNameCasingRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "PARAMETER_NAME_CASING"]


class TestParameterNameCasingRule:
    @pytest.fixture
    def rule(self) -> ParameterNameCasingRule:
        return ParameterNameCasingRule()

    def test_rule_has_correct_code(self, rule: ParameterNameCasingRule) -> None:
        assert rule.code == "PARAMETER_NAME_CASING"

    def test_flags_lower_case_parameter_name(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              parameter width = 8;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_all_caps_parameter_name(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              parameter WIDTH = 8;
            endmodule
            """
        )

        assert diagnostics == []

    def test_flags_lower_case_localparam_name(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              localparam depth = 4;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_ordinary_wire_name(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire my_wire;
            endmodule
            """
        )

        assert diagnostics == []
