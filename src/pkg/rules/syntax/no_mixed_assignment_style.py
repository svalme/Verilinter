from ...parser.syntax import ASSIGNMENT_KINDS, is_assignment_expression, is_procedural_block, iter_assignment_nodes
from ...vnodes.syntax_vnode import SyntaxVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

def _enclosing_procedural_block(ctx) -> SyntaxVNode | None:
    for ancestor in reversed(ctx.stack):
        if is_procedural_block(ancestor.raw):
            return ancestor
    return None


def _mix_trigger_node(block: SyntaxVNode):
    seen_kinds = set()

    for node in iter_assignment_nodes(block.raw):
        if node.kind not in seen_kinds and seen_kinds:
            return node
        seen_kinds.add(node.kind)

    return None


@rule_runner.register
class NoMixedAssignmentStyleRule(Rule):
    code = "NO_MIXED_ASSIGNMENT_STYLE"
    message = "Mixed blocking and non-blocking assignments used in the same procedural block"

    def applies(self, vnode, ctx) -> bool:
        if not is_assignment_expression(vnode.raw):
            return False

        block = _enclosing_procedural_block(ctx)
        if block is None:
            return False

        trigger = _mix_trigger_node(block)
        return trigger is vnode.raw
