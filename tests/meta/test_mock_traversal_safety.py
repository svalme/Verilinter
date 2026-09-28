"""Meta-tests ensuring syntax queries and AST traversals are immune to infinite loops on Mock objects.

When unit tests construct mock AST nodes or mock contexts using `unittest.mock.Mock()`,
attribute accesses like `mock.parent` or `mock.left` dynamically fabricate child Mock
instances rather than returning None. Furthermore, test setups can accidentally construct
cyclic parent graphs (`m.parent = m`).

These tests verify that:
1. All AST ancestor and descendant traversals are strictly bounded (e.g. depth < 64 or 1000).
2. CST/AST queries verify `isinstance(..., SyntaxNode)` where appropriate.
3. Every exported query and predicate in `src.pkg.parser.syntax_queries` safely and quickly
   terminates when passed plain or cyclic `Mock` objects without hanging or raising RecursionError.
"""
from __future__ import annotations

import inspect
import time
from unittest.mock import Mock

import pytest

import src.pkg.parser.syntax_queries as sq
from src.pkg.parser.parse import tree_uses_default_nettype_none
from src.pkg.semantic.scope import Scope, enclosing_module_scope
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context


def test_exported_syntax_queries_mock_safety() -> None:
    """Invokes every callable exported in `syntax_queries` with generic and cyclic Mocks."""
    cyclic_mock = Mock()
    cyclic_mock.parent = cyclic_mock
    cyclic_mock.left = cyclic_mock
    cyclic_mock.right = cyclic_mock
    cyclic_mock.select = cyclic_mock
    cyclic_mock.predicate = cyclic_mock
    cyclic_mock.elseClause = cyclic_mock
    cyclic_mock.clause = cyclic_mock
    cyclic_mock.statement = cyclic_mock
    cyclic_mock.block = cyclic_mock
    cyclic_mock.items = ()
    cyclic_mock.kind = 999999
    cyclic_mock.stack = []

    plain_mock = Mock()
    plain_mock.stack = []

    for name in dir(sq):
        if name.startswith("_"):
            continue
        obj = getattr(sq, name)
        if not callable(obj):
            continue

        sig = inspect.signature(obj)
        params = list(sig.parameters.values())

        # Build dummy arguments for required parameters
        for target_mock in (plain_mock, cyclic_mock):
            args = []
            kwargs = {}
            for param in params:
                pname = param.name.lower()
                if "ctx" in pname:
                    mock_ctx = Mock()
                    mock_ctx.stack = []
                    mock_ctx.scope = Mock(return_value=None)
                    args.append(mock_ctx)
                elif "scope" in pname or "symbol_table" in pname or "symtab" in pname:
                    args.append(target_mock)
                elif "tree" in pname:
                    mock_tree = Mock()
                    mock_tree.sourceManager = None
                    mock_tree.root = None
                    args.append(mock_tree)
                elif param.default is not inspect.Parameter.empty:
                    # Has default, can omit or provide default
                    continue
                else:
                    args.append(target_mock)

            # Ensure execution completes in under 0.1 seconds without hang or recursion error
            t0 = time.perf_counter()
            try:
                obj(*args, **kwargs)
            except (TypeError, AttributeError, ValueError):
                # Expected when mock doesn't fulfill expected structural interface;
                # the goal is preventing infinite loops (RecursionError / hang).
                pass
            elapsed = time.perf_counter() - t0
            assert elapsed < 0.1, f"Function {name} took {elapsed:.4f}s on mock input (possible loop!)"


def test_specific_parent_traversal_cyclic_safety() -> None:
    """Verifies targeted parent-walking functions with explicit cyclic mocks."""
    cyclic = Mock()
    cyclic.parent = cyclic

    # 1. Type query argument
    assert sq.is_type_query_argument(cyclic) is False

    # 2. Branch exclusivity signature
    assert sq.branch_exclusivity_signature(cyclic) == ()

    # 3. Multiple nonblocking write trigger nodes
    assert sq.multiple_nonblocking_write_trigger_nodes(cyclic) == {}

    # 4. System task output argument
    assert sq.is_system_task_output_argument(cyclic) is False

    # 5. Subroutine formal direction
    mock_ctx = Mock()
    mock_ctx.scope = Mock(return_value=None)
    mock_symtab = Mock()
    assert sq.subroutine_formal_direction(cyclic, mock_ctx, mock_symtab) is None

    # 6. Procedural block top-level reset names
    assert sq.procedural_block_top_level_reset_names(cyclic) == set()

    # 7. Unwrapping parentheses
    assert sq.unwrap_parentheses(cyclic) is cyclic


def test_tree_uses_default_nettype_none_mock_safety() -> None:
    """Verifies tree_uses_default_nettype_none terminates on cyclic token mock."""
    mock_tree = Mock()
    mock_token = Mock()
    mock_token.getNextToken.return_value = mock_token
    mock_token.trivia = ()
    mock_root = Mock()
    mock_root.getFirstToken.return_value = mock_token
    mock_tree.root = mock_root

    # Must return False without looping
    t0 = time.perf_counter()
    assert tree_uses_default_nettype_none(mock_tree) is False
    assert time.perf_counter() - t0 < 0.1


def test_semantic_scope_cyclic_safety() -> None:
    """Verifies Scope hierarchical lookup and enclosing_module_scope terminate on cyclic parents."""
    mock_scope = Mock()
    mock_scope.parent = mock_scope
    mock_scope.lookup.return_value = None
    mock_scope.kind = "block"

    t0 = time.perf_counter()
    assert enclosing_module_scope(mock_scope) is None
    assert time.perf_counter() - t0 < 0.1


def test_symbol_table_resolve_cyclic_safety() -> None:
    """Verifies SymbolTable resolution terminates on cyclic scopes."""
    symtab = SymbolTable()
    mock_scope = Mock()
    mock_scope.parent = mock_scope
    mock_scope.lookup.return_value = None
    mock_scope.imports = []

    t0 = time.perf_counter()
    assert symtab.lookup_from_scope("foo", mock_scope) is None
    assert time.perf_counter() - t0 < 0.1


def test_context_stack_cyclic_safety() -> None:
    """Verifies Context.stack property terminates even if _parent forms a cycle."""
    ctx = Context()
    ctx._parent = ctx
    ctx._vnode = Mock()

    t0 = time.perf_counter()
    stack = ctx.stack
    assert time.perf_counter() - t0 < 0.1
    assert len(stack) == 1
