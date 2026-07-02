"""Integration tests proving the multi-file linting path: a shared SymbolTable
accumulates state across real, separately-parsed files, and diagnostics are
correctly attributed back to the file they came from.
"""

from pathlib import Path

import pyslang as sl

from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import symbol_rule_runner
from src.pkg.ast.dispatch import dispatch
from src.pkg.ast.context import Context
from src.pkg.ast.symbol_table import SymbolTable
from src.pkg.ast.walker import Walker

DATA = Path(__file__).parent / "data"
FILE_A = DATA / "dup_module_a.v"
FILE_B = DATA / "dup_module_b.v"


def _walk_files(paths: list[Path]) -> tuple[Walker, SymbolTable]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    for path in paths:
        symbol_table.set_current_file(str(path))
        tree = sl.SyntaxTree.fromFile(str(path))
        walker.walk(tree.root, tree, ctx, symbol_table)

    return walker, symbol_table


class TestMultiFileLinting:
    """dup_module_a.v and dup_module_b.v both declare `module dup_mod` with an
    unused `real unused_sig`, so linting them together should register one
    duplicate module and two distinct unused-variable diagnostics."""

    def test_module_registry_spans_files(self) -> None:
        _, symbol_table = _walk_files([FILE_A, FILE_B])

        assert len(symbol_table.modules["dup_mod"]) == 2
        assert symbol_table.is_duplicate_module("dup_mod") is True

    def test_scopes_are_stamped_with_their_source_file(self) -> None:
        _, symbol_table = _walk_files([FILE_A, FILE_B])

        files = {scope.file for scope in symbol_table.modules["dup_mod"]}
        assert files == {str(FILE_A), str(FILE_B)}

    def test_walker_results_include_nodes_from_every_file(self) -> None:
        # pyslang's SourceManager normalizes absolute paths to be relative to
        # the current working directory, so it may not echo back the exact
        # string we passed to SyntaxTree.fromFile() -- compare by basename
        # rather than assuming byte-for-byte equality with our input path.
        walker, _ = _walk_files([FILE_A, FILE_B])

        seen_files = {
            Path(vnode.location["file"]).name
            for vnode, _ctx in walker.results
            if vnode.location.get("file")
        }
        assert seen_files == {FILE_A.name, FILE_B.name}

    def test_diagnostics_are_attributed_to_the_correct_file(self) -> None:
        _, symbol_table = _walk_files([FILE_A, FILE_B])

        diagnostics = symbol_rule_runner.run(symbol_table)
        unused = [d for d in diagnostics if "unused_sig" in d["message"]]

        assert len(unused) == 2
        assert all("file" in d for d in unused)
        assert {Path(d["file"]).name for d in unused} == {FILE_A.name, FILE_B.name}

    def test_duplicate_module_rule_fires_once_for_the_second_file(self) -> None:
        _, symbol_table = _walk_files([FILE_A, FILE_B])

        diagnostics = symbol_rule_runner.run(symbol_table)
        dup = [d for d in diagnostics if d["message"].startswith("Duplicate module")]

        assert len(dup) == 1
        assert Path(dup[0]["file"]).name == FILE_B.name
        assert FILE_A.name in dup[0]["message"]
