from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import shutil
import os
import uuid

import pytest

from .support.lint_harness import (
    LintCaseFile,
    LintCaseResult,
    run_file_lint_case,
    run_inline_lint_case,
    run_inline_lint_case_spec,
)

collect_ignore_glob = ["_tmp_*"]


if os.name == "nt":
    @pytest.fixture(name="tmp_path")
    def workspace_tmp_path() -> Path:
        """Use inherited workspace permissions on Windows.

        Python 3.14/pytest's mode-0700 temporary directories can be inaccessible
        to the sandbox account, even with --basetemp inside the workspace.
        Keep each test isolated without requesting that restricted ACL.
        """
        root = (Path(__file__).parent / "_tmp_harness").resolve()
        path = root / f"pytest_{uuid.uuid4().hex}"
        path.mkdir(parents=True)
        try:
            yield path
        finally:
            path.resolve().relative_to(root)
            shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def lint_inline_case() -> Callable[..., LintCaseResult]:
    """Lint inline HDL snippets without touching the filesystem."""

    def _lint_case(files: dict[str, str], *, allow_parse_errors: bool = False) -> LintCaseResult:
        return run_inline_lint_case(files, allow_parse_errors=allow_parse_errors)

    return _lint_case


@pytest.fixture
def lint_inline_case_spec() -> Callable[..., LintCaseResult]:
    """Lint inline HDL snippets with per-file metadata."""

    def _lint_case(
        files: dict[str, LintCaseFile], *, allow_parse_errors: bool = False
    ) -> LintCaseResult:
        return run_inline_lint_case_spec(files, allow_parse_errors=allow_parse_errors)

    return _lint_case


@pytest.fixture
def lint_temp_file_case() -> Callable[..., LintCaseResult]:
    """Lint generated HDL files through the real file-path parser flow."""
    scratch_root = Path(__file__).parent / "_tmp_harness"
    scratch_root.mkdir(parents=True, exist_ok=True)

    def _lint_case(files: dict[str, str], *, allow_parse_errors: bool = False) -> LintCaseResult:
        case_dir = scratch_root / f"case_{uuid.uuid4().hex}"
        case_dir.mkdir(parents=True, exist_ok=False)

        try:
            paths: list[Path] = []
            for relative_path, contents in files.items():
                path = case_dir / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(contents.strip() + "\n", encoding="utf-8")
                paths.append(path)
            return run_file_lint_case(paths, allow_parse_errors=allow_parse_errors)
        finally:
            shutil.rmtree(case_dir, ignore_errors=True)

    return _lint_case
