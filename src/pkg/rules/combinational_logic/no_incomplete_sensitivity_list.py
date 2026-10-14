from typing import TYPE_CHECKING, Any

from ...parser.syntax import identifier_name, is_identifier_name_node
from ...parser.types import IDENTIFIER_NAME_NODE_TYPES
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoIncompleteSensitivityListRule(Rule):
    code = "NO_INCOMPLETE_SENSITIVITY_LIST"
    message = "Signal is read in this block but missing from its explicit sensitivity list"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    target_node_types = IDENTIFIER_NAME_NODE_TYPES

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        if not is_identifier_name_node(vnode.raw):
            return False

        # Computed once per enclosing block by ProceduralBlockHandler rather
        # than re-derived here per node.
        block_frame = getattr(ctx, "block_frame", None)
        missing = (
            block_frame.missing_sensitivity
            if block_frame is not None
            else getattr(ctx, "data", {}).get("missing_sensitivity", {})
        )
        return any(node is vnode.raw for node in missing.values())

    def report(self, vnode: BaseVNode) -> dict[str, Any]:
        diagnostic = super().report(vnode)
        name = identifier_name(vnode.raw)
        diagnostic["message"] = f"Signal '{name}' is read in this block but missing from its sensitivity list"
        return diagnostic
