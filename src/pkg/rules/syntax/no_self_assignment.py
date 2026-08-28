from ...parser.syntax import assignment_left, assignment_right, identifier_name, is_assignment_expression
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner


@rule_runner.register
class NoSelfAssignmentRule(Rule):
    code = "NO_SELF_ASSIGNMENT"
    message = "Self-assignment detected"
    category = "rtl_style"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, _ctx: object) -> bool:
        if not is_assignment_expression(vnode.raw):
            return False

        left = assignment_left(vnode.raw)
        right = assignment_right(vnode.raw)
        if left is None or right is None:
            return False

        left_name = identifier_name(left)
        right_name = identifier_name(right)
        return left_name is not None and left_name == right_name
