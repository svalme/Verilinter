from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.syntax_and_structure.one_module_per_file import OneModulePerFileRule


from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/syntax_and_structure/test_one_module_per_file.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "ONE_MODULE_PER_FILE"]


class TestOneModulePerFileRule:
    @pytest.fixture
    def rule(self) -> OneModulePerFileRule:
        return OneModulePerFileRule()

    def test_rule_has_correct_code(self, rule: OneModulePerFileRule) -> None:
        assert rule.code == "ONE_MODULE_PER_FILE"

    def test_does_not_flag_single_module(self) -> None:
        diagnostics = _diagnostics("module top; endmodule")

        assert diagnostics == []

    def test_flags_second_module_when_two_modules_in_one_file(self) -> None:
        diagnostics = _diagnostics("module a; endmodule\nmodule b; endmodule")

        assert len(diagnostics) == 1

    def test_flags_every_module_after_the_first(self) -> None:
        diagnostics = _diagnostics("module a; endmodule\nmodule b; endmodule\nmodule c; endmodule")

        assert len(diagnostics) == 2

    def test_does_not_flag_first_module_alongside_a_package(self) -> None:
        diagnostics = _diagnostics("package p; endpackage\nmodule top; endmodule")

        assert diagnostics == []
