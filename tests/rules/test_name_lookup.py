"""The rules-area name lookup: what a name refers to from a scope, and what gives none."""
from __future__ import annotations

from src.pkg.rules.name_lookup import named_symbol
from src.pkg.semantic.scope import Scope
from src.pkg.semantic.symbol import Symbol


def _scope_with(name: str, parent: Scope | None = None) -> tuple[Scope, Symbol]:
    scope = Scope("module", "m")
    if parent is not None:
        scope.set_parent(parent)
    symbol = Symbol(name=name, kind="variable")
    scope.define(symbol)
    return scope, symbol


def test_a_name_declared_in_the_scope_is_found() -> None:
    scope, symbol = _scope_with("a")
    assert named_symbol(scope, "a") is symbol


def test_a_name_declared_in_an_enclosing_scope_is_found() -> None:
    outer, symbol = _scope_with("a")
    inner = Scope("block", "b")
    inner.set_parent(outer)
    assert named_symbol(inner, "a") is symbol


def test_an_inner_declaration_hides_an_outer_one_of_the_same_name() -> None:
    outer, _ = _scope_with("a")
    inner, inner_symbol = _scope_with("a", parent=outer)
    assert named_symbol(inner, "a") is inner_symbol


def test_an_unknown_name_gives_none() -> None:
    scope, _ = _scope_with("a")
    assert named_symbol(scope, "missing") is None


def test_an_empty_name_or_no_scope_gives_none() -> None:
    scope, _ = _scope_with("a")
    assert named_symbol(scope, None) is None
    assert named_symbol(scope, "") is None
    assert named_symbol(None, "a") is None


def test_a_scope_with_only_a_plain_lookup_is_asked_for_that() -> None:
    symbol = Symbol(name="a", kind="variable")

    class OnlyLookup:
        def lookup(self, name: str) -> Symbol | None:
            return symbol if name == "a" else None

    assert named_symbol(OnlyLookup(), "a") is symbol
    assert named_symbol(OnlyLookup(), "b") is None


def test_an_object_with_no_lookup_gives_none() -> None:
    assert named_symbol(object(), "a") is None
