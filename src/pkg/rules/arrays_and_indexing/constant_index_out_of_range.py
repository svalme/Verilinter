from typing import TYPE_CHECKING

from ...parser.syntax import (
    constant_integer_value,
    element_select_index_or_range,
    identifier_select_base_and_selectors,
)
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


def _is_constant_index_out_of_range(vnode: BaseVNode, ctx: "Context") -> bool:
    """True when `vnode` is an `a[...]` bit-select/part-select whose constant
    index/range falls outside `a`'s declared `[bit_width-1:0]` range.

    Assumes a zero-based declared range, since `Symbol` only tracks
    `bit_width`, not the declaration's actual MSB/LSB text -- a non-zero-based
    declaration (`wire [10:5] x;`) is silently mismodeled, a known limitation.
    For an indexed part-select (`a[base +: W]` / `a[base -: W]`), only the
    width `W` alone is checked against `bit_width`; the full precise check
    that also accounts for a constant `base` is a known gap, not attempted
    in this first pass.
    """
    result = identifier_select_base_and_selectors(vnode.raw)
    if result is None:
        return False
    base_name, selectors = result

    symbol = ctx.scope().lookup_hierarchical(base_name)
    if symbol is None or not isinstance(symbol.bit_width, int):
        return False
    bit_width = symbol.bit_width
    msb = getattr(symbol, "msb", None)
    lsb = getattr(symbol, "lsb", None)
    has_range = isinstance(msb, int) and isinstance(lsb, int)
    min_bound = min(msb, lsb) if has_range else 0
    max_bound = max(msb, lsb) if has_range else bit_width - 1

    for selector in selectors:
        unwrapped = element_select_index_or_range(selector)
        if unwrapped is None:
            continue
        shape, payload = unwrapped

        if shape == "bit":
            index = constant_integer_value(payload)
            if index is not None and (index < min_bound or index > max_bound):
                return True
        elif shape == "simple_range":
            left, right = payload
            for bound in (constant_integer_value(left), constant_integer_value(right)):
                if bound is not None and (bound < min_bound or bound > max_bound):
                    return True
        elif shape in ("ascending", "descending"):
            _base, width_expr = payload
            width = constant_integer_value(width_expr)
            if width is not None and width > bit_width:
                return True

    return False


@rule_runner.register
class ConstantIndexOutOfRangeRule(Rule):
    code = "CONSTANT_INDEX_OUT_OF_RANGE"
    message = "Constant bit-select or part-select index is out of the signal's declared range"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return _is_constant_index_out_of_range(vnode, ctx)
