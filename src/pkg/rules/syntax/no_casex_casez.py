from ...parser.syntax import is_casex_casez_token
from ..base_rule import Rule
from .rule_runner import rule_runner


@rule_runner.register
class NoCaseXCaseZRule(Rule):
    code = "NO_CASEX_CASEZ"
    message = "Use of casex/casez can hide X/Z mismatches"

    def applies(self, vnode, ctx) -> bool:
        return is_casex_casez_token(vnode.raw)
