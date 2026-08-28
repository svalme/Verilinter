from typing import TYPE_CHECKING

from ...parser.syntax import is_virtual_interface_type_node
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoVirtualInterfaceRule(Rule):
    code = "NO_VIRTUAL_INTERFACE"
    message = "Use of virtual interface declarations is discouraged in synthesizable RTL; virtual interfaces are a testbench-only construct"
    category = "sv_subset"
    default_profiles = ("sv_rtl_subset",)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_virtual_interface_type_node(vnode.raw)
