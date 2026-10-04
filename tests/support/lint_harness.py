from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import uuid

from src.pkg.parser.parse import parse_file, parse_text
from src.pkg.parser.types import SyntaxTree

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

    def expect_clean(self) -> None:
        """Assert that zero diagnostics were reported across all rules and files."""
        assert self.diagnostics == [], (
            f"Expected clean lint result (0 diagnostics), found {len(self.diagnostics)}: {self.diagnostics}"
        )

    def expect_empty(self) -> None:
        """Alias for expect_clean."""
        self.expect_clean()

    def expect_diagnostics(
        self,
        expected: list[object] | tuple[object, ...] | set[object],
        *,
        filter_code: str | None = None,
        filter_file: str | None = None,
        sort: bool = True,
    ) -> None:
        """Assert exact diagnostics matching against a normalized specification.

        Supported item shapes in `expected`:
        - `(line, code)`: e.g. `(10, "NO_IMPLICIT_NET")`
        - `(line, col, code)`: e.g. `(10, 5, "NO_IMPLICIT_NET")`
        - `(file, line, code)`: e.g. `("top.sv", 10, "NO_IMPLICIT_NET")`
        - `(file, line, col, code)`: e.g. `("top.sv", 10, 5, "NO_IMPLICIT_NET")`
        - `code` (str): e.g. `"NO_IMPLICIT_NET"`

        If `filter_code` is provided, only diagnostics with matching `code` are asserted.
        If `filter_file` is provided, only diagnostics matching the filename are asserted.
        If `sort` is True (default), actual and expected items are sorted prior to equality comparison,
        ensuring deterministic, non-brittle verification.
        """
        filtered = self.diagnostics
        if filter_code is not None:
            filtered = [d for d in filtered if d.get("code") == filter_code]
        if filter_file is not None:
            target_name = Path(str(filter_file)).name
            target_posix = Path(str(filter_file)).as_posix()
            filtered = [
                d for d in filtered
                if Path(str(d.get("file", ""))).name == target_name
                or Path(str(d.get("file", ""))).as_posix() == target_posix
                or str(d.get("file", "")) == str(filter_file)
            ]

        expected_seq = list(expected)
        if not expected_seq:
            assert len(filtered) == 0, (
                f"Expected 0 diagnostics (filters: code={filter_code!r}, file={filter_file!r}), "
                f"found {len(filtered)}:\n{filtered}"
            )
            return

        def _shape_tag(item: object) -> tuple[type, ...]:
            if isinstance(item, str):
                return (str,)
            if isinstance(item, tuple):
                return tuple(type(x) for x in item)
            return (type(item),)

        first_shape = _shape_tag(expected_seq[0])
        for idx, item in enumerate(expected_seq):
            if _shape_tag(item) != first_shape:
                raise ValueError(
                    f"Inconsistent expectation shapes in expect_diagnostics: "
                    f"item at index {idx} has shape {_shape_tag(item)}, expected {first_shape}"
                )

        def _project(d: Diagnostic, template: object) -> object:
            if isinstance(template, str):
                return str(d.get("code", ""))
            if isinstance(template, tuple):
                if len(template) == 2 and isinstance(template[0], int) and isinstance(template[1], str):
                    return (int(d.get("line") or 0), str(d.get("code", "")))
                if len(template) == 2 and isinstance(template[0], str) and isinstance(template[1], str):
                    return (Path(str(d.get("file", ""))).name, str(d.get("code", "")))
                if len(template) == 3 and isinstance(template[0], int) and isinstance(template[1], int) and isinstance(template[2], str):
                    return (int(d.get("line") or 0), int(d.get("col") or 0), str(d.get("code", "")))
                if len(template) == 3 and isinstance(template[0], str) and isinstance(template[1], int) and isinstance(template[2], str):
                    return (Path(str(d.get("file", ""))).name, int(d.get("line") or 0), str(d.get("code", "")))
                if len(template) == 4 and isinstance(template[0], str) and isinstance(template[1], int) and isinstance(template[2], int) and isinstance(template[3], str):
                    return (
                        Path(str(d.get("file", ""))).name,
                        int(d.get("line") or 0),
                        int(d.get("col") or 0),
                        str(d.get("code", "")),
                    )
            raise ValueError(f"Unsupported diagnostic expectation shape: {template!r}")

        sample = expected_seq[0]
        actual_normalized = [_project(d, sample) for d in filtered]

        actual_list = sorted(actual_normalized) if sort else actual_normalized
        expected_list = sorted(expected_seq) if sort else expected_seq

        assert actual_list == expected_list, (
            f"Diagnostic expectation mismatch (filters: code={filter_code!r}, file={filter_file!r}):\n"
            f"  Expected ({len(expected_list)}): {expected_list}\n"
            f"  Actual   ({len(actual_list)}): {actual_list}\n"
            f"  Raw diagnostics: {filtered}"
        )


from src.pkg.engine import LintPipeline


def _run_walked_files(
    file_inputs: list[tuple[str, SyntaxTree]],
    *,
    default_nettype_none_by_file: dict[str, bool] | None = None,
    jobs: int = 1,
    allow_parse_errors: bool = False,
    selection: RuleSelection | None = None,
) -> LintCaseResult:
    """Run already-parsed files through the unified multi-phase LintPipeline.

    By default, a file with real parser errors fails loudly here rather than
    silently handing a parser-recovery AST to the walker: pyslang's recovery
    can leave enough tree behind for a rule assertion to pass for reasons
    unrelated to the RTL the case is meant to demonstrate. Pass
    `allow_parse_errors=True` for cases that intentionally exercise recovery,
    and assert on the expected parser errors in the test itself.

    `selection` scopes diagnostics to a specific profile/category configuration
    (see `src/pkg/rules/rule_selection.py`); omitted, every registered rule runs.
    """
    pipeline = LintPipeline()
    result = pipeline.analyze_trees(
        file_inputs,
        default_nettype_none_by_file=default_nettype_none_by_file,
        allow_parse_errors=allow_parse_errors,
        selection=selection,
        jobs=jobs,
    )
    return LintCaseResult(diagnostics=result.diagnostics)


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
        (
            str(relative_path),
            parse_text(
                contents.strip() + "\n",
                name=str(relative_path),
            ),
        )
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
        (
            str(relative_path),
            parse_text(
                file.contents.strip() + "\n",
                name=str(relative_path),
            ),
        )
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
        (str(path), parse_file(path))
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


def run_paired_lint_case(
    files: dict[str, str],
    *,
    tmp_path: Path | None = None,
    jobs: int = 1,
    allow_parse_errors: bool = False,
    selection: RuleSelection | None = None,
) -> LintCaseResult:
    """Run HDL files through BOTH in-memory and on-disk execution pipelines,
    asserting that both pathways produce identical diagnostics, and return
    the verified LintCaseResult.
    """
    inline_result = run_inline_lint_case(
        files,
        jobs=jobs,
        allow_parse_errors=allow_parse_errors,
        selection=selection,
    )

    created_tmp = False
    if tmp_path is None:
        scratch_root = Path(__file__).resolve().parent.parent / "_tmp_harness"
        scratch_root.mkdir(parents=True, exist_ok=True)
        tmp_path = scratch_root / f"paired_{uuid.uuid4().hex}"
        tmp_path.mkdir(parents=True, exist_ok=True)
        created_tmp = True

    try:
        disk_paths: list[Path] = []
        for relative_path, contents in files.items():
            clean_rel = Path(relative_path).as_posix().lstrip("/\\")
            path = tmp_path / clean_rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents.strip() + "\n", encoding="utf-8")
            disk_paths.append(path)

        file_result = run_file_lint_case(
            disk_paths,
            jobs=jobs,
            allow_parse_errors=allow_parse_errors,
            selection=selection,
        )

        def _clean_msg(msg: str) -> str:
            msg_str = str(msg or "")
            prefixes: list[str] = [
                str(tmp_path),
                str(tmp_path.resolve()),
                tmp_path.as_posix(),
                tmp_path.resolve().as_posix(),
            ]
            try:
                rel = tmp_path.resolve().relative_to(Path.cwd().resolve())
                prefixes.extend([str(rel), rel.as_posix()])
            except (ValueError, RuntimeError):
                pass
            for p in prefixes:
                for sep in ("\\", "/"):
                    msg_str = msg_str.replace(p + sep, "")
                msg_str = msg_str.replace(p, "")
            return msg_str.replace("\\", "/")

        def _norm_file(f: object) -> str:
            p = Path(str(f or ""))
            try:
                return p.resolve().relative_to(tmp_path.resolve()).as_posix()
            except (ValueError, RuntimeError):
                return p.as_posix()

        def _norm_tuple(d: Diagnostic) -> tuple[str, int, int, str, str]:
            return (
                _norm_file(d.get("file")),
                int(d.get("line") or 0),
                int(d.get("col") or 0),
                str(d.get("code", "")),
                _clean_msg(str(d.get("message", ""))),
            )

        inline_norm = sorted(_norm_tuple(d) for d in inline_result.diagnostics)
        file_norm = sorted(_norm_tuple(d) for d in file_result.diagnostics)

        assert inline_norm == file_norm, (
            f"Parity mismatch between in-memory and on-disk execution!\n"
            f"  In-memory ({len(inline_norm)}): {inline_norm}\n"
            f"  On-disk   ({len(file_norm)}): {file_norm}"
        )

        return inline_result
    finally:
        if created_tmp and tmp_path.exists():
            shutil.rmtree(tmp_path, ignore_errors=True)


__all__ = [
    "Diagnostic",
    "LintCaseFile",
    "LintCaseResult",
    "run_file_lint_case",
    "run_inline_lint_case",
    "run_inline_lint_case_spec",
    "run_lint_case",
    "run_paired_lint_case",
]
