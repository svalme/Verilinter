from typing import TYPE_CHECKING

from ...parser.syntax import is_internal_inout_port_declaration
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoInternalInoutRule(Rule):
    code = "NO_INOUT_INTERNAL"
    message = "Internal inout declarations are not allowed"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_internal_inout_port_declaration(vnode.raw)
