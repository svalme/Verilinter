"""Integration coverage for IdentifierNameHandler against a real parsed file:
proves vnode_factory registration, dispatch registration, handler execution,
and the full walker all agree on how identifier reference nodes are handled.
"""

from pathlib import Path

import pytest

from src.pkg.parser.parse import parse_file
from src.pkg.parser.syntax import is_subroutine_prototype_name
from src.pkg.parser.types import (
    IDENTIFIER_NAME_NODE_TYPES,
    IdentifierNameNode,
    IdentifierSelectNameNode,
    SyntaxNode,
    SyntaxTree,
)
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.vnodes.identifier_vnode import IdentifierNameVNode
from src.pkg.vnodes.register_vnodes import *
from src.pkg.vnodes.vnode_factory import vnode_factory

DATA = Path(__file__).resolve().parents[3] / "data"


IDENTIFIER_NODE_TYPES = IDENTIFIER_NAME_NODE_TYPES


def _find_identifier_nodes(node) -> list[SyntaxNode]:
    results = []
    if isinstance(node, IDENTIFIER_NODE_TYPES):
        results.append(node)
    if hasattr(node, "__iter__"):
        for child in node:
            results.extend(_find_identifier_nodes(child))
    return results


@pytest.fixture
def tree() -> SyntaxTree:
    return parse_file(DATA / "simple.v")


class TestIdentifierHandlerRegistration:
    def test_identifier_name_syntax_is_registered_with_vnode_factory(self) -> None:
        assert IdentifierNameNode in vnode_factory._node_map
        assert vnode_factory._node_map[IdentifierNameNode] is IdentifierNameVNode

    def test_identifier_select_name_syntax_is_registered_with_vnode_factory(self) -> None:
        assert IdentifierSelectNameNode in vnode_factory._node_map
        assert vnode_factory._node_map[IdentifierSelectNameNode] is IdentifierNameVNode

    def test_identifier_name_syntax_is_registered_with_dispatch(self) -> None:
        assert IdentifierNameNode in dispatch._registry

    def test_identifier_select_name_syntax_is_registered_with_dispatch(self) -> None:
        assert IdentifierSelectNameNode in dispatch._registry


class TestIdentifierHandlerAgainstRealFile:
    def test_finds_identifier_nodes_in_simple_v(self, tree: SyntaxTree) -> None:
        identifier_nodes = _find_identifier_nodes(tree.root)
        assert len(identifier_nodes) > 0

    def test_vnode_factory_creates_identifier_name_vnode(self, tree: SyntaxTree) -> None:
        raw_node = _find_identifier_nodes(tree.root)[0]
        vnode = vnode_factory.create(raw_node, tree)

        assert isinstance(vnode, IdentifierNameVNode)
        assert vnode.identifier_name

    def test_handler_update_context_registers_a_symbol(self, tree: SyntaxTree) -> None:
        raw_node = _find_identifier_nodes(tree.root)[0]
        vnode = vnode_factory.create(raw_node, tree)
        handler = dispatch.get(vnode)

        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)

        new_ctx = handler.update_context(ctx, vnode, symbol_table)

        assert len(new_ctx.stack) == len(ctx.stack) + 1
        assert symbol_table.global_scope.lookup(vnode.identifier_name) is not None

    def test_full_walk_visits_every_identifier_in_the_file(self, tree: SyntaxTree) -> None:
        walker = Walker(dispatch)
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)

        walker.walk(tree.root, tree, ctx, symbol_table)

        identifier_results = [
            vnode for vnode, _ctx in walker.results if isinstance(vnode, IdentifierNameVNode)
        ]
        raw_identifier_count = len(_find_identifier_nodes(tree.root))

        assert len(identifier_results) == raw_identifier_count


class TestIdentifierHandlerSkipsBindDirectiveTarget:
    def test_bind_directive_target_name_is_not_registered_as_a_symbol(self) -> None:
        """A `bind` directive's target names a module, not a variable; walking it must
        not create an implicit-net symbol the way an ordinary identifier read would."""
        tree = parse_file(DATA / "bind_directive.sv")
        walker = Walker(dispatch)
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)

        walker.walk(tree.root, tree, ctx, symbol_table)

        assert symbol_table.global_scope.lookup("bind_directive_target") is None


class TestIdentifierHandlerSkipsSubroutinePrototypeName:
    def test_task_name_is_not_registered_as_a_symbol(self) -> None:
        """A task/function's own declared name is not a variable read; walking it must
        not create an implicit-net symbol anywhere in the symbol table."""
        tree = parse_file(DATA / "task_declaration.v")
        walker = Walker(dispatch)
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)

        walker.walk(tree.root, tree, ctx, symbol_table)

        assert all(scope.lookup("do_work") is None for scope in symbol_table.scopes)

    def test_predicate_true_for_declaration_name_false_for_body_reference(self) -> None:
        """`add_one` appears twice in function_declaration.sv: once as the function's own
        declared name (`FunctionPrototypeSyntax.name`), and once as an ordinary identifier
        inside the body (`add_one = x + 1;`, the classic implicit-return-variable pattern).
        Only the first is a declaration name; the second is a genuine identifier reference
        the predicate must NOT swallow, since it's the well-known separate gap (function
        return-variable modeling) documented in RULES.md rather than something this fix
        addresses."""
        tree = parse_file(DATA / "function_declaration.sv")

        identifier_nodes = [
            node for node in _find_identifier_nodes(tree.root)
            if getattr(getattr(node, "identifier", None), "valueText", None) == "add_one"
        ]

        prototype_names = [node for node in identifier_nodes if is_subroutine_prototype_name(node)]
        body_references = [node for node in identifier_nodes if not is_subroutine_prototype_name(node)]

        assert len(prototype_names) == 1
        assert len(body_references) >= 1


class TestIdentifierHandlerSkipsDefparamTarget:
    def test_defparam_hierarchical_target_is_not_registered_as_a_symbol(self) -> None:
        """`defparam u_child.WIDTH = 8;` names a hierarchical parameter-override path,
        not a variable; neither the instance segment nor the parameter segment should
        be walked as an ordinary identifier read."""
        tree = parse_file(DATA / "defparam_usage.v")
        walker = Walker(dispatch)
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)

        walker.walk(tree.root, tree, ctx, symbol_table)

        for scope in symbol_table.scopes:
            symbol = scope.lookup("WIDTH")
            assert symbol is None or symbol.kind != "implicit_net"


class TestIdentifierHandlerSkipsDisableStatementTarget:
    def test_disable_statement_label_is_not_registered_as_a_symbol(self) -> None:
        """`disable done_flag;` names a block/task label, not a variable read."""
        tree = parse_file(DATA / "disable_statement.v")
        walker = Walker(dispatch)
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)

        walker.walk(tree.root, tree, ctx, symbol_table)

        assert all(scope.lookup("done_flag") is None for scope in symbol_table.scopes)


def _no_implicit_net_named(symbol_table: SymbolTable, name: str) -> bool:
    return all(
        scope.lookup(name) is None or scope.lookup(name).kind != "implicit_net"
        for scope in symbol_table.scopes
    )


class TestIdentifierHandlerSkipsNamedTypeReference:
    def test_typedef_reference_is_not_registered_as_implicit_net(self) -> None:
        """`byte_t v;` names a typedef'd type, not a variable read."""
        tree = parse_file(DATA / "named_type_reference.sv")
        walker = Walker(dispatch)
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)

        walker.walk(tree.root, tree, ctx, symbol_table)

        assert _no_implicit_net_named(symbol_table, "byte_t")


class TestIdentifierHandlerSkipsInvocationCallee:
    def test_call_site_callee_is_not_registered_as_implicit_net(self) -> None:
        """`c_add(1, 2)` names the DPI function being called, not a variable read."""
        tree = parse_file(DATA / "invocation_callee.sv")
        walker = Walker(dispatch)
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)

        walker.walk(tree.root, tree, ctx, symbol_table)

        assert _no_implicit_net_named(symbol_table, "c_add")


class TestIdentifierHandlerSkipsCoverCrossItems:
    def test_cross_items_are_not_registered_as_implicit_net(self) -> None:
        """`cross cpx, cpy;` names previously-declared coverpoint labels."""
        tree = parse_file(DATA / "cover_cross.sv")
        walker = Walker(dispatch)
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)

        walker.walk(tree.root, tree, ctx, symbol_table)

        assert _no_implicit_net_named(symbol_table, "cpx")
        assert _no_implicit_net_named(symbol_table, "cpy")


class TestIdentifierHandlerSkipsExtendsClauseBaseName:
    def test_base_class_name_is_not_registered_as_implicit_net(self) -> None:
        """`class C extends Base;` names a base class, not a variable read."""
        tree = parse_file(DATA / "extends_clause.sv")
        walker = Walker(dispatch)
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)

        walker.walk(tree.root, tree, ctx, symbol_table)

        assert _no_implicit_net_named(symbol_table, "extends_clause_base")
