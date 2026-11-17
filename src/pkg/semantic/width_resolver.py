"""Answers the width of an expression and says where the answer came from.

Three sources, asked in this order: slang's elaborated width when every instance of the enclosing module
agrees, the set of widths when they do not, and the estimator (which evaluates with the parameter values
the module declares) when slang has no entry for the expression. A reader that cares how sure the width is
reads `source`; one that only needs a number reads `width`. The resolver reads; it never changes the symbol
table or the record."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from ..parser.elaborated_widths import ElaboratedWidths
from ..parser.syntax import natural_expression_width_and_signed

Estimator = Callable[[object, object, object], tuple[int | None, bool | None]]


class WidthSource(StrEnum):
    ELABORATED = "elaborated"  # slang computed it, and every instance gave the same width
    INSTANCES_DISAGREE = "instances_disagree"  # slang computed it per instance and the instances differ
    ESTIMATOR_DEFAULTS = "estimator_defaults"  # slang has no entry; the estimator used the declared parameter values
    UNKNOWN = "unknown"  # neither source knows


@dataclass(frozen=True)
class ResolvedWidth:
    source: WidthSource
    width: int | None  # the one width, or None for INSTANCES_DISAGREE and UNKNOWN
    signed: bool | None
    elaborated_widths: frozenset[int]  # every width slang gave; empty when it has no entry
    estimator_width: int | None  # the estimator's answer, kept so a comparison can see both


class WidthResolver:
    def __init__(self, record: ElaboratedWidths | None, estimator: Estimator = natural_expression_width_and_signed) -> None:
        self._record = record
        self._estimator = estimator

    def resolve(self, scope: object, expr: object, tree: object) -> ResolvedWidth:
        estimator_width, estimator_signed = self._estimator(scope, expr, tree)
        found = None
        if self._record is not None and not self._record.is_macro_expansion(expr, tree):
            found = self._record.widths_for(expr, tree)
        if found is None:
            source = WidthSource.ESTIMATOR_DEFAULTS if estimator_width is not None else WidthSource.UNKNOWN
            return ResolvedWidth(source, estimator_width, estimator_signed, frozenset(), estimator_width)
        if found.width is None:
            return ResolvedWidth(WidthSource.INSTANCES_DISAGREE, None, found.is_signed, found.widths, estimator_width)
        return ResolvedWidth(WidthSource.ELABORATED, found.width, found.is_signed, found.widths, estimator_width)
