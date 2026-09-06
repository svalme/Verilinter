from typing import TYPE_CHECKING

from ...parser.syntax import (
    duplicate_generate_branch_label,
    is_case_generate_node,
    is_if_generate_node,
)
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class DuplicateGenerateBlockLabelRule(Rule):
    """Sibling of `MISSING_GENERATE_BLOCK_LABEL`: flags two sibling generate
    blocks under one `if`/`case`-generate construct that share the same
    explicit label. Cross-region label collisions (two separate top-level
    `generate...endgenerate` regions in the same module) are a known gap,
    not attempted here -- see `duplicate_generate_branch_label`.
    """

    code = "DUPLICATE_GENERATE_BLOCK_LABEL"
    message = "Sibling generate blocks share the same explicit label"
    category = "rtl_correctness"
    default_profiles = ("legacy_verilog",)

    def applies(self, vnode: BaseVNode, _ctx: "Context") -> bool:
        if not (is_if_generate_node(vnode.raw) or is_case_generate_node(vnode.raw)):
            return False
        return duplicate_generate_branch_label(vnode.raw)
