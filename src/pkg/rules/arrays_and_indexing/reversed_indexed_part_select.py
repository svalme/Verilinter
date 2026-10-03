from typing import TYPE_CHECKING

from ...parser.syntax import is_reversed_indexed_part_select
from ...parser.types import RangeSelectNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class ReversedIndexedPartSelectRule(Rule):
    code = "REVERSED_INDEXED_PART_SELECT"
    message = "Reversed indexed part-select operator ':+` or `:-` used instead of `+:` or `-:`"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    target_node_types = (RangeSelectNode,)

    def applies(self, vnode: BaseVNode, _ctx: "Context") -> bool:
        return is_reversed_indexed_part_select(vnode.raw)
