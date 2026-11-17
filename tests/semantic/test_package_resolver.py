"""The package resolver: what it says about a package and its members, and what it must not guess."""
from __future__ import annotations

from src.pkg.handlers.register_handlers import *  # noqa: F401,F403
from src.pkg.parser.parse import parse_text
from src.pkg.semantic.package_registry import record_packages_from_symbol_table, seed_cross_file_packages
from src.pkg.semantic.package_resolver import PackageResolver
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.parse_diagnostics import assert_no_parse_errors

PACKAGE = """
package pkg;
  parameter int WIDTH = 8;
  typedef logic [3:0] nibble_t;
  function automatic int twice(input int a, output int b);
    b = a;
    return a * 2;
  endfunction
  task automatic poke(input logic x, inout logic y);
    y = x;
  endtask
endpackage
"""


def _table(code: str = PACKAGE) -> SymbolTable:
    symbol_table = SymbolTable()
    tree = parse_text(code)
    assert_no_parse_errors("tests/semantic/test_package_resolver.py", tree)
    Walker(dispatch).walk(tree.root, tree, Context(scope=symbol_table.global_scope), symbol_table)
    return symbol_table


def test_a_declared_package_has_a_scope_and_members() -> None:
    resolver = _table().package_resolver()
    assert resolver.is_declared("pkg")
    assert resolver.scope("pkg") is not None
    member = resolver.member("pkg", "WIDTH")
    assert member is not None and member.name == "WIDTH"


def test_an_unknown_package_or_member_is_none_and_not_declared() -> None:
    resolver = _table().package_resolver()
    assert not resolver.is_declared("other")
    assert resolver.scope("other") is None
    assert resolver.member("other", "WIDTH") is None
    assert resolver.member("pkg", "MISSING") is None


def test_a_member_is_looked_up_in_the_package_only_not_in_an_enclosing_scope() -> None:
    table = _table(PACKAGE + "\nmodule top; localparam OUTER = 1; endmodule\n")
    resolver = table.package_resolver()
    assert resolver.member("pkg", "OUTER") is None
    assert resolver.member("top", "OUTER") is None


def test_a_function_and_a_task_are_found_as_subroutines() -> None:
    resolver = _table().package_resolver()
    function = resolver.subroutine("pkg", "twice")
    task = resolver.subroutine("pkg", "poke")
    assert function is not None and function.name == "twice"
    assert task is not None and task.name == "poke"


def test_a_member_that_is_not_a_subroutine_is_not_found_as_one() -> None:
    resolver = _table().package_resolver()
    assert resolver.subroutine("pkg", "WIDTH") is None
    assert resolver.subroutine("pkg", "missing") is None
    assert resolver.subroutine("other", "twice") is None


def test_the_resolver_over_no_registry_knows_no_package() -> None:
    resolver = PackageResolver(None)
    assert resolver.scope("pkg") is None
    assert not resolver.is_declared("pkg")
    assert resolver.scopes("pkg") == []


def test_the_scope_that_declares_a_package_is_not_a_stand_in() -> None:
    scope = _table().package_resolver().scope("pkg")
    assert scope is not None and not scope.is_stand_in


def test_a_package_seeded_from_another_file_is_a_stand_in_and_resolves_members() -> None:
    declaring = _table()
    registry: dict[str, list[dict]] = {}
    record_packages_from_symbol_table("pkg_file.sv", declaring, registry)

    importing = SymbolTable()
    seed_cross_file_packages(importing, registry, "user_file.sv")
    resolver = importing.package_resolver()
    scope = resolver.scope("pkg")
    assert scope is not None and scope.is_stand_in
    assert resolver.member("pkg", "WIDTH") is not None
    assert resolver.subroutine("pkg", "twice") is not None
    assert scope not in importing.scopes
