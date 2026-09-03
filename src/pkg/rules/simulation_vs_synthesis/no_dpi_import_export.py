from typing import TYPE_CHECKING

from ...parser.syntax import is_dpi_import_export_node
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoDpiImportExportRule(Rule):
    code = "NO_DPI_IMPORT_EXPORT"
    message = "Use of DPI import/export declarations is discouraged in synthesizable RTL; DPI is a simulation/foreign-code bridge"
    category = "sv_subset"
    default_profiles = ("sv_rtl_subset",)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_dpi_import_export_node(vnode.raw)
