import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.naming_and_style.module_name_casing import ModuleNameCasingRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "MODULE_NAME_CASING"]


class TestModuleNameCasingRule:
    @pytest.fixture
    def rule(self) -> ModuleNameCasingRule:
        return ModuleNameCasingRule()

    def test_rule_has_correct_code(self, rule: ModuleNameCasingRule) -> None:
        assert rule.code == "MODULE_NAME_CASING"

    def test_flags_camel_case_module_name(self) -> None:
        diagnostics = _diagnostics(
            """
            module MyModule;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_upper_case_module_name(self) -> None:
        diagnostics = _diagnostics(
            """
            module TOP;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_lower_snake_case_module_name(self) -> None:
        diagnostics = _diagnostics(
            """
            module my_module;
            endmodule
            """
        )

        assert diagnostics == []
