from typing import TYPE_CHECKING

from ...parser.syntax import is_string_type_node
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoStringTypeRule(Rule):
    code = "NO_STRING_TYPE"
    message = "Use of string type is discouraged in synthesizable RTL; string is a simulation-only data type"
    category = "sv_subset"
    default_profiles = ("sv_rtl_subset",)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_string_type_node(vnode.raw)
