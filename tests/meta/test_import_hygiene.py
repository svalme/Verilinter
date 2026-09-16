"""Meta-tests enforcing import and state hygiene across the test suite.

Ensures that no test files import directly from `pkg.*` or `run_lint`, which
would create duplicate module namespaces in `sys.modules` and cause `isinstance`
checks on AST vnodes and dispatch registries to fail. All test files must
import from `src.pkg.*` or `src.run_lint`.
"""
from __future__ import annotations

import ast
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parents[1]


def test_test_suite_imports_use_src_prefix() -> None:
    """Statically verifies that all test files import from src.pkg or src.run_lint."""
    violations: list[str] = []

    for py_file in sorted(TESTS_ROOT.rglob("*.py")):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except Exception as err:
            violations.append(f"{py_file}: Parse error: {err}")
            continue

        rel_path = py_file.relative_to(TESTS_ROOT)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "pkg" or alias.name.startswith("pkg."):
                        violations.append(
                            f"tests/{rel_path}:{node.lineno}: 'import {alias.name}' "
                            f"(must use 'import src.{alias.name}')"
                        )
                    elif alias.name == "run_lint" or alias.name.startswith("run_lint."):
                        violations.append(
                            f"tests/{rel_path}:{node.lineno}: 'import {alias.name}' "
                            f"(must use 'import src.{alias.name}')"
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    if node.module == "pkg" or node.module.startswith("pkg."):
                        violations.append(
                            f"tests/{rel_path}:{node.lineno}: 'from {node.module} import ...' "
                            f"(must use 'from src.{node.module} import ...')"
                        )
                    elif node.module == "run_lint" or node.module.startswith("run_lint."):
                        violations.append(
                            f"tests/{rel_path}:{node.lineno}: 'from {node.module} import ...' "
                            f"(must use 'from src.{node.module} import ...')"
                        )

    error_msg = (
        f"Found {len(violations)} non-conforming import(s) in tests/:\n"
        + "\n".join(violations)
        + "\nAll tests must import from 'src.pkg.*' or 'src.run_lint' to prevent "
        "dual-module namespace pollution."
    )
    assert not violations, error_msg


def test_vnode_factory_and_dispatch_registrations_intact() -> None:
    """Verifies that vnode_factory and dispatch registries are populated and not corrupted."""
    from src.pkg.handlers.register_handlers import dispatch
    from src.pkg.vnodes.vnode_factory import vnode_factory

    assert len(vnode_factory._node_map) > 0, "vnode_factory._node_map is empty"
    assert len(dispatch._registry) > 0, "dispatch._registry is empty"
