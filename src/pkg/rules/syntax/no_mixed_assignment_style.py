from typing import TYPE_CHECKING

from ...parser.syntax import is_assignment_expression, is_procedural_block, iter_assignment_nodes
from ...parser.types import SyntaxNode
from ...vnodes.base_vnode import BaseVNode
from ...vnodes.syntax_vnode import SyntaxVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


def _enclosing_procedural_block(ctx: "Context") -> SyntaxVNode | None:
    for ancestor in reversed(ctx.stack):
        if is_procedural_block(ancestor.raw):
            return ancestor
    return None


def _mix_trigger_node(block: SyntaxVNode) -> SyntaxNode | None:
    seen_kinds: set[object] = set()

    for node in iter_assignment_nodes(block.raw):
        if node.kind not in seen_kinds and seen_kinds:
            return node
        seen_kinds.add(node.kind)

    return None


@rule_runner.register
class NoMixedAssignmentStyleRule(Rule):
    code = "NO_MIXED_ASSIGNMENT_STYLE"
    message = "Mixed blocking and non-blocking assignments used in the same procedural block"

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        if not is_assignment_expression(vnode.raw):
            return False

        block = _enclosing_procedural_block(ctx)
        if block is None:
            return False

        trigger = _mix_trigger_node(block)
        return trigger is vnode.raw
