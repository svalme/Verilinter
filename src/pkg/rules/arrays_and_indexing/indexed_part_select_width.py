from typing import TYPE_CHECKING

from ...parser.syntax import is_illegal_indexed_part_select_width
from ...parser.types import RangeSelectNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class IndexedPartSelectWidthRule(Rule):
    code = "INDEXED_PART_SELECT_WIDTH"
    message = "Width of indexed part-select (+: / -:) must be a constant positive integer expression"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    target_node_types = (RangeSelectNode,)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        try:
            scope = ctx.scope()
        except Exception:
            scope = None
        return is_illegal_indexed_part_select_width(vnode.raw, scope=scope)
