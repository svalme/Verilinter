from ...parser.syntax import is_endcase_token
from ...walk.context import ContextFlag
from ..base_rule import Rule
from .rule_runner import rule_runner

@rule_runner.register
class DefaultCaseRule(Rule):
    code = "DEFAULT_CASE"
    message = "Case statement missing default case"

    def applies(self, vnode, ctx) -> bool:
        return is_endcase_token(vnode.raw) \
            and ctx.has(ContextFlag.CASE_GENERATE) \
            and not ctx.has(ContextFlag.DEFAULT)
