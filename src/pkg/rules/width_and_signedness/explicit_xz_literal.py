from typing import TYPE_CHECKING

from ...parser.syntax import is_explicit_xz_literal
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class ExplicitXZLiteralRule(Rule):
    code = "EXPLICIT_XZ_LITERAL"
    message = "Explicit X/Z literal used as a value; unsynthesizable and defeats reset/comparison determinism"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, _ctx: "Context") -> bool:
        return is_explicit_xz_literal(vnode.raw)
