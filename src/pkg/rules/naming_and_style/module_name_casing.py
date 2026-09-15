from typing import TYPE_CHECKING

from ...parser.syntax import is_module_declaration_node, module_declaration_name
from ...parser.types import ModuleDeclarationNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner
from ._naming_conventions import is_lower_snake_case

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class ModuleNameCasingRule(Rule):
    code = "MODULE_NAME_CASING"
    message = "Module name is not lower_snake_case"
    category = "rtl_style"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    target_node_types = (ModuleDeclarationNode,)

    def applies(self, vnode: BaseVNode, _ctx: "Context") -> bool:
        if not is_module_declaration_node(vnode.raw):
            return False
        name = module_declaration_name(vnode.raw)
        return name is not None and not is_lower_snake_case(name)
