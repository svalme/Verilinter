from typing import TYPE_CHECKING

from ...parser.syntax import comparison_operands, identifier_name, unwrap_parentheses
from ...parser.types import BinaryExpressionNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class SelfComparisonRule(Rule):
    code = "SELF_COMPARISON"
    message = "Signal is compared with itself"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    target_node_types = (BinaryExpressionNode,)

    def applies(self, vnode: BaseVNode, _ctx: "Context") -> bool:
        operands = comparison_operands(vnode.raw)
        if operands is None:
            return False
        left, right, _op = operands
        if left is None or right is None:
            return False
        left_name = identifier_name(unwrap_parentheses(left))
        return left_name is not None and left_name == identifier_name(unwrap_parentheses(right))
