from ...parser.syntax import is_internal_inout_port_declaration
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner


@rule_runner.register
class NoInternalInoutRule(Rule):
    code = "NO_INOUT_INTERNAL"
    message = "Internal inout declarations are not allowed"

    def applies(self, vnode: BaseVNode, ctx) -> bool:
        return is_internal_inout_port_declaration(vnode.raw)
