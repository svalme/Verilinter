from ...parser.syntax import has_case_overlapping_items, is_case_statement
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner


@rule_runner.register
class CaseOverlappingItemsRule(Rule):
    code = "CASE_OVERLAPPING_ITEMS"
    message = "Case statement contains duplicate or overlapping case items"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    overlaps_with = ("NO_DUPLICATE_CASE_ITEM",)

    def applies(self, vnode: BaseVNode, _ctx: object) -> bool:
        return is_case_statement(vnode.raw) and has_case_overlapping_items(vnode.raw)
