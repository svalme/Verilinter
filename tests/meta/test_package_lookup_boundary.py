"""Meta-test keeping the lookup of a package, a package member and a package subroutine in one place.

What `pkg::name` refers to, which scope declares a package and which subroutine `pkg::f` calls are answered by
`semantic/package_resolver.py`. A file that reads the table's package registry itself builds a second
answer that can disagree with the first, for example about a package declared in several input files or a
stand-in scope seeded from another file. The scope and the table hold the registry by reference, and the
registry module fills it.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

SRC_ROOT = Path(__file__).resolve().parents[2] / "src"

PACKAGE_REGISTRY_NAMES = {"packages"}

ALLOWED = {
    "pkg/semantic/package_resolver.py": "the one resolver for a package, a member and a subroutine",
    "pkg/semantic/scope.py": "holds the registry by reference and delegates the lookups to the resolver",
    "pkg/semantic/symbol_table.py": "owns the registry and registers a package scope",
    "pkg/semantic/package_registry.py": "records packages and seeds the stand-in scopes of other files' packages",
}


def _uses(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits = [
        f"line {node.lineno}: .{node.attr}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr in PACKAGE_REGISTRY_NAMES
    ]
    hits += [
        f"line {node.lineno}: getattr(..., 'packages')"
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value in PACKAGE_REGISTRY_NAMES
    ]
    return hits


def test_packages_are_looked_up_only_through_the_resolver() -> None:
    offenders: dict[str, list[str]] = {}
    for path in sorted(SRC_ROOT.rglob("*.py")):
        rel = path.relative_to(SRC_ROOT).as_posix()
        if rel in ALLOWED:
            continue
        uses = _uses(path)
        if uses:
            offenders[rel] = uses
    assert not offenders, (
        "These files read the package registry themselves; ask PackageResolver instead "
        f"(symbol_table.package_resolver()), or add the file to ALLOWED with the reason: {offenders}"
    )


def test_every_allowed_file_exists() -> None:
    missing = [rel for rel in ALLOWED if not (SRC_ROOT / rel).is_file()]
    assert not missing, f"stale entries in ALLOWED: {missing}"
