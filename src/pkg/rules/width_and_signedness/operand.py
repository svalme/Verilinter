"""One classification of an expression operand for the comparison, index and width rules.

Each rule used to decide for itself whether an operand was a constant, a bounded value or a computed one,
and the decisions disagreed. `classify_operand` answers once; a rule asks the `Operand` it gets back.
"""
from __future__ import annotations

from enum import StrEnum
from functools import cached_property
from typing import Sequence

from ...parser.syntax import (
    constant_integer_value,
    evaluate_constant_text_expression,
    identifier_name,
    is_width_bounded_operand,
    natural_expression_width_and_signed,
    unwrap_parentheses,
)


class OperandKind(StrEnum):
    LITERAL = "literal"  # a number the parser can fold (`4'd3`, `-1`)
    CONSTANT_SYMBOL = "constant_symbol"  # a parameter or enum member: its value, not a declared range, fixes its behavior
    WIDTH_BOUNDED = "width_bounded"  # a name, select or concatenation: a value limited to its declared width
    COMPUTED = "computed"  # any other expression; it is evaluated at the context width and can exceed its operands' width


class Operand:
    """An expression operand with its kind, folded value, and natural width and signedness.

    Width and signedness are computed on first use because many comparisons are decided from the kind alone.
    """

    def __init__(self, scope: object, expr: object, tree: object, kind: OperandKind, value: int | None) -> None:
        self._scope = scope
        self._expr = expr
        self._tree = tree
        self.kind = kind
        self.value = value  # set for LITERAL

    @cached_property
    def _natural(self) -> tuple[int | None, bool | None]:
        return natural_expression_width_and_signed(self._scope, self._expr, self._tree)

    @property
    def width(self) -> int | None:
        return self._natural[0]

    @property
    def signed(self) -> bool | None:
        return self._natural[1]

    @property
    def is_literal(self) -> bool:
        return self.kind is OperandKind.LITERAL

    @property
    def is_constant_symbol(self) -> bool:
        return self.kind is OperandKind.CONSTANT_SYMBOL

    @property
    def is_width_bounded(self) -> bool:
        return self.kind is OperandKind.WIDTH_BOUNDED


def classify_operand(scope: object, expr: object, tree: object = None) -> Operand:
    inner = unwrap_parentheses(expr)
    value = constant_integer_value(inner)
    if value is not None:
        return Operand(scope, expr, tree, OperandKind.LITERAL, value)

    name = identifier_name(inner)
    lookup = getattr(scope, "lookup_hierarchical", None)
    symbol = lookup(name) if name and callable(lookup) else None
    if symbol is not None and symbol.is_compile_time_constant:
        return Operand(scope, expr, tree, OperandKind.CONSTANT_SYMBOL, None)

    kind = OperandKind.WIDTH_BOUNDED if is_width_bounded_operand(expr) else OperandKind.COMPUTED
    return Operand(scope, expr, tree, kind, None)


def packed_dimension_bounds(symbol: object, position: int, scope: object) -> tuple[int, int, int] | None:
    """`(lowest index, highest index, width)` of the packed dimension that the `position`-th element-bit
    selector indexes, outermost dimension first, or None when the dimension or its bounds are unknown.

    In `a[1][7:0]` on `logic [2:0][7:0] a` the first selector indexes the `[2:0]` dimension and the second
    the `[7:0]` one, so each is checked against its own bounds and not against the whole vector."""
    dimensions = getattr(symbol, "packed_dimensions", ())
    if not 0 <= position < len(dimensions):
        return None
    msb = evaluate_constant_text_expression(dimensions[position][0], scope)
    lsb = evaluate_constant_text_expression(dimensions[position][1], scope)
    if msb is None or lsb is None:
        return None
    return min(msb, lsb), max(msb, lsb), abs(msb - lsb) + 1


def selectors_into_element_bits(symbol: object, selectors: Sequence[object]) -> Sequence[object]:
    """The selectors that index the bits of one element of `symbol`.

    In `a[i][3:0]` on `logic [7:0] a [0:15]` the first selector picks an array element (an unpacked
    dimension) and only the rest index bits, so a bit-range check applies to what follows.
    """
    return selectors[len(getattr(symbol, "unpacked_dimensions", ())):]
