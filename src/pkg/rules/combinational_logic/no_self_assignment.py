from ...parser.syntax import assignment_record, same_expression, unwrap_parentheses
from ...parser.types import BinaryExpressionNode
from ...semantic.models.assignment_record import AssignmentKind
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner


@rule_runner.register
class NoSelfAssignmentRule(Rule):
    code = "NO_SELF_ASSIGNMENT"
    message = "Self-assignment detected"
    category = "rtl_style"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    target_node_types = (BinaryExpressionNode,)

    def applies(self, vnode: BaseVNode, ctx: object) -> bool:
        record = assignment_record(ctx, vnode)
        if record is None or record.kind in (AssignmentKind.COMPOUND, AssignmentKind.INITIALIZER):
            return False
        if len(record.targets) != 1 or record.targets[0].reference is None or record.rhs is None:
            return False
        return same_expression(record.targets[0].reference, unwrap_parentheses(record.rhs))
