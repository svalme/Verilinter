from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pyslang as sl

from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import module_rule_runner, rule_runner, symbol_rule_runner
from src.pkg.rules.rule_selection import RuleSelection
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker

from .parse_diagnostics import assert_no_parse_errors


Diagnostic = dict[str, object]


@dataclass(frozen=True)
class LintCaseFile:
    """One file in a lint case, with optional per-file metadata."""

    contents: str
    default_nettype_none: bool = False


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

    def expect_no_code(self, code: str) -> None:
        matches = self.for_code(code)
        assert matches == [], f"Expected no diagnostics for {code}, found: {matches}"

    def expect_code_count(self, code: str, count: int) -> list[Diagnostic]:
        matches = self.for_code(code)
        assert len(matches) == count, (
            f"Expected {count} diagnostics for {code}, found {len(matches)}: {matches}"
        )
        return matches

    def expect_code_once(self, code: str) -> Diagnostic:
        matches = self.expect_code_count(code, 1)
        return matches[0]

    def expect_codes(self, expected_codes: set[str]) -> None:
        actual_codes = {str(diagnostic["code"]) for diagnostic in self.diagnostics}
        assert actual_codes == expected_codes, (
            f"Expected diagnostic codes {expected_codes}, found {actual_codes}"
        )

    def expect_files_for_code(self, code: str, expected_files: set[str]) -> None:
        actual_files = self.files_for_code(code)
        assert actual_files == expected_files, (
            f"Expected files {expected_files} for {code}, found {actual_files}"
        )

    def expect_message_contains(self, code: str, text: str) -> None:
        messages = self.messages_for_code(code)
        assert any(text in message for message in messages), (
            f"Expected at least one {code} message to contain {text!r}, found: {messages}"
        )


def _run_walked_files(
    file_inputs: list[tuple[str, sl.SyntaxTree]],
    *,
    default_nettype_none_by_file: dict[str, bool] | None = None,
    jobs: int = 1,
    allow_parse_errors: bool = False,
    selection: RuleSelection | None = None,
) -> LintCaseResult:
    """Run already-parsed files through the real walker and rule runners.

    By default, a file with real parser errors fails loudly here rather than
    silently handing a parser-recovery AST to the walker: pyslang's recovery
    can leave enough tree behind for a rule assertion to pass for reasons
    unrelated to the RTL the case is meant to demonstrate. Pass
    `allow_parse_errors=True` for cases that intentionally exercise recovery,
    and assert on the expected parser errors in the test itself.

    `selection` scopes diagnostics to a specific profile/category configuration
    (see `src/pkg/rules/rule_selection.py`); omitted, every registered rule runs.
    """
    if jobs != 1:
        raise NotImplementedError("lint case harness only supports sequential runs")

    if not allow_parse_errors:
        for file_name, tree in file_inputs:
            assert_no_parse_errors(file_name, tree)

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
        rule_runner.run(walker.results, selection)
        + symbol_rule_runner.run(symbol_table, selection)
        + module_rule_runner.run(symbol_table, selection)
    )
    return LintCaseResult(diagnostics=diagnostics)


def run_inline_lint_case(
    files: dict[str, str],
    *,
    jobs: int = 1,
    allow_parse_errors: bool = False,
    selection: RuleSelection | None = None,
) -> LintCaseResult:
    """Run one or more pseudo-files through the real walker and rule runners.

    The harness stays in-memory so regression tests can cover multi-file cases
    even on environments where temporary-file creation is restricted.
    """
    file_inputs = [
        (str(relative_path), sl.SyntaxTree.fromText(contents.strip() + "\n"))
        for relative_path, contents in files.items()
    ]
    return _run_walked_files(
        file_inputs, jobs=jobs, allow_parse_errors=allow_parse_errors, selection=selection
    )


def run_inline_lint_case_spec(
    files: dict[str, LintCaseFile],
    *,
    jobs: int = 1,
    allow_parse_errors: bool = False,
    selection: RuleSelection | None = None,
) -> LintCaseResult:
    """Run inline HDL snippets with per-file metadata such as default_nettype state."""
    file_inputs = [
        (str(relative_path), sl.SyntaxTree.fromText(file.contents.strip() + "\n"))
        for relative_path, file in files.items()
    ]
    default_nettype_none_by_file = {
        str(relative_path): file.default_nettype_none for relative_path, file in files.items()
    }
    return _run_walked_files(
        file_inputs,
        default_nettype_none_by_file=default_nettype_none_by_file,
        jobs=jobs,
        allow_parse_errors=allow_parse_errors,
        selection=selection,
    )


def run_file_lint_case(
    paths: list[Path],
    *,
    jobs: int = 1,
    allow_parse_errors: bool = False,
    selection: RuleSelection | None = None,
) -> LintCaseResult:
    """Run real checked-in files through the parser boundary and full file path flow."""
    file_inputs = [
        (str(path), sl.SyntaxTree.fromFile(str(path)))
        for path in paths
    ]
    return _run_walked_files(
        file_inputs, jobs=jobs, allow_parse_errors=allow_parse_errors, selection=selection
    )


def run_lint_case(
    _case_root: Path, files: dict[str, str], *, jobs: int = 1, allow_parse_errors: bool = False
) -> LintCaseResult:
    """Backward-compatible alias for the inline rule-regression harness."""
    return run_inline_lint_case(files, jobs=jobs, allow_parse_errors=allow_parse_errors)
