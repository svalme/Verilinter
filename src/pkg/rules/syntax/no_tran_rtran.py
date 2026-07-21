from ...parser.syntax import is_tran_rtran_token
from ..base_rule import Rule
from .rule_runner import rule_runner


@rule_runner.register
class NoTranRtranRule(Rule):
    code = "NO_TRAN_RTRAN"
    message = "Use of tran/rtran is discouraged in RTL; prefer explicit connectivity modeling instead"

    def applies(self, vnode, ctx) -> bool:
        return is_tran_rtran_token(vnode.raw)
