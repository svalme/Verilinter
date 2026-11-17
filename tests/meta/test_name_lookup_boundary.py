"""Meta-test keeping name and symbol lookups in a known set of files.

Every lookup (`lookup`, `lookup_hierarchical`, `lookup_from_scope`, `lookup_package`,
`lookup_package_member`, `lookup_module`, `lookup_qualified`, `lookup_global`) is called or defined in a
file listed below, with what that file uses it for. A file that starts calling a lookup has to be added
here, which is the moment to ask whether `Scope.lookup_hierarchical` (the one name lookup, which follows
imports) is the right call and whether a second copy of its walk is being written.
"""
from __future__ import annotations

import ast
from pathlib import Path

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

LOOKUP_FILES = {
    "pkg/semantic/scope.py": "defines the single-scope lookup, the one name lookup and the package member lookup",
    "pkg/semantic/hierarchical_resolver.py": "the one resolver for hierarchical paths: first segment, block and instance steps, the member",
    "pkg/semantic/package_resolver.py": "the one resolver for a package: its scopes, a member name and a subroutine",
    "pkg/semantic/module_resolver.py": "the one resolver for a module an instance names: its scope, ports and parameters",
    "pkg/semantic/symbol_table.py": "defines the table-level lookups; resolves queued interface member uses",
    "pkg/handlers/identifier_name/symbol_resolver.py": "resolves every identifier occurrence",
    "pkg/handlers/hierarchy_instantiation_handler.py": "symbol behind a shorthand port connection",
    "pkg/handlers/hierarchy_instantiation/port_connection_extractor.py": "a port by name in the child module scope",
    "pkg/handlers/declarations/clocking_declaration_handler.py": "the signals of a clocking block",
    "pkg/handlers/statements/return_statement_handler.py": "the function result variable in the function scope",
    "pkg/parser/_syntax_queries/expressions/symbol_resolution.py": "the one lookup (scope, package member, or mapping) the constant evaluator and the width estimators use",
    "pkg/parser/_syntax_queries/assignment_records.py": "the symbol of an assignment target or initializer",
    "pkg/parser/_syntax_queries/shapes.py": "the base symbol of an element select",
    "pkg/parser/_syntax_queries/fsm.py": "state variables and case item constants",
    "pkg/parser/_syntax_queries/generate/loops.py": "scope wrapper that binds genvars to their values",
    "pkg/rules/arrays_and_indexing/constant_index_out_of_range.py": "the indexed base symbol",
    "pkg/rules/width_and_signedness/no_assignment_width_mismatch.py": "operand symbols for the width rules",
    "pkg/rules/width_and_signedness/operand.py": "operand symbols for the width rules",
    "pkg/rules/fsms/one_hot_encoding_violation.py": "the state variable",
    "pkg/handlers/declarations/declarator_handler.py": "the typedef behind a variable's declared type name",
    "pkg/semantic/connection_records.py": "the signal a connection names, in the instantiating module",
    "pkg/semantic/instance_effects.py": "the child module and the signals a port connection names, to mark instance-driven signals",
    "pkg/rules/connection_analysis.py": "port and connection symbols, child module ports, type-parameter ports",
}


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
        "These files call a name lookup that is not in LOOKUP_FILES; add them with their purpose, "
        "after checking that Scope.lookup_hierarchical is the right call:\n" + "\n".join(violations)
    )


def test_listed_files_still_use_a_lookup() -> None:
    stale = [rel for rel in LOOKUP_FILES if not (SRC_ROOT / rel).exists() or not _lookups_in(SRC_ROOT / rel)]
    assert not stale, "Remove from LOOKUP_FILES, they no longer call a lookup:\n" + "\n".join(stale)
