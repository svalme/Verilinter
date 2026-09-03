from typing import TYPE_CHECKING

from ...parser.syntax import is_associative_array_dimension_node
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoAssociativeArrayRule(Rule):
    code = "NO_ASSOCIATIVE_ARRAY"
    message = "Use of associative array declarations (arr[*], arr[string], arr[int], etc.) is discouraged in synthesizable RTL; associative arrays are a software-oriented SystemVerilog construct"
    category = "sv_subset"
    default_profiles = ("sv_rtl_subset",)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_associative_array_dimension_node(vnode.raw)
