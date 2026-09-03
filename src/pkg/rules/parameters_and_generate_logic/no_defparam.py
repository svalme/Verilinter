from typing import TYPE_CHECKING

from ...parser.syntax import is_defparam_token
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoDefparamRule(Rule):
    code = "NO_DEFPARAM"
    message = "Use of defparam is discouraged; prefer explicit parameter overrides at instantiation"
    category = "classic_rtl_exclusion"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_defparam_token(vnode.raw)
