from typing import TYPE_CHECKING

from ...parser.syntax import (
    assignment_is_implicit_real_conversion,
    declarator_is_implicit_real_conversion,
)
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoImplicitRealConversionRule(Rule):
    code = "NO_IMPLICIT_REAL_CONVERSION"
    message = "Implicit conversion of real or fractional value to integral target loses fractional precision"
    category = "declarations_and_types"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        raw = vnode.raw
        if declarator_is_implicit_real_conversion(raw):
            return True
        if assignment_is_implicit_real_conversion(raw):
            return True
        return False
