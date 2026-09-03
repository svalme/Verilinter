from typing import TYPE_CHECKING

from ...parser.syntax import is_missing_timescale_directive
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class MissingTimescaleDirectiveRule(Rule):
    code = "MISSING_TIMESCALE_DIRECTIVE"
    message = "File has no `timescale directive before its first module declaration"
    category = "rtl_subset"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_missing_timescale_directive(vnode.raw, vnode.tree)
