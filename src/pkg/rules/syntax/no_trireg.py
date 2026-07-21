from ...parser.syntax import is_trireg_token
from ..base_rule import Rule
from .rule_runner import rule_runner


@rule_runner.register
class NoTriregRule(Rule):
    code = "NO_TRIREG"
    message = "Use of trireg is discouraged in RTL; prefer explicit storage and connectivity modeling instead"

    def applies(self, vnode, ctx) -> bool:
        return is_trireg_token(vnode.raw)
