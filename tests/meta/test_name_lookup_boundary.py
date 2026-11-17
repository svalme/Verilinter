"""Meta-test keeping name and symbol lookups in a known set of files, per area.

Every lookup (`lookup`, `lookup_hierarchical`, `lookup_from_scope`, `lookup_package`,
`lookup_package_member`, `lookup_module`, `lookup_qualified`, `lookup_global`) is called or defined in a
file listed below, with the area it belongs to, the exact lookups it may call and what it uses them for. A
file that starts calling a lookup has to be added here, which is the moment to ask whether
`Scope.lookup_hierarchical` (the one name lookup, which follows imports) or the area's resolver is the right
call and whether a second copy of its walk is being written.

An area is a part of the code that asks the same questions: `semantic` (the tables, scopes and resolver
classes), `handlers` (the walk), `parser_queries` (the syntax query helpers) and `rules`. Each area but
`semantic` has a resolver, the one file that answers a lookup for the others. Another file of that area that
calls a lookup itself is an exception to move onto the resolver; the number of exceptions per area can only
go down, and a lookup an exception calls beyond the ones listed fails the test.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import NamedTuple

import pytest

pytestmark = pytest.mark.meta

SRC_ROOT = Path(__file__).resolve().parents[2] / "src"

LOOKUP_NAMES = {
    "lookup",
    "lookup_hierarchical",
    "lookup_from_scope",
    "lookup_package",
    "lookup_package_member",
    "lookup_module",
    "lookup_qualified",
    "lookup_global",
}


class Entry(NamedTuple):
    area: str
    lookups: frozenset[str]
    purpose: str
    role: str = "user"  # "resolver" answers lookups for its area; "exception" should move onto it; "user" is the area's own plumbing


def _e(area: str, lookups: str, purpose: str, role: str = "user") -> Entry:
    return Entry(area, frozenset(lookups.split()), purpose, role)


LOOKUP_FILES: dict[str, Entry] = {
    # semantic: the tables, scopes and resolver classes
    "pkg/semantic/scope.py": _e("semantic", "lookup lookup_hierarchical lookup_package_member", "defines the single-scope lookup, the one name lookup and the package member lookup"),
    "pkg/semantic/symbol_table.py": _e("semantic", "lookup lookup_from_scope lookup_global lookup_hierarchical lookup_module lookup_package lookup_qualified", "defines the table-level lookups; resolves queued interface member uses"),
    "pkg/semantic/hierarchical_resolver.py": _e("semantic", "lookup lookup_hierarchical", "the one resolver for hierarchical paths: first segment, block and instance steps, the member"),
    "pkg/semantic/module_resolver.py": _e("semantic", "lookup_module", "the one resolver for a module an instance names: its scope, ports and parameters"),
    "pkg/semantic/package_resolver.py": _e("semantic", "lookup", "the one resolver for a package: its scopes, a member name and a subroutine"),
    "pkg/semantic/connection_records.py": _e("semantic", "lookup_hierarchical", "the signal a connection names, in the instantiating module"),
    "pkg/semantic/instance_effects.py": _e("semantic", "lookup_hierarchical", "the child module and the signals a port connection names, to mark instance-driven signals"),
    # handlers: the walk
    "pkg/handlers/identifier_name/symbol_resolver.py": _e("handlers", "lookup_hierarchical lookup_package_member", "resolves every identifier occurrence and answers `symbol_named` for the other handlers", "resolver"),
    # parser_queries: syntax query helpers
    "pkg/parser/_syntax_queries/expressions/symbol_resolution.py": _e("parser_queries", "lookup lookup_hierarchical lookup_package_member", "the one lookup (scope, package member, or mapping) the constant evaluator and the width estimators use", "resolver"),
    "pkg/parser/_syntax_queries/generate/loops.py": _e("parser_queries", "lookup lookup_hierarchical lookup_package_member", "scope wrapper that binds genvars to their values and forwards every lookup"),
    "pkg/parser/_syntax_queries/assignment_records.py": _e("parser_queries", "lookup lookup_hierarchical", "the symbol of an assignment target or initializer", "exception"),
    "pkg/parser/_syntax_queries/shapes.py": _e("parser_queries", "lookup_hierarchical", "the base symbol of an element select", "exception"),
    "pkg/parser/_syntax_queries/fsm.py": _e("parser_queries", "lookup lookup_hierarchical", "state variables and case item constants", "exception"),
    # rules
    "pkg/rules/name_lookup.py": _e("rules", "lookup lookup_hierarchical", "the one place a rule asks which symbol a name refers to from a scope", "resolver"),
}

# The direct callers per area that should move onto the area's resolver. Lower a number when one moves; a new
# exception fails the test and is the moment to ask for a resolver method instead.
EXCEPTIONS_PER_AREA = {"semantic": 0, "handlers": 0, "parser_queries": 3, "rules": 0}
AREAS_WITH_A_RESOLVER = {"handlers", "parser_queries", "rules"}


def _lookups_in(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in LOOKUP_NAMES:
            found.add(node.func.attr)
        elif isinstance(node, ast.FunctionDef) and node.name in LOOKUP_NAMES:
            found.add(node.name)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in LOOKUP_NAMES:
            found.add(node.value)
    return found


def test_lookups_are_called_only_from_listed_files() -> None:
    violations: list[str] = []
    for path in sorted(SRC_ROOT.rglob("*.py")):
        rel = path.relative_to(SRC_ROOT).as_posix()
        if rel in LOOKUP_FILES:
            continue
        violations.extend(f"{rel}: {name}" for name in sorted(_lookups_in(path)))
    assert not violations, (
        "These files call a name lookup that is not in LOOKUP_FILES; add them with their area and purpose, "
        "after checking that Scope.lookup_hierarchical or the area's resolver is the right call:\n" + "\n".join(violations)
    )


def test_listed_files_call_exactly_the_lookups_listed() -> None:
    problems: list[str] = []
    for rel, entry in LOOKUP_FILES.items():
        path = SRC_ROOT / rel
        if not path.exists():
            problems.append(f"{rel}: the file no longer exists; remove it from LOOKUP_FILES")
            continue
        used = _lookups_in(path)
        if used - entry.lookups:
            problems.append(f"{rel}: also calls {sorted(used - entry.lookups)}; ask the area resolver or list it")
        if entry.lookups - used:
            problems.append(f"{rel}: no longer calls {sorted(entry.lookups - used)}; remove it from the list")
    assert not problems, "\n".join(problems)


def test_each_area_with_a_resolver_names_one_and_counts_its_exceptions() -> None:
    problems: list[str] = []
    for area in sorted({entry.area for entry in LOOKUP_FILES.values()}):
        entries = {rel: entry for rel, entry in LOOKUP_FILES.items() if entry.area == area}
        resolvers = [rel for rel, entry in entries.items() if entry.role == "resolver"]
        exceptions = [rel for rel, entry in entries.items() if entry.role == "exception"]
        if area in AREAS_WITH_A_RESOLVER and not resolvers:
            problems.append(f"{area}: no file is marked as the area's resolver")
        if area not in AREAS_WITH_A_RESOLVER and (resolvers or exceptions):
            problems.append(f"{area}: has no resolver, so it has no exceptions either")
        expected = EXCEPTIONS_PER_AREA.get(area, 0)
        if len(exceptions) != expected:
            problems.append(
                f"{area}: {len(exceptions)} direct callers of a lookup where the area has a resolver, expected "
                f"{expected} (lower EXCEPTIONS_PER_AREA when one moves onto the resolver): {exceptions}"
            )
    assert not problems, "\n".join(problems)
