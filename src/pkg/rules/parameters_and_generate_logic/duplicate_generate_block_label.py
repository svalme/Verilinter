from typing import TYPE_CHECKING

from ...parser.syntax import generate_label_redefined
from ...parser.types import CaseGenerateNode, GenerateBlockNode, IfGenerateNode, LoopGenerateNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class DuplicateGenerateBlockLabelRule(Rule):
    """Sibling of `MISSING_GENERATE_BLOCK_LABEL`: flags a generate construct that gives a block an explicit
    label an earlier generate construct in the same scope already uses. Both constructs are elaborated, so
    the two blocks coexist and the shared label is a redefinition. The branches of one `if`/`else` chain or
    one `case`-generate are not compared with each other: only one is elaborated, so they may share a label.
    """

    code = "DUPLICATE_GENERATE_BLOCK_LABEL"
    message = "Generate block label is already used by another generate construct in the same scope"
    category = "rtl_correctness"
    default_profiles = ("legacy_verilog",)
    target_node_types = (IfGenerateNode, CaseGenerateNode, LoopGenerateNode, GenerateBlockNode)

    def applies(self, vnode: BaseVNode, _ctx: "Context") -> bool:
        return generate_label_redefined(vnode.raw)
