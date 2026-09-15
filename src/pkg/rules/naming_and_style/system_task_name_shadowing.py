from typing import TYPE_CHECKING

from ...parser.syntax import ALL_SYSTEM_TASK_NAMES, declarator_name
from ...parser.types import DeclaratorNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class SystemTaskNameShadowingRule(Rule):
    code = "SYSTEM_TASK_NAME_SHADOWING"
    message = "Identifier shadows a built-in system task/function name"
    category = "rtl_style"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    target_node_types = (DeclaratorNode,)

    def applies(self, vnode: BaseVNode, _ctx: "Context") -> bool:
        if not isinstance(vnode.raw, DeclaratorNode):
            return False
        name = declarator_name(vnode.raw)
        return name is not None and name in ALL_SYSTEM_TASK_NAMES
