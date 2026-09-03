from typing import TYPE_CHECKING

from ...parser.syntax import is_extra_module_declaration_in_file
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class OneModulePerFileRule(Rule):
    code = "ONE_MODULE_PER_FILE"
    message = "File declares more than one module; keep one module per file"
    category = "module_style"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_extra_module_declaration_in_file(vnode.raw, vnode.tree)
