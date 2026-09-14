from typing import TYPE_CHECKING

from ...parser.syntax import declarator_is_port, declarator_name, declarator_port_direction
from ...parser.types import DeclaratorNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context

_EXPECTED_SUFFIX_BY_DIRECTION = {"input": "_i", "output": "_o", "inout": "_io"}


@rule_runner.register
class PortDirectionSuffixRule(Rule):
    code = "PORT_DIRECTION_SUFFIX"
    message = "Port name missing expected direction suffix (_i/_o/_io)"
    category = "rtl_style"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        if ctx.scope().kind in ("function", "task"):
            return False
        if not isinstance(vnode.raw, DeclaratorNode):
            return False
        if not declarator_is_port(ctx):
            return False
        direction = declarator_port_direction(ctx)
        suffix = _EXPECTED_SUFFIX_BY_DIRECTION.get(direction or "")
        if suffix is None:
            return False
        name = declarator_name(vnode.raw)
        return name is not None and not name.endswith(suffix)
