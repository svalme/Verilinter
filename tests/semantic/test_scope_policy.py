"""The scope policy table is executable: every entry's sample must behave as the entry says."""
from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

import pyslang as sl
import pytest

from src.pkg.handlers.register_handlers import *  # noqa: F401,F403  (registers the handlers)
from src.pkg.parser.parse import parse_text
from src.pkg.rules.declarations_and_types.redeclared_variable import RedeclaredVariableRule
from src.pkg.semantic.scope_kinds import SCOPE_POLICY, ScopeKind, ScopePolicyEntry
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.parse_diagnostics import assert_no_parse_errors

SRC_DIR = Path(__file__).resolve().parents[2] / "src" / "pkg"


def _walk(code: str) -> SymbolTable:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    tree = parse_text(code)
    assert_no_parse_errors("tests/semantic/test_scope_policy.py", tree)
    Walker(dispatch).walk(tree.root, tree, ctx, symbol_table)
    return symbol_table


def _entry_id(entry: ScopePolicyEntry) -> str:
    return "+".join(entry.constructs)


def test_policy_names_real_syntax_kinds() -> None:
    known = {name for name in dir(sl.SyntaxKind) if not name.startswith("_")}
    unknown = [c for entry in SCOPE_POLICY for c in entry.constructs if c not in known]
    assert unknown == []


def test_every_scope_kind_is_produced_by_some_entry() -> None:
    produced = {entry.scope_kind for entry in SCOPE_POLICY if entry.scope_kind is not None}
    assert set(ScopeKind) - produced == {ScopeKind.GLOBAL}


def test_a_construct_appears_in_one_entry_only() -> None:
    counts = Counter(c for entry in SCOPE_POLICY for c in entry.constructs)
    assert [c for c, n in counts.items() if n > 1] == []


def test_scopes_are_created_with_a_scope_kind_not_a_string_literal() -> None:
    """Scope kinds come from ScopeKind so the policy table stays the one list of scope shapes."""
    offenders: list[str] = []
    for path in sorted(SRC_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            callee = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            if callee not in ("new_scope", "Scope"):
                continue
            for keyword in node.keywords:
                if keyword.arg == "kind" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                    offenders.append(f"{path.relative_to(SRC_DIR).as_posix()}:{node.lineno} kind={keyword.value.value!r}")
    assert offenders == [], offenders


@pytest.mark.parametrize("entry", [e for e in SCOPE_POLICY if not e.is_gap], ids=_entry_id)
def test_scoped_construct_opens_its_own_scope(entry: ScopePolicyEntry) -> None:
    table = _walk(entry.sample)

    opened = [scope for scope in table.scopes if scope.kind == entry.scope_kind]
    assert len(opened) >= 2, f"{_entry_id(entry)} did not open a {entry.scope_kind} scope per sibling"
    assert RedeclaredVariableRule().run(table) == [], "sibling declarations collided; the construct shares a scope"


@pytest.mark.parametrize("entry", [e for e in SCOPE_POLICY if e.is_gap], ids=_entry_id)
def test_known_gap_still_shares_its_enclosing_scope(entry: ScopePolicyEntry) -> None:
    """When this fails the construct has been given a scope: record its ScopeKind in the entry."""
    table = _walk(entry.sample)

    assert RedeclaredVariableRule().run(table), (
        f"{_entry_id(entry)} no longer collides with its sibling; it now opens a scope, so set scope_kind in SCOPE_POLICY"
    )
