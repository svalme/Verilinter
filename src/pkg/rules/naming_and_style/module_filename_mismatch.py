from typing import TYPE_CHECKING

from ...parser.syntax import is_module_filename_mismatch
from ...parser.types import ModuleDeclarationNode
from ...semantic.scope import enclosing_module_scope
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class ModuleFilenameMismatchRule(Rule):
    code = "MODULE_FILENAME_MISMATCH"
    message = "No module in this file matches its filename; rename the file or the module for consistency"
    category = "module_style"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    target_node_types = (ModuleDeclarationNode,)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        scope = enclosing_module_scope(ctx.scope())
        current_file = scope.file if scope is not None else None
        return is_module_filename_mismatch(vnode.raw, vnode.tree, current_file)
