import pyslang as sl

from ..vnode.base_vnode import BaseVNode
from ..ast.context import Context, ContextFlag
from .base_rule import Rule
from .rule_runner import rule_runner

@rule_runner.register
class DefaultCaseRule(Rule):
    code = "DEFAULT_CASE"
    message = "Case statement missing default case"

    def applies(self, vnode, ctx) -> bool:
        return vnode.raw.kind == sl.TokenKind.EndCaseKeyword \
            and ctx.has(ContextFlag.CASE_GENERATE) \
            and not ctx.has(ContextFlag.DEFAULT)


    
