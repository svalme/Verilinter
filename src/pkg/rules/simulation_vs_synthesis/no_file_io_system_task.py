from typing import TYPE_CHECKING

from ...parser.syntax import is_file_io_system_task
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoFileIoSystemTaskRule(Rule):
    code = "NO_FILE_IO_SYSTEM_TASK"
    message = "Use of file I/O system tasks ($fopen/$fclose/$fdisplay/$fwrite/$fscanf/etc.) is discouraged in synthesizable RTL; these are simulation-only file operations"
    category = "classic_rtl_exclusion"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_file_io_system_task(vnode.raw)
