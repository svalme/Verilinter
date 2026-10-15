from typing import TYPE_CHECKING, Any

from ...parser.syntax import is_empty_non_ansi_port, is_empty_port_connection
from ...parser.types import EmptyNonAnsiPortNode, EmptyPortConnectionNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NullPortRule(Rule):
    code = "NULLPORT"
    message = "Null port on module (perhaps extraneous comma)"
    category = "module_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    target_node_types = (EmptyNonAnsiPortNode, EmptyPortConnectionNode)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_empty_non_ansi_port(vnode.raw) or is_empty_port_connection(vnode.raw)

    def report(self, vnode: BaseVNode) -> dict[str, Any]:
        loc = vnode.location or {}
        if is_empty_port_connection(vnode.raw):
            msg = "Empty (null) port connection in module instance (perhaps extraneous comma)"
        else:
            msg = "Null port on module (perhaps extraneous comma)"
        diagnostic: dict[str, Any] = {
            "code": self.code,
            "line": loc.get("line", 0),
            "col": loc.get("col", 0),
            "message": msg,
        }
        if "file" in loc:
            diagnostic["file"] = loc["file"]
        return diagnostic
