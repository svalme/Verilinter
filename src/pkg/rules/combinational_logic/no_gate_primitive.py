from typing import TYPE_CHECKING

from ...parser.syntax import is_gate_primitive_token
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoGatePrimitiveRule(Rule):
    code = "NO_GATE_PRIMITIVE"
    message = "Use of gate-level primitives is discouraged in RTL; prefer behavioral or operator-level modeling"
    category = "classic_rtl_exclusion"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_gate_primitive_token(vnode.raw, ctx)
