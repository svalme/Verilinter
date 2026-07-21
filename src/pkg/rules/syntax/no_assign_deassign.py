from ...parser.syntax import is_assign_deassign_token
from ..base_rule import Rule
from .rule_runner import rule_runner


@rule_runner.register
class NoAssignDeassignRule(Rule):
    code = "NO_ASSIGN_DEASSIGN"
    message = "Use of assign/deassign is discouraged in RTL; prefer explicit continuous or procedural intent"

    def applies(self, vnode, ctx) -> bool:
        return is_assign_deassign_token(vnode.raw)
