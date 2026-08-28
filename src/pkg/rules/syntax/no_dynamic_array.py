from typing import TYPE_CHECKING

from ...parser.syntax import is_dynamic_array_dimension_node
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoDynamicArrayRule(Rule):
    code = "NO_DYNAMIC_ARRAY"
    message = "Use of dynamic array declarations (arr[]) is discouraged in synthesizable RTL; dynamic arrays are a software-oriented SystemVerilog construct"
    category = "sv_subset"
    default_profiles = ("sv_rtl_subset",)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_dynamic_array_dimension_node(vnode.raw)
