from typing import TYPE_CHECKING

from ...parser.syntax import is_casex_casez_token
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoCaseXCaseZRule(Rule):
    code = "NO_CASEX_CASEZ"
    message = "Use of casex/casez can hide X/Z mismatches"

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_casex_casez_token(vnode.raw)
