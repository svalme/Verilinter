from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import shutil
import uuid

import pytest

from .support.lint_harness import (
    LintCaseFile,
    LintCaseResult,
    run_file_lint_case,
    run_inline_lint_case,
    run_inline_lint_case_spec,
)


@pytest.fixture
def lint_inline_case() -> Callable[[dict[str, str]], LintCaseResult]:
    """Lint inline HDL snippets without touching the filesystem."""

    def _lint_case(files: dict[str, str]) -> LintCaseResult:
        return run_inline_lint_case(files)

    return _lint_case


@pytest.fixture
def lint_inline_case_spec() -> Callable[[dict[str, LintCaseFile]], LintCaseResult]:
    """Lint inline HDL snippets with per-file metadata."""

    def _lint_case(files: dict[str, LintCaseFile]) -> LintCaseResult:
        return run_inline_lint_case_spec(files)

    return _lint_case


@pytest.fixture
def lint_temp_file_case() -> Callable[[dict[str, str]], LintCaseResult]:
    """Lint generated HDL files through the real file-path parser flow."""
    scratch_root = Path(__file__).parent / "_tmp_harness"
    scratch_root.mkdir(parents=True, exist_ok=True)

    def _lint_case(files: dict[str, str]) -> LintCaseResult:
        case_dir = scratch_root / f"case_{uuid.uuid4().hex}"
        case_dir.mkdir(parents=True, exist_ok=False)

        try:
            paths: list[Path] = []
            for relative_path, contents in files.items():
                path = case_dir / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(contents.strip() + "\n", encoding="utf-8")
                paths.append(path)
            return run_file_lint_case(paths)
        finally:
            shutil.rmtree(case_dir, ignore_errors=True)

    return _lint_case
