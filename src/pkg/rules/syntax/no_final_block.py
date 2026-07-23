from typing import TYPE_CHECKING

from ...parser.syntax import is_final_block
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoFinalBlockRule(Rule):
    code = "NO_FINAL_BLOCK"
    message = "Use of final blocks is usually not appropriate in synthesizable RTL"

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_final_block(vnode.raw)
