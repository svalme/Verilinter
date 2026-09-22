from ...parser.syntax import is_conditional_constant_expression
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner


@rule_runner.register
class ConditionalConstantExpressionRule(Rule):
    code = "CONDITIONAL_CONSTANT_EXPRESSION"
    message = "Conditional statement has a constant expression predicate"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, _ctx: object) -> bool:
        return is_conditional_constant_expression(vnode.raw)
