from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from .support.lint_harness import LintCaseResult, run_inline_lint_case


@pytest.fixture
def lint_inline_case() -> Callable[[dict[str, str]], LintCaseResult]:
    """Lint inline HDL snippets without touching the filesystem."""

    def _lint_case(files: dict[str, str]) -> LintCaseResult:
        return run_inline_lint_case(files)

    return _lint_case
