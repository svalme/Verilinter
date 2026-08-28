from typing import TYPE_CHECKING

from ...parser.syntax import is_unsized_literal_in_flagged_value_context
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoUnsizedLiteralRule(Rule):
    code = "NO_UNSIZED_LITERAL"
    message = "Unsized decimal literal used as an assigned value; its width will be inferred and may mismatch the target"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_unsized_literal_in_flagged_value_context(vnode.raw)
