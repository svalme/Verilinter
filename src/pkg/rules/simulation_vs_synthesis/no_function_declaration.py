from typing import TYPE_CHECKING

from ...parser.syntax import is_function_declaration_node
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoFunctionDeclarationRule(Rule):
    code = "NO_FUNCTION_DECLARATION"
    message = "Use of function declarations is discouraged in this restricted RTL subset"
    category = "rtl_subset"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_function_declaration_node(vnode.raw)
