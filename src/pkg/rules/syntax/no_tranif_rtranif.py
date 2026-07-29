from typing import TYPE_CHECKING

from ...parser.syntax import is_tranif_rtranif_token
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoTranifRtranifRule(Rule):
    code = "NO_TRANIF_RTRANIF"
    message = "Use of tranif/rtranif is discouraged in RTL; prefer explicit connectivity modeling instead"
    category = "classic_rtl_exclusion"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_tranif_rtranif_token(vnode.raw)
