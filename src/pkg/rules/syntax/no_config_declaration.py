from typing import TYPE_CHECKING

from ...parser.syntax import is_config_declaration_node
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoConfigDeclarationRule(Rule):
    code = "NO_CONFIG_DECLARATION"
    message = "Use of config declarations is discouraged in synthesizable RTL; library/config binding is a compilation-flow concern, not design intent"
    category = "classic_rtl_exclusion"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_config_declaration_node(vnode.raw)
