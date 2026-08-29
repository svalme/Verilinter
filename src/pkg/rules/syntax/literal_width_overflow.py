from typing import TYPE_CHECKING

from ...parser.syntax import sized_literal_overflow
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from typing import Any

    from ...walk.context import Context


@rule_runner.register
class LiteralWidthOverflowRule(Rule):
    code = "LITERAL_WIDTH_OVERFLOW"
    message = "Sized literal's value does not fit in its declared width"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, _ctx: "Context") -> bool:
        return sized_literal_overflow(vnode.raw) is not None

    def report(self, vnode: BaseVNode) -> "dict[str, Any]":
        diagnostic = super().report(vnode)
        overflow = sized_literal_overflow(vnode.raw)
        if overflow is not None:
            declared_width, minimum_width = overflow
            diagnostic["message"] = (
                f"Literal needs at least {minimum_width} bits but is declared {declared_width}'"
            )
        return diagnostic
