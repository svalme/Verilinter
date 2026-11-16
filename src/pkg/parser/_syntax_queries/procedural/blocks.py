"""Walking a procedural block: the identifiers it reads and how deeply statements nest."""
from __future__ import annotations

from collections.abc import Iterator
from ...syntax_kinds import DATA_DECLARATION_KINDS, PARALLEL_BLOCK_STATEMENT_KIND, SEQUENTIAL_BLOCK_STATEMENT_KIND
from ...traversal_guard import guarded_generator
from ...types import ProceduralBlockNode, SyntaxNode
from ..shared import identifier_name


def node_syntax_children(node: object) -> Iterator[SyntaxNode]:
    try:
        children = iter(node)
    except TypeError:
        return
    for child in children:
        if isinstance(child, SyntaxNode):
            yield child


def block_declares_names(raw: object) -> bool:
    """True for a `begin ... end` or `fork ... join` block that declares a variable of its own.

    Such a block is a namespace: `automatic int idx;` in two blocks names two variables."""
    if getattr(raw, "kind", None) not in (SEQUENTIAL_BLOCK_STATEMENT_KIND, PARALLEL_BLOCK_STATEMENT_KIND):
        return False
    return any(getattr(item, "kind", None) in DATA_DECLARATION_KINDS for item in getattr(raw, "items", ()))


def iter_identifier_reads(root: SyntaxNode) -> Iterator[tuple[str, SyntaxNode]]:
    """Yield (name, raw_node) for every read-access identifier under `root`, in document
    order. Does not descend into a nested procedural block."""

    from ...syntax_queries import identifier_name, is_identifier_name_node
    from ..access import _identifier_access_modes_over_ancestors

    if not isinstance(root, SyntaxNode):
        return

    @guarded_generator(max_depth=128)
    def _walk(node: SyntaxNode, ancestors: list[object]) -> Iterator[tuple[str, SyntaxNode]]:
        if is_identifier_name_node(node):
            name = identifier_name(node)
            if name:
                is_read, _is_write = _identifier_access_modes_over_ancestors(ancestors, node)
                if is_read:
                    yield name, node

        ancestors.append(node)
        try:
            for child in node_syntax_children(node):
                if not isinstance(child, ProceduralBlockNode):
                    yield from _walk(child, ancestors)
        finally:
            ancestors.pop()

    yield from _walk(root, [])


@guarded_generator(max_depth=128)
def iter_identifier_nodes(root: SyntaxNode) -> Iterator[tuple[str, SyntaxNode]]:
    from ...syntax_queries import identifier_name, is_identifier_name_node

    if not isinstance(root, SyntaxNode):
        return

    if is_identifier_name_node(root):
        name = identifier_name(root)
        if name:
            yield name, root

    for child in node_syntax_children(root):
        yield from iter_identifier_nodes(child)


def procedural_nesting_depth(ctx: "Context") -> int:
    """Count block/conditional/case-statement ancestors above the current
    position, back to (but not including) the nearest enclosing procedural
    block. The current node itself is excluded -- callers add 1 back in for
    it. Loop statements are deliberately not counted -- `DEEPLY_NESTED_BLOCK`
    only tracks begin/end and if/case nesting, not loop-body nesting.
    """
    from ...syntax_queries import (
        is_block_statement,
        is_case_statement,
        is_conditional_statement,
        is_procedural_block,
    )

    depth = 0
    for ancestor in ctx.iter_ancestors(include_self=False):
        if is_procedural_block(ancestor.raw):
            break
        if is_block_statement(ancestor.raw) or is_conditional_statement(ancestor.raw) or is_case_statement(ancestor.raw):
            depth += 1
    return depth
