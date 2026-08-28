from typing import TYPE_CHECKING

from ...parser.syntax import is_random_system_function
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoRandomSystemFunctionRule(Rule):
    code = "NO_RANDOM_SYSTEM_FUNCTION"
    message = "Use of $random/$urandom/$urandom_range is discouraged in synthesizable RTL; these are simulation-only randomization functions"
    category = "classic_rtl_exclusion"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_random_system_function(vnode.raw)
