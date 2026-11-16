"""Block-local temporaries: variables a combinational block uses as scratch space.

A variable that nothing outside its always block reads or writes, and that each read inside the block follows
an unconditional write to, never carries a value from one evaluation to the next, so it infers no latch.
"""
from __future__ import annotations

from ...traversal_guard import guarded_traversal
from ...types import SyntaxNode
from ..access import syntax_identifier_access_modes
from ..assignment_records import assignment_target_names
from ..conditional_shapes import expression_statement_expression, is_block_statement, is_conditional_statement, iter_statement_nodes
from ..keywords_and_tokens import is_case_statement
from ..module_file import is_module_declaration_node
from ..module_ports import module_port_directions
from .blocks import iter_identifier_nodes


@guarded_traversal(max_depth=64, default=set())
def unconditional_assignment_targets(statement: SyntaxNode) -> set[str]:
    """The names a statement assigns on every path through it, looking into plain begin-end blocks but not
    into conditionals or case statements."""
    if is_block_statement(statement):
        names: set[str] = set()
        for child in iter_statement_nodes(statement):
            if is_conditional_statement(child) or is_case_statement(child):
                continue
            names.update(unconditional_assignment_targets(child))
        return names

    expr = expression_statement_expression(statement)
    if expr is None:
        return set()

    return set(assignment_target_names(expr))


_MAX_PARENT_STEPS = 256


def _is_inside(node: SyntaxNode, container: SyntaxNode) -> bool:
    current: object | None = node
    for _ in range(_MAX_PARENT_STEPS):
        if current is container:
            return True
        current = getattr(current, "parent", None)
        if current is None:
            return False
    return False


def _enclosing_module(node: SyntaxNode) -> SyntaxNode | None:
    current: object | None = node
    for _ in range(_MAX_PARENT_STEPS):
        if is_module_declaration_node(current):
            return current  # type: ignore[return-value]
        current = getattr(current, "parent", None)
        if current is None:
            return None
    return None


def _written_before_in_enclosing_lists(read: SyntaxNode, name: str, block: SyntaxNode) -> bool:
    """True when a statement ahead of `read`, in the statement list that holds it or in one that encloses
    that, assigns `name` on every path."""
    child: object = read
    current: object | None = getattr(read, "parent", None)
    for _ in range(_MAX_PARENT_STEPS):
        if current is None or current is block:
            return False
        if is_block_statement(current):
            for statement in iter_statement_nodes(current):
                if statement is child:
                    break
                if name in unconditional_assignment_targets(statement):
                    return True
        child, current = current, getattr(current, "parent", None)
    return False


def is_block_local_temporary(block: SyntaxNode, name: str) -> bool:
    """True when `name` is read and written only inside `block`, and every read inside it follows an
    unconditional write on the same path. A port is never a temporary: it is observed outside the module."""
    module = _enclosing_module(block)
    if module is None:
        return False
    if any(port_name == name for port_name, _direction in module_port_directions(module)):
        return False
    for occurrence_name, occurrence in iter_identifier_nodes(module):
        if occurrence_name != name:
            continue
        reads, writes = syntax_identifier_access_modes(occurrence)
        if not _is_inside(occurrence, block):
            if reads or writes:
                return False
            continue
        if reads and not _written_before_in_enclosing_lists(occurrence, name, block):
            return False
    return True
