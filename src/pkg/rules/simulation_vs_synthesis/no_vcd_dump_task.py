from typing import TYPE_CHECKING

from ...parser.syntax import is_vcd_dump_task
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoVcdDumpTaskRule(Rule):
    code = "NO_VCD_DUMP_TASK"
    message = "Use of $dumpfile/$dumpvars-family VCD dump system tasks is discouraged in synthesizable RTL; these are simulation-only waveform tracing tasks"
    category = "classic_rtl_exclusion"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_vcd_dump_task(vnode.raw)
