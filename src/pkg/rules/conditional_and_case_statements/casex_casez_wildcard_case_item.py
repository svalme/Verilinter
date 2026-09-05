from typing import TYPE_CHECKING

from ...parser.syntax import has_casex_casez_wildcard_case_item
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class CasexCasezWildcardCaseItemRule(Rule):
    code = "CASEX_CASEZ_WILDCARD_CASE_ITEM"
    message = "casex/casez case item is composed entirely of wildcard bits and silently matches every value"
    category = "rtl_correctness"
    default_profiles = ("legacy_verilog",)

    def applies(self, vnode: BaseVNode, _ctx: "Context") -> bool:
        return has_casex_casez_wildcard_case_item(vnode.raw)
