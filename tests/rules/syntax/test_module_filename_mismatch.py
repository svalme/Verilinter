from pathlib import Path

import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.syntax.module_filename_mismatch import ModuleFilenameMismatchRule

DATA = Path(__file__).parent.parent.parent / "data"


def _diagnostics(path: Path) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    symbol_table.set_current_file(str(path))
    tree = sl.SyntaxTree.fromFile(str(path))
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "MODULE_FILENAME_MISMATCH"]


class TestModuleFilenameMismatchRule:
    @pytest.fixture
    def rule(self) -> ModuleFilenameMismatchRule:
        return ModuleFilenameMismatchRule()

    def test_rule_has_correct_code(self, rule: ModuleFilenameMismatchRule) -> None:
        assert rule.code == "MODULE_FILENAME_MISMATCH"

    def test_flags_module_name_not_matching_filename(self) -> None:
        diagnostics = _diagnostics(DATA / "module_filename_mismatch.v")

        assert len(diagnostics) == 1

    def test_does_not_flag_module_name_matching_filename(self) -> None:
        diagnostics = _diagnostics(DATA / "module_filename_match.v")

        assert diagnostics == []

    def test_does_not_flag_when_any_module_in_file_matches_filename(self) -> None:
        diagnostics = _diagnostics(DATA / "module_filename_match_multi.v")

        assert diagnostics == []
