from typing import TYPE_CHECKING

from ...parser.syntax import is_real_type_node
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoRealTypeRule(Rule):
    code = "NO_REAL_TYPE"
    message = "Use of real/shortreal/realtime types is discouraged in synthesizable RTL; floating-point types are not synthesizable"
    category = "classic_rtl_exclusion"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_real_type_node(vnode.raw)
