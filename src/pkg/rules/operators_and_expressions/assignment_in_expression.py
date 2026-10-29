from typing import TYPE_CHECKING

from ...parser.syntax import is_assignment_inside_expression
from ...parser.types import BinaryExpressionNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class AssignmentInExpressionRule(Rule):
    code = "ASSIGNEQEXPR"
    message = "Assignment '=' inside expression; was '==' intended, or use a separate statement"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    target_node_types = (BinaryExpressionNode,)

    def applies(self, vnode: BaseVNode, _ctx: "Context") -> bool:
        return is_assignment_inside_expression(vnode.raw)
