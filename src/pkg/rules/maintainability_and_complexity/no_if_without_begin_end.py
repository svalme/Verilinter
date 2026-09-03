from typing import TYPE_CHECKING

from ...parser.syntax import is_unwrapped_else_body, is_unwrapped_if_body
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoIfWithoutBeginEndRule(Rule):
    code = "NO_IF_WITHOUT_BEGIN_END"
    message = "`if` branch is a single statement not wrapped in begin/end"
    category = "rtl_subset"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_unwrapped_if_body(vnode.raw)


@rule_runner.register
class NoElseWithoutBeginEndRule(Rule):
    code = "NO_ELSE_WITHOUT_BEGIN_END"
    message = "`else` branch is a single statement not wrapped in begin/end"
    category = "rtl_subset"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_unwrapped_else_body(vnode.raw)
