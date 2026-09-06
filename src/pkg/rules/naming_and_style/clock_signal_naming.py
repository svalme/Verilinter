from typing import TYPE_CHECKING

from ...parser.syntax import sync_clock_signal_name
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class ClockSignalNamingRule(Rule):
    code = "CLOCK_SIGNAL_NAMING"
    message = "Clock signal is not named 'clk' or suffixed '_clk'"
    category = "rtl_style"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, _ctx: "Context") -> bool:
        name = sync_clock_signal_name(vnode.raw)
        return name is not None and name != "clk" and not name.endswith("_clk")
