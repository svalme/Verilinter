from typing import TYPE_CHECKING

from ...parser.syntax import is_multi_clock_procedural_block, is_procedural_block
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class MultiClockProceduralBlockRule(Rule):
    code = "MULTI_CLOCK_PROCEDURAL_BLOCK"
    message = "Procedural block has multiple clock signals or unhandled edge triggers"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        if not is_procedural_block(vnode.raw):
            return False
        return is_multi_clock_procedural_block(vnode.raw)
