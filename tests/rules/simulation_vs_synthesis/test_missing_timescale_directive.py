from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.simulation_vs_synthesis.missing_timescale_directive import MissingTimescaleDirectiveRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "MISSING_TIMESCALE_DIRECTIVE"]


class TestMissingTimescaleDirectiveRule:
    @pytest.fixture
    def rule(self) -> MissingTimescaleDirectiveRule:
        return MissingTimescaleDirectiveRule()

    def test_rule_has_correct_code(self, rule: MissingTimescaleDirectiveRule) -> None:
        assert rule.code == "MISSING_TIMESCALE_DIRECTIVE"

    def test_flags_module_with_no_timescale(self) -> None:
        diagnostics = _diagnostics("module top; endmodule")

        assert len(diagnostics) == 1

    def test_does_not_flag_module_with_timescale(self) -> None:
        diagnostics = _diagnostics("`timescale 1ns/1ps\nmodule top; endmodule")

        assert diagnostics == []

    def test_does_not_flag_when_timescale_follows_a_leading_comment(self) -> None:
        diagnostics = _diagnostics("// header comment\n`timescale 1ns/1ps\nmodule top; endmodule")

        assert diagnostics == []

    def test_flags_only_first_module_when_multiple_modules_have_no_timescale(self) -> None:
        diagnostics = _diagnostics("module a; endmodule\nmodule b; endmodule")

        assert len(diagnostics) == 1

    def test_does_not_flag_any_module_when_timescale_precedes_multiple_modules(self) -> None:
        diagnostics = _diagnostics("`timescale 1ns/1ps\nmodule a; endmodule\nmodule b; endmodule")

        assert diagnostics == []
