from typing import TYPE_CHECKING

from ...parser.syntax import is_xz_equality_comparison
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class XZEqualityComparisonRule(Rule):
    code = "XZ_EQUALITY_COMPARISON"
    message = "==/!= compared against an X/Z literal always evaluates deterministically false/true; use ===/!== or ==?/!=? instead"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, _ctx: "Context") -> bool:
        return is_xz_equality_comparison(vnode.raw)
