"""Meta-test keeping the lookup of a module an instance names in one place.

Which module a name refers to, its ports (from a walked file or the cross-file port registry) and its
parameters are answered by `semantic/module_resolver.py`. A file that calls `lookup_module` or reads the
registry itself builds a second answer that can disagree with the first, for example about a module declared
only in another file. The table defines the lookup and the registry; the registry module fills it.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

SRC_ROOT = Path(__file__).resolve().parents[2] / "src"

MODULE_LOOKUPS = {"lookup_module", "module_ports"}

ALLOWED = {
    "pkg/semantic/module_resolver.py": "the one resolver for a module an instance names",
    "pkg/semantic/symbol_table.py": "defines the module table and the registry attribute",
    "pkg/semantic/module_registry.py": "fills the registry before each file's walk",
}


def _uses(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        f"line {node.lineno}: {node.attr}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr in MODULE_LOOKUPS
    ]


def test_modules_are_looked_up_only_through_the_resolver() -> None:
    offenders: dict[str, list[str]] = {}
    for path in sorted(SRC_ROOT.rglob("*.py")):
        rel = path.relative_to(SRC_ROOT).as_posix()
        if rel in ALLOWED:
            continue
        uses = _uses(path)
        if uses:
            offenders[rel] = uses
    assert not offenders, (
        "These files look a module up or read the port registry themselves; ask ModuleResolver instead, or add "
        f"the file to ALLOWED with the reason: {offenders}"
    )


def test_every_allowed_file_exists() -> None:
    missing = [rel for rel in ALLOWED if not (SRC_ROOT / rel).is_file()]
    assert not missing, f"stale entries in ALLOWED: {missing}"
