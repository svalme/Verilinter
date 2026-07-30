from typing import TYPE_CHECKING, Any

from ...parser.syntax import (
    ALWAYS_BLOCK_KIND,
    identifier_name,
    iter_identifier_reads,
    procedural_block_sensitivity_names,
    procedural_block_statement,
)
from ...parser.types import IdentifierNameNode, IdentifierSelectNameNode, SyntaxNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


def _enclosing_always_block(ctx: "Context") -> BaseVNode | None:
    for ancestor in reversed(ctx.stack):
        if getattr(ancestor.raw, "kind", None) == ALWAYS_BLOCK_KIND:
            return ancestor
    return None


def _missing_sensitivity_trigger_nodes(block_raw: object) -> dict[str, SyntaxNode]:
    """For a plain `always` block with an explicit sensitivity list, return
    {name: first_read_node} for every signal read in the body that is not listed,
    in first-occurrence order. Returns {} if there's no explicit list to check
    (wildcard, edge-sensitive, or not a plain `always` block)."""
    sensitivity_names = procedural_block_sensitivity_names(block_raw)
    if sensitivity_names is None:
        return {}

    timing_statement = procedural_block_statement(block_raw)
    body = procedural_block_statement(timing_statement) if timing_statement is not None else None
    if body is None:
        return {}

    missing: dict[str, SyntaxNode] = {}
    for name, node in iter_identifier_reads(body):
        if name not in sensitivity_names and name not in missing:
            missing[name] = node
    return missing


@rule_runner.register
class NoIncompleteSensitivityListRule(Rule):
    code = "NO_INCOMPLETE_SENSITIVITY_LIST"
    message = "Signal is read in this block but missing from its explicit sensitivity list"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        if not isinstance(vnode.raw, (IdentifierNameNode, IdentifierSelectNameNode)):
            return False

        block = _enclosing_always_block(ctx)
        if block is None:
            return False

        missing = _missing_sensitivity_trigger_nodes(block.raw)
        return any(node is vnode.raw for node in missing.values())

    def report(self, vnode: BaseVNode) -> dict[str, Any]:
        diagnostic = super().report(vnode)
        name = identifier_name(vnode.raw)
        diagnostic["message"] = f"Signal '{name}' is read in this block but missing from its sensitivity list"
        return diagnostic
