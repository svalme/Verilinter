from typing import TYPE_CHECKING

from ...parser.syntax import is_specify_block_node
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoSpecifyBlockRule(Rule):
    code = "NO_SPECIFY_BLOCK"
    message = "Use of specify blocks is discouraged in synthesizable RTL; pin-to-pin timing modeling is not synthesizable"
    category = "classic_rtl_exclusion"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_specify_block_node(vnode.raw)
