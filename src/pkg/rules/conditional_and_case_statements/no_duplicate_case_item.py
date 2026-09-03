from ...parser.syntax import case_item_expressions, case_statement_items, is_case_statement, source_text_for_node
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner


def _has_duplicate_case_item(vnode: BaseVNode) -> bool:
    seen: set[str] = set()

    for item in case_statement_items(vnode.raw):
        for expression in case_item_expressions(item):
            key = source_text_for_node(expression, vnode.tree)
            if key is None:
                continue
            if key in seen:
                return True
            seen.add(key)

    return False


@rule_runner.register
class NoDuplicateCaseItemRule(Rule):
    code = "NO_DUPLICATE_CASE_ITEM"
    message = "Duplicate case item detected"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, _ctx: object) -> bool:
        return is_case_statement(vnode.raw) and _has_duplicate_case_item(vnode)
