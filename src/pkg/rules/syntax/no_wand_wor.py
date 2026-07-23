from typing import TYPE_CHECKING

from ...parser.syntax import is_wand_wor_token
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoWandWorRule(Rule):
    code = "NO_WAND_WOR"
    message = "Use of wand/wor is discouraged in RTL; prefer explicit logic composition instead"

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_wand_wor_token(vnode.raw)
