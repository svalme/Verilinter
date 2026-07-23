from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pyslang as sl

from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import module_rule_runner, rule_runner, symbol_rule_runner
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker


Diagnostic = dict[str, object]


@dataclass(frozen=True)
class LintCaseResult:
    """Convenience wrapper around end-to-end lint diagnostics."""

    diagnostics: list[Diagnostic]

    def for_code(self, code: str) -> list[Diagnostic]:
        return [diagnostic for diagnostic in self.diagnostics if diagnostic.get("code") == code]

    def files_for_code(self, code: str) -> set[str]:
        return {
            Path(str(diagnostic["file"])).name
            for diagnostic in self.for_code(code)
            if diagnostic.get("file")
        }

    def messages_for_code(self, code: str) -> list[str]:
        return [str(diagnostic["message"]) for diagnostic in self.for_code(code)]


def _run_walked_files(
    file_inputs: list[tuple[str, sl.SyntaxTree]],
    *,
    default_nettype_none_by_file: dict[str, bool] | None = None,
    jobs: int = 1,
) -> LintCaseResult:
    """Run already-parsed files through the real walker and rule runners."""
    if jobs != 1:
        raise NotImplementedError("lint case harness only supports sequential runs")

    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    for file_name, tree in file_inputs:
        symbol_table.set_current_file(file_name)
        symbol_table.set_current_file_default_nettype_none(
            (default_nettype_none_by_file or {}).get(file_name, False)
        )
        walker.walk(tree.root, tree, ctx, symbol_table)

    diagnostics = (
        rule_runner.run(walker.results)
        + symbol_rule_runner.run(symbol_table)
        + module_rule_runner.run(symbol_table)
    )
    return LintCaseResult(diagnostics=diagnostics)


def run_inline_lint_case(files: dict[str, str], *, jobs: int = 1) -> LintCaseResult:
    """Run one or more pseudo-files through the real walker and rule runners.

    The harness stays in-memory so regression tests can cover multi-file cases
    even on environments where temporary-file creation is restricted.
    """
    file_inputs = [
        (str(relative_path), sl.SyntaxTree.fromText(contents.strip() + "\n"))
        for relative_path, contents in files.items()
    ]
    return _run_walked_files(file_inputs, jobs=jobs)


def run_file_lint_case(paths: list[Path], *, jobs: int = 1) -> LintCaseResult:
    """Run real checked-in files through the parser boundary and full file path flow."""
    file_inputs = [
        (str(path), sl.SyntaxTree.fromFile(str(path)))
        for path in paths
    ]
    return _run_walked_files(file_inputs, jobs=jobs)


def run_lint_case(_case_root: Path, files: dict[str, str], *, jobs: int = 1) -> LintCaseResult:
    """Backward-compatible alias for the inline rule-regression harness."""
    return run_inline_lint_case(files, jobs=jobs)
