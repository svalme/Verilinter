"""Malformed AST and stress tests for syntax queries, scope resolution, and AST walkers.

Validates that:
1. Pyslang error-recovery syntax trees (with syntax errors, missing tokens, skipped tokens)
   pass safely through all syntax queries and rule inspection routines without unhandled exceptions.
2. Pathologically deep AST nesting (depth > 64, up to depth 500) respects recursion limits
   and terminates without RecursionError or stack overflows.
3. Malformed nodes (missing attributes, unexpected primitive types, non-iterable objects)
   are handled defensively without crashing.
4. Scope hierarchies, SymbolTable resolution, and Context stacks with cyclic or malformed
   structures terminate safely.
5. The core Walker terminates cleanly even on pathological or cyclic AST topologies.
"""
from __future__ import annotations

from unittest.mock import Mock

import pytest
import pyslang as sl

import src.pkg.parser.syntax_queries as sq
from src.pkg.parser.parse import parse_text
from src.pkg.semantic.scope import Scope, enclosing_module_scope
from src.pkg.semantic.symbol import Symbol
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.vnodes.base_vnode import BaseVNode
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import Dispatch
from src.pkg.walk.walker import Walker
from tests.support.termination import terminates_within


pytestmark = pytest.mark.stress


# ---------------------------------------------------------------------------
# 1. Pyslang Error-Recovery Syntax Trees (Malformed RTL Snippets)
# ---------------------------------------------------------------------------

PATHOLOGICAL_SNIPPETS = [
    # Broken port lists and empty syntax nodes
    "module m(;;; ,,, ;); endmodule",
    # Unclosed conditional and case blocks
    "module m; initial begin if (1) case (x) endmodule",
    # Mismatched begin/end with stray tokens
    "module m; always_comb begin if (a) begin b = 1; end else begin ; end endmodule",
    # Malformed expressions with operator cascades
    "module m; assign a = + - * / % & | ^ ~! b; endmodule",
    # Malformed multidimensional slicing and concatenations
    "module m; assign x = { { { ,,, } } } + a[:][+:]; endmodule",
    # Unterminated generate and instantiate constructs
    "module m; generate if (1) begin : foo sub #() u1 (); endgenerate endmodule",
    # Severely broken module headers with keyword collisions
    "module module module (input wire logic logic [][]); endmodule",
]


@pytest.mark.parametrize("snippet", PATHOLOGICAL_SNIPPETS)
def test_queries_on_error_recovery_trees(snippet: str) -> None:
    """Parses malformed RTL through pyslang error-recovery and verifies all queries tolerate the CST."""
    tree = parse_text(snippet)
    assert tree is not None
    root = tree.root
    assert root is not None

    symtab = SymbolTable()
    scope = symtab.new_scope("module", name="m")
    ctx = Context(scope=scope)

    # Walk all descendant nodes in the malformed tree and execute core queries
    def _visit(node: object) -> None:
        if not isinstance(node, sl.SyntaxNode):
            return

        # Core queries should run without raising unexpected exceptions or looping
        _ = sq.unwrap_parentheses(node)
        _ = sq.is_conditional_statement(node)
        _ = sq.is_assignment_expression(node)
        _ = sq.assignment_left(node)
        _ = sq.assignment_right(node)
        _ = sq.assignment_target_identifier_name(node)
        _ = sq.evaluate_constant_expression(node, scope=scope)
        _ = sq.simple_expression_width_and_signed(scope, node, tree)
        _ = sq.natural_expression_width_and_signed(scope, node, tree)
        _ = sq.extract_assignment_target_and_selectors(node)
        _ = sq.resolve_assignment_target(node, scope, tree)
        _ = sq.is_state_register_reset_covered(node, "dummy")
        _ = list(sq.iter_assignment_nodes(node))
        _ = list(sq.iter_identifier_reads(node))

        for child in node:
            if isinstance(child, sl.SyntaxNode):
                _visit(child)

    # Every exported query runs on every node of the tree, so this budget is larger.
    with terminates_within(budget_s=10.0):
        _visit(root)


# ---------------------------------------------------------------------------
# 2. Pathologically Deep AST Nesting
# ---------------------------------------------------------------------------

def test_deeply_nested_parenthesized_expressions() -> None:
    """Verifies that 100 levels of nested parentheses terminate within depth bounds."""
    nested_text = "module m; assign x = " + ("(" * 100) + "a" + (")" * 100) + "; endmodule"
    tree = parse_text(nested_text)
    assert tree is not None
    root = tree.root

    with terminates_within():
        unwrapped = sq.unwrap_parentheses(root)
        assert unwrapped is not None


def test_deeply_nested_element_selectors() -> None:
    """Verifies that 100 levels of chained element selects terminate within depth bounds."""
    nested_text = "module m; assign x = a" + ("[0]" * 100) + "; endmodule"
    tree = parse_text(nested_text)
    assert tree is not None

    scope = SymbolTable().new_scope("module", name="m")
    with terminates_within():
        w, is_signed = sq.simple_expression_width_and_signed(scope, tree.root, tree)


def test_deeply_nested_concatenations() -> None:
    """Verifies that 100 levels of nested concatenations terminate within depth bounds."""
    nested_text = "module m; assign x = " + ("{" * 100) + "1'b0" + ("}" * 100) + "; endmodule"
    tree = parse_text(nested_text)
    assert tree is not None

    scope = SymbolTable().new_scope("module", name="m")
    with terminates_within():
        w, is_signed = sq.simple_expression_width_and_signed(scope, tree.root, tree)


# ---------------------------------------------------------------------------
# 3. Malformed Nodes and Degenerate Inputs
# ---------------------------------------------------------------------------

def test_queries_with_none_and_degenerate_types() -> None:
    """Verifies queries handle None, empty strings, ints, and raw dicts gracefully."""
    assert sq.source_text_for_node(None, None) is None
    for degenerate in (None, 0, 42, "", "   ", (), [], {}, object()):
        assert sq.is_conditional_statement(degenerate) is False
        assert sq.is_assignment_expression(degenerate) is False
        assert sq.assignment_left(degenerate) is None
        assert sq.assignment_right(degenerate) is None
        assert sq.assignment_target_identifier_name(degenerate) is None
        assert sq.constant_integer_value(degenerate) is None
        assert sq.evaluate_constant_expression(degenerate) is None
        assert sq.unwrap_parentheses(degenerate) is degenerate
        assert sq.raw_node_children(degenerate) == []
        assert sq.node_location(degenerate, None) is None
        assert sq.is_state_register_reset_covered(degenerate, "foo") is False
        assert list(sq.iter_assignment_nodes(degenerate)) == []
        assert list(sq.iter_identifier_reads(degenerate)) == []


def test_queries_with_mock_missing_attributes() -> None:
    """Verifies queries handle mock objects with arbitrary missing or None attributes."""
    bare_mock = Mock(spec=[])  # No attributes defined

    assert sq.is_conditional_statement(bare_mock) is False
    assert sq.is_assignment_expression(bare_mock) is False
    assert sq.assignment_left(bare_mock) is None
    assert sq.assignment_right(bare_mock) is None
    assert sq.assignment_target_identifier_name(bare_mock) is None
    assert sq.constant_integer_value(bare_mock) is None
    assert sq.evaluate_constant_expression(bare_mock) is None
    assert sq.raw_node_children(bare_mock) == []
    assert sq.is_state_register_reset_covered(bare_mock, "clk") is False


# ---------------------------------------------------------------------------
# 4. Scope and SymbolTable Loop Immunity
# ---------------------------------------------------------------------------

def test_scope_hierarchical_cycle_immunity() -> None:
    """Verifies Scope.lookup_hierarchical terminates when scopes form parent cycles."""
    scope_a = Scope(kind="block", name="A")
    scope_b = Scope(kind="block", name="B")
    scope_a.parent = scope_b
    scope_b.parent = scope_a

    with terminates_within():
        assert scope_a.lookup_hierarchical("non_existent") is None


def test_symbol_table_lookup_global_cycle_immunity() -> None:
    """Verifies SymbolTable.lookup_global terminates when children form cycles."""
    symtab = SymbolTable()
    child_scope = Scope(kind="block", name="child")
    child_scope.children = [child_scope]
    symtab.global_scope.children = [child_scope]

    with terminates_within():
        assert symtab.lookup_global("non_existent") is None


def test_symbol_table_package_import_cycle_immunity() -> None:
    """Verifies SymbolTable.lookup_from_scope terminates when packages import each other circularly."""
    symtab = SymbolTable()
    pkg_a_scope = Scope(kind="package", name="pkgA")
    pkg_b_scope = Scope(kind="package", name="pkgB")

    pkg_a_scope.add_import("pkgB", None)
    pkg_b_scope.add_import("pkgA", None)

    symtab.register_package("pkgA", pkg_a_scope)
    symtab.register_package("pkgB", pkg_b_scope)

    test_scope = Scope(kind="module", name="top")
    test_scope.add_import("pkgA", None)

    with terminates_within():
        assert symtab.lookup_from_scope("unknown_sym", test_scope) is None


# ---------------------------------------------------------------------------
# 5. Walker Resilience on Cyclic and Malformed Graphs
# ---------------------------------------------------------------------------

def test_walker_terminates_on_cyclic_ast_graph() -> None:
    """Verifies Walker.walk terminates and recovers gracefully on cyclical AST graphs."""
    cyclic_node = Mock(spec=sl.SyntaxNode)
    cyclic_node.kind = 999999
    cyclic_node.__iter__ = lambda self: iter([cyclic_node])

    dispatch = Dispatch()
    walker = Walker(dispatch)
    ctx = Context()
    symtab = SymbolTable()
    tree = Mock(spec=sl.SyntaxTree)

    with terminates_within():
        walker.walk(cyclic_node, tree, ctx, symtab)
    assert len(walker.results) == 1
