"""Integration coverage for IdentifierNameHandler against a real parsed file:
proves vnode_factory registration, dispatch registration, handler execution,
and the full walker all agree on how identifier reference nodes are handled.
"""

from pathlib import Path

import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.vnodes.identifier_vnode import IdentifierNameVNode
from src.pkg.vnodes.register_vnodes import *
from src.pkg.vnodes.vnode_factory import vnode_factory

DATA = Path(__file__).parent.parent / "data"


IDENTIFIER_NODE_TYPES = (sl.IdentifierNameSyntax, sl.IdentifierSelectNameSyntax)


def _find_identifier_nodes(node) -> list[sl.SyntaxNode]:
    results = []
    if isinstance(node, IDENTIFIER_NODE_TYPES):
        results.append(node)
    if hasattr(node, "__iter__"):
        for child in node:
            results.extend(_find_identifier_nodes(child))
    return results


@pytest.fixture
def tree() -> sl.SyntaxTree:
    return sl.SyntaxTree.fromFile(str(DATA / "simple.v"))


class TestIdentifierHandlerRegistration:
    def test_identifier_name_syntax_is_registered_with_vnode_factory(self) -> None:
        assert sl.IdentifierNameSyntax in vnode_factory._node_map
        assert vnode_factory._node_map[sl.IdentifierNameSyntax] is IdentifierNameVNode

    def test_identifier_select_name_syntax_is_registered_with_vnode_factory(self) -> None:
        assert sl.IdentifierSelectNameSyntax in vnode_factory._node_map
        assert vnode_factory._node_map[sl.IdentifierSelectNameSyntax] is IdentifierNameVNode

    def test_identifier_name_syntax_is_registered_with_dispatch(self) -> None:
        assert sl.IdentifierNameSyntax in dispatch._registry

    def test_identifier_select_name_syntax_is_registered_with_dispatch(self) -> None:
        assert sl.IdentifierSelectNameSyntax in dispatch._registry


class TestIdentifierHandlerAgainstRealFile:
    def test_finds_identifier_nodes_in_simple_v(self, tree: sl.SyntaxTree) -> None:
        identifier_nodes = _find_identifier_nodes(tree.root)
        assert len(identifier_nodes) > 0

    def test_vnode_factory_creates_identifier_name_vnode(self, tree: sl.SyntaxTree) -> None:
        raw_node = _find_identifier_nodes(tree.root)[0]
        vnode = vnode_factory.create(raw_node, tree)

        assert isinstance(vnode, IdentifierNameVNode)
        assert vnode.identifier_name

    def test_handler_update_context_registers_a_symbol(self, tree: sl.SyntaxTree) -> None:
        raw_node = _find_identifier_nodes(tree.root)[0]
        vnode = vnode_factory.create(raw_node, tree)
        handler = dispatch.get(vnode)

        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)

        new_ctx = handler.update_context(ctx, vnode, symbol_table)

        assert len(new_ctx.stack) == len(ctx.stack) + 1
        assert symbol_table.global_scope.lookup(vnode.identifier_name) is not None

    def test_full_walk_visits_every_identifier_in_the_file(self, tree: sl.SyntaxTree) -> None:
        walker = Walker(dispatch)
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)

        walker.walk(tree.root, tree, ctx, symbol_table)

        identifier_results = [
            vnode for vnode, _ctx in walker.results if isinstance(vnode, IdentifierNameVNode)
        ]
        raw_identifier_count = len(_find_identifier_nodes(tree.root))

        assert len(identifier_results) == raw_identifier_count
