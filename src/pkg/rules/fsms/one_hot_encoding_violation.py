from typing import TYPE_CHECKING

from ...parser.syntax import (
    case_item_expressions,
    case_statement_items,
    case_statement_selector_name,
    is_case_statement,
    is_state_register_case,
    resolve_case_item_value,
)
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


def _is_one_hot_encoding_violation(vnode: BaseVNode, ctx: "Context") -> bool:
    """True when a state-register case statement's declared width structurally
    implies one-hot intent (width equals the number of distinct resolvable
    state values -- the defining property of a one-hot scheme, since binary
    encoding of N states only ever needs `ceil(log2(N))` bits) and at least
    one of those values doesn't have exactly one bit set.

    Deliberately narrower than "flag any value with popcount != 1": that
    would false-fire constantly on ordinary sequential binary encoding, where
    small values like 1/2/4 coincidentally have popcount 1. General
    "mixed binary/one-hot/gray encoding style" detection (this rule's
    original broader framing) is a known, undetected gap -- gray-code
    adjacency needs the state-transition graph this project doesn't build.

    Requires at least 3 distinct states before applying the width-equality
    signal at all: a 2-state FSM is very commonly declared with a 2-bit
    register anyway (headroom for future states), which would otherwise
    coincidentally satisfy `width == state_count` on completely ordinary
    binary-style code (`IDLE = 2'b00` has popcount 0) -- confirmed as a real
    false positive during development, not just a theoretical edge case.
    """
    if not is_case_statement(vnode.raw):
        return False
    if not is_state_register_case(vnode.raw, ctx):
        return False

    name = case_statement_selector_name(vnode.raw)
    if name is None:
        return False
    symbol = ctx.scope().lookup(name)
    if symbol is None or not isinstance(symbol.bit_width, int) or symbol.bit_width <= 1:
        return False

    values: set[int] = set()
    for item in case_statement_items(vnode.raw):
        for expression in case_item_expressions(item):
            value = resolve_case_item_value(expression, ctx.scope())
            if value is not None:
                values.add(value)

    if len(values) < 3 or len(values) != symbol.bit_width:
        return False

    return any(bin(value).count("1") != 1 for value in values)


@rule_runner.register
class OneHotEncodingViolationRule(Rule):
    code = "ONE_HOT_ENCODING_VIOLATION"
    message = "State register's declared width implies one-hot encoding, but at least one state value doesn't have exactly one bit set"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return _is_one_hot_encoding_violation(vnode, ctx)
