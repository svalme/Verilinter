from typing import TYPE_CHECKING

from ...parser.syntax import declarator_is_parameter, declarator_name
from ...parser.types import DeclaratorNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner
from ._naming_conventions import is_lower_snake_case

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class SignalNameCasingRule(Rule):
    code = "SIGNAL_NAME_CASING"
    message = "Signal name is not lower_snake_case"
    category = "rtl_style"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    target_node_types = (DeclaratorNode,)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        if not isinstance(vnode.raw, DeclaratorNode):
            return False
        if declarator_is_parameter(ctx):
            return False
        name = declarator_name(vnode.raw)
        return name is not None and not is_lower_snake_case(name)
