from src.pkg.parser.parse import parse_text
from src.pkg.parser.syntax import (
    assignment_left,
    contains_descendant,
    declarator_name,
    hierarchical_instance_name,
    identifier_access_modes,
    identifier_is_assignment_lhs,
    identifier_name,
    instantiation_type_name,
    is_assignment_expression,
    module_declaration_name,
    procedural_block_sensitivity_names,
)
from src.pkg.parser.types import (
    DeclaratorNode,
    HierarchicalInstanceNode,
    HierarchyInstantiationNode,
    IdentifierNameNode,
    IdentifierSelectNameNode,
    ModuleDeclarationNode,
    ProceduralBlockNode,
    SyntaxNode,
)
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *


def _walk_collect(code: str):
    tree = parse_text(code)
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)
    walker.walk(tree.root, tree, ctx, symbol_table)
    return walker.results


def _find_first(node, predicate):
    if predicate(node):
        return node

    if hasattr(node, "__iter__"):
        for child in node:
            if isinstance(child, SyntaxNode):
                found = _find_first(child, predicate)
                if found is not None:
                    return found

    return None


class TestSvAdapter:
    def test_name_accessors_extract_common_parser_names(self) -> None:
        tree = parse_text(
            """
            module top;
              logic a;
              foo_mod u_foo();
            endmodule
            """
        )

        module_node = _find_first(tree.root, lambda node: isinstance(node, ModuleDeclarationNode))
        declarator_node = _find_first(tree.root, lambda node: isinstance(node, DeclaratorNode))
        instantiation_node = _find_first(tree.root, lambda node: isinstance(node, HierarchyInstantiationNode))
        instance_node = _find_first(tree.root, lambda node: isinstance(node, HierarchicalInstanceNode))

        assert module_node is not None
        assert declarator_node is not None
        assert instantiation_node is not None
        assert instance_node is not None

        assert module_declaration_name(module_node) == "top"
        assert declarator_name(declarator_node) == "a"
        assert instantiation_type_name(instantiation_node) == "foo_mod"
        assert hierarchical_instance_name(instance_node) == "u_foo"

    def test_assignment_left_returns_left_expression(self) -> None:
        tree = parse_text(
            """
            module top;
              logic x, y;
              initial x = y;
            endmodule
            """
        )
        assign = _find_first(tree.root, is_assignment_expression)
        assert assign is not None
        assert assignment_left(assign) is assign.left

    def test_contains_descendant_finds_nested_identifier(self) -> None:
        tree = parse_text(
            """
            module top;
              logic [7:0] a;
              initial a[0] = 1'b0;
            endmodule
            """
        )
        assign = _find_first(tree.root, is_assignment_expression)
        target = _find_first(
            tree.root,
            lambda node: isinstance(node, IdentifierSelectNameNode) and identifier_name(node) == "a",
        )
        left = assign.left if assign is not None else None
        assert assign is not None and left is not None and target is not None
        assert contains_descendant(left, target) is True

    def test_identifier_is_assignment_lhs_for_indexed_target(self) -> None:
        results = _walk_collect(
            """
            module top;
              logic [7:0] a, b;
              initial a[0] = b[0];
            endmodule
            """
        )

        lhs_identifier = next(
            vnode for vnode, ctx in results if isinstance(vnode.raw, IdentifierSelectNameNode) and identifier_name(vnode.raw) == "a"
        )
        lhs_ctx = next(
            ctx for vnode, ctx in results if isinstance(vnode.raw, IdentifierSelectNameNode) and identifier_name(vnode.raw) == "a"
        )
        rhs_identifier = next(
            vnode for vnode, ctx in results if isinstance(vnode.raw, IdentifierSelectNameNode) and identifier_name(vnode.raw) == "b"
        )
        rhs_ctx = next(
            ctx for vnode, ctx in results if isinstance(vnode.raw, IdentifierSelectNameNode) and identifier_name(vnode.raw) == "b"
        )

        assert identifier_is_assignment_lhs(lhs_ctx, lhs_identifier.raw) is True
        assert identifier_is_assignment_lhs(rhs_ctx, rhs_identifier.raw) is False

    def test_identifier_access_modes_marks_compound_assignment_as_read_and_write(self) -> None:
        results = _walk_collect(
            """
            module top;
              int x;
              initial x += 1;
            endmodule
            """
        )

        identifier_vnode, identifier_ctx = next(
            (vnode, ctx)
            for vnode, ctx in results
            if isinstance(vnode.raw, IdentifierNameNode) and identifier_name(vnode.raw) == "x"
        )

        assert identifier_access_modes(identifier_ctx, identifier_vnode.raw) == (True, True)

    def test_identifier_access_modes_marks_increment_as_read_and_write(self) -> None:
        results = _walk_collect(
            """
            module top;
              int x;
              initial ++x;
            endmodule
            """
        )

        identifier_vnode, identifier_ctx = next(
            (vnode, ctx)
            for vnode, ctx in results
            if isinstance(vnode.raw, IdentifierNameNode) and identifier_name(vnode.raw) == "x"
        )

        assert identifier_access_modes(identifier_ctx, identifier_vnode.raw) == (True, True)

    def test_identifier_access_modes_treats_lhs_selector_as_read(self) -> None:
        results = _walk_collect(
            """
            module top;
              logic [3:0] y;
              logic [1:0] b;
              logic c;
              initial y[b] = c;
            endmodule
            """
        )

        identifier_vnode, identifier_ctx = next(
            (vnode, ctx)
            for vnode, ctx in results
            if isinstance(vnode.raw, IdentifierNameNode) and identifier_name(vnode.raw) == "b"
        )

        assert identifier_access_modes(identifier_ctx, identifier_vnode.raw) == (True, False)

    def test_procedural_block_sensitivity_names_collects_index_base_and_selector(self) -> None:
        tree = parse_text(
            """
            module top(input logic [3:0] a, input logic [1:0] sel, output logic y);
              always @(a[sel]) begin
                y = a[sel];
              end
            endmodule
            """
        )

        always_block = _find_first(tree.root, lambda node: isinstance(node, ProceduralBlockNode))

        assert always_block is not None
        assert procedural_block_sensitivity_names(always_block) == {"a", "sel"}
