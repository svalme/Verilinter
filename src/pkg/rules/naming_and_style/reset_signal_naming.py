from typing import TYPE_CHECKING

from ...parser.syntax import async_reset_signal_edges
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


def _has_polarity_mismatch(vnode: BaseVNode) -> bool:
    for name, edge in async_reset_signal_edges(vnode.raw).items():
        suffixed = name.endswith("_n") or name.endswith("_b")
        if edge == "negedge" and not suffixed:
            return True
        if edge == "posedge" and suffixed:
            return True
    return False


@rule_runner.register
class ResetSignalNamingRule(Rule):
    code = "RESET_SIGNAL_NAMING"
    message = "Sensitivity-list signal's edge polarity does not match its _n/_b suffix convention"
    category = "rtl_style"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, _ctx: "Context") -> bool:
        return _has_polarity_mismatch(vnode)
