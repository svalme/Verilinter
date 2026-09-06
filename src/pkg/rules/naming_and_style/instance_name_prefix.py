from typing import TYPE_CHECKING

from ...parser.syntax import hierarchical_instance_name
from ...parser.types import HierarchicalInstanceNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class InstanceNamePrefixRule(Rule):
    code = "INSTANCE_NAME_PREFIX"
    message = "Instance name missing expected prefix (u_/i_)"
    category = "rtl_style"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, _ctx: "Context") -> bool:
        if not isinstance(vnode.raw, HierarchicalInstanceNode):
            return False
        name = hierarchical_instance_name(vnode.raw)
        return name is not None and not name.startswith(("u_", "i_"))
