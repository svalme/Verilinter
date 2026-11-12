"""One lookup serves every consumer: a name brought in by `import pkg::*;` or written `pkg::name` resolves
the same way for the identifier resolver, the constant evaluator, widths and write regions."""
from __future__ import annotations

import pytest

from src.pkg.handlers.register_handlers import *  # noqa: F401,F403
from src.pkg.parser.parse import parse_text
from src.pkg.parser.syntax import evaluate_constant_expression
from src.pkg.rules.combinational_logic.no_multiple_drivers import NoMultipleDriversRule
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.parse_diagnostics import assert_no_parse_errors

PACKAGE = """
package pkg;
  parameter int unsigned A = 0;
  parameter int unsigned B = 1;
  parameter int unsigned W = 4;
  typedef enum logic [1:0] { IDLE = 2'd0, BUSY = 2'd1, DONE = 2'd3 } state_e;
endpackage
"""


def _walk(source: str) -> SymbolTable:
    table = SymbolTable()
    tree = parse_text(source)
    assert_no_parse_errors("tests/semantic/test_package_name_resolution.py", tree)
    Walker(dispatch).walk(tree.root, tree, Context(scope=table.global_scope), table)
    return table


def _module_scope(table: SymbolTable):
    scope = table.lookup_module("m")
    assert scope is not None
    return scope


class TestImportedNames:
    def test_wildcard_import_resolves_through_the_scope_lookup(self) -> None:
        table = _walk(PACKAGE + "module m; import pkg::*; endmodule")
        symbol = _module_scope(table).lookup_hierarchical("W")
        assert symbol is not None and symbol.value == 4

    def test_named_import_brings_in_only_that_name(self) -> None:
        table = _walk(PACKAGE + "module m; import pkg::W; endmodule")
        scope = _module_scope(table)
        assert scope.lookup_hierarchical("W") is not None
        assert scope.lookup_hierarchical("A") is None

    def test_local_declaration_wins_over_an_import(self) -> None:
        table = _walk(PACKAGE + "module m; import pkg::*; localparam W = 9; endmodule")
        assert _module_scope(table).lookup_hierarchical("W").value == 9

    def test_enum_member_of_an_imported_package_resolves(self) -> None:
        table = _walk(PACKAGE + "module m; import pkg::*; endmodule")
        symbol = _module_scope(table).lookup_hierarchical("DONE")
        assert symbol is not None and symbol.value == 3

    def test_the_symbol_table_lookup_agrees_with_the_scope_lookup(self) -> None:
        table = _walk(PACKAGE + "module m; import pkg::*; endmodule")
        scope = _module_scope(table)
        assert table.lookup_from_scope("B", scope) is scope.lookup_hierarchical("B")


class TestConstantEvaluation:
    def _evaluate(self, expression: str, imports: str = "import pkg::*;") -> int | None:
        source = PACKAGE + f"module m; {imports} localparam X = {expression}; endmodule"
        table = _walk(source)
        tree = parse_text(source)
        module = [member for member in tree.root.members if getattr(member, "kind", None).name == "ModuleDeclaration"][0]
        expr = list(module.members)[-1].parameter.declarators[0].initializer.expr
        return evaluate_constant_expression(expr, scope=_module_scope(table))

    def test_imported_constant_in_an_expression(self) -> None:
        assert self._evaluate("W * 2 + B") == 9

    def test_package_qualified_constant_without_an_import(self) -> None:
        assert self._evaluate("pkg::W + 1", imports="") == 5

    def test_unknown_package_is_unknown(self) -> None:
        assert self._evaluate("other::W", imports="") is None

    def test_enum_member_value(self) -> None:
        assert self._evaluate("DONE") == 3


class TestWritesThroughImportedIndices:
    def _diagnostics(self, body: str) -> list[dict]:
        table = _walk(PACKAGE + f"module m(input logic a, input logic b); import pkg::*; logic [3:0] v; {body} endmodule")
        return NoMultipleDriversRule().run(table)

    def test_imported_constant_indices_are_disjoint(self) -> None:
        assert self._diagnostics("assign v[A] = a; assign v[B] = b;") == []

    def test_same_imported_index_still_conflicts(self) -> None:
        assert len(self._diagnostics("assign v[B] = a; assign v[B] = b;")) == 1

    def test_qualified_indices_are_disjoint(self) -> None:
        assert self._diagnostics("assign v[pkg::A] = a; assign v[pkg::B] = b;") == []
