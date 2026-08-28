from typing import TYPE_CHECKING

from ...parser.syntax import is_unlabeled_generate_block
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class MissingGenerateBlockLabelRule(Rule):
    code = "MISSING_GENERATE_BLOCK_LABEL"
    message = "Generate block is missing an explicit label"
    category = "rtl_style"
    default_profiles = ("legacy_verilog",)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_unlabeled_generate_block(vnode.raw)
