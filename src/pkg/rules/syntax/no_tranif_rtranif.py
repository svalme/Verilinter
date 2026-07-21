from ...parser.syntax import is_tranif_rtranif_token
from ..base_rule import Rule
from .rule_runner import rule_runner


@rule_runner.register
class NoTranifRtranifRule(Rule):
    code = "NO_TRANIF_RTRANIF"
    message = "Use of tranif/rtranif is discouraged in RTL; prefer explicit connectivity modeling instead"

    def applies(self, vnode, ctx) -> bool:
        return is_tranif_rtranif_token(vnode.raw)
