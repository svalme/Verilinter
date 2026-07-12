from ...parser.syntax import is_unique_priority_case_token
from ..base_rule import Rule
from .rule_runner import rule_runner


@rule_runner.register
class NoUniquePriorityCaseRule(Rule):
    code = "NO_UNIQUE_PRIORITY_CASE"
    message = "Use of unique/priority case can overstate case completeness or exclusivity"

    def applies(self, vnode, ctx) -> bool:
        return is_unique_priority_case_token(vnode.raw)
