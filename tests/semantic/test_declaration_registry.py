"""The declaration registry is executable: every entry's sample must behave as the entry says."""
from __future__ import annotations

from collections import Counter
import re

import pyslang as sl
import pytest

from src.pkg.handlers.register_handlers import *  # noqa: F401,F403  (registers the handlers)
from src.pkg.parser.parse import parse_text
from src.pkg.semantic.declaration_registry import DECLARATIONS, Coverage, DeclarationEntry
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.parse_diagnostics import assert_no_parse_errors

NAME = "qq_x"
# Declaration-shaped kinds: the ones a new pyslang release could add a name-declaring construct to.
_DECLARATION_SHAPE = re.compile(r"(Declaration|Declarator|Assignment$|Port$|Header$)")


def _declaration_shaped_kinds() -> set[str]:
    names = {name for name in dir(sl.SyntaxKind) if not name.startswith("_") and name[0].isupper()}
    return {n for n in names if _DECLARATION_SHAPE.search(n) and "Statement" not in n and "Expression" not in n}


def _walk(sample: str) -> SymbolTable:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    tree = parse_text(f"`default_nettype none\n{sample}\n`default_nettype wire\n")
    assert_no_parse_errors("tests/semantic/test_declaration_registry.py", tree)
    Walker(dispatch).walk(tree.root, tree, ctx, symbol_table)
    return symbol_table


def _symbols_named(table: SymbolTable, name: str) -> list:
    return [scope.symbols[name] for scope in table.scopes if name in scope.symbols]


def _is_unresolved(table: SymbolTable, name: str) -> bool:
    """The name was used but never declared (what NO_IMPLICIT_NET / UNDECLARED_VARIABLE report)."""
    return any(ref.name == name and ref.is_unresolved for ref in table.unresolved_references)


def _entry_id(entry: DeclarationEntry) -> str:
    return "+".join(entry.kinds[:2])


def test_every_declaration_shaped_syntax_kind_has_an_entry() -> None:
    covered = {kind for entry in DECLARATIONS for kind in entry.kinds}
    missing = sorted(_declaration_shaped_kinds() - covered)
    assert missing == [], (
        "pyslang defines declaration-shaped kinds with no entry in DECLARATIONS; add each with its "
        f"coverage (and a sample when it declares a name): {missing}"
    )


def test_registry_names_real_syntax_kinds() -> None:
    known = {name for name in dir(sl.SyntaxKind) if not name.startswith("_")}
    assert [k for entry in DECLARATIONS for k in entry.kinds if k not in known] == []


def test_a_kind_appears_in_one_entry_only() -> None:
    counts = Counter(kind for entry in DECLARATIONS for kind in entry.kinds)
    assert [kind for kind, n in counts.items() if n > 1] == []


def test_named_handlers_are_registered() -> None:
    registered = {type(handler).__name__ for handler in dispatch._registry.values()}
    named = {entry.handler for entry in DECLARATIONS if entry.handler}
    assert sorted(named - registered) == []


def test_entries_carry_the_fields_their_coverage_requires() -> None:
    problems = []
    for entry in DECLARATIONS:
        if entry.coverage is Coverage.HANDLER and not entry.handler:
            problems.append(f"{_entry_id(entry)}: HANDLER entry names no handler")
        if entry.coverage is not Coverage.NOT_APPLICABLE and not entry.sample:
            problems.append(f"{_entry_id(entry)}: {entry.coverage} entry has no sample")
        if entry.coverage is Coverage.NOT_APPLICABLE and not entry.note:
            problems.append(f"{_entry_id(entry)}: NOT_APPLICABLE entry gives no reason")
    assert problems == []


_RESOLVING = [e for e in DECLARATIONS if e.coverage in (Coverage.HANDLER, Coverage.GENERIC)]
_GAPS = [e for e in DECLARATIONS if e.coverage is Coverage.GAP]


@pytest.mark.parametrize("entry", _RESOLVING, ids=_entry_id)
def test_declared_name_resolves(entry: DeclarationEntry) -> None:
    table = _walk(entry.sample)

    assert not _is_unresolved(table, NAME), f"{_entry_id(entry)}: `{NAME}` was reported as undeclared or an implicit net"
    if entry.declares_kind:
        kinds = {sym.kind for sym in _symbols_named(table, NAME)}
        assert entry.declares_kind in kinds, f"{_entry_id(entry)}: expected a {entry.declares_kind} symbol, found {kinds}"


@pytest.mark.parametrize("entry", _GAPS, ids=_entry_id)
def test_known_gap_still_fails_to_resolve(entry: DeclarationEntry) -> None:
    """When this fails the construct now declares its name: change its coverage to HANDLER or GENERIC."""
    table = _walk(entry.sample)

    assert _is_unresolved(table, NAME), (
        f"{_entry_id(entry)}: `{NAME}` now resolves; update the entry's coverage in DECLARATIONS"
    )
