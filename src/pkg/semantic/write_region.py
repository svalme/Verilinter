"""Which part of a symbol one write touches, and when two such parts can overlap.

A region is a tuple of steps, one per selector applied to the written name, outermost first; the empty
tuple is the whole symbol. Steps are positional, so step k of two writes to one symbol refers to the same
dimension or member.

    ("index", value)        `a[3]`; value is None when it cannot be evaluated
    ("range", low, high)    `a[7:4]`, `a[b +: w]`; both None when either end cannot be evaluated
    ("field", name)         `s.mode`
"""
from __future__ import annotations

from collections.abc import Iterable

RegionStep = tuple[object, ...]
WriteRegion = tuple[RegionStep, ...]

INDEX = "index"
RANGE = "range"
FIELD = "field"


def normalize_region(steps: Iterable[Iterable[object]] | None) -> WriteRegion:
    """Rebuild a region from its serialized form; a JSON round trip turns the tuples into lists."""
    return tuple(tuple(step) for step in steps or ())


def _bounds(step: RegionStep) -> tuple[int, int] | None:
    """The (low, high) values an index or range step covers, or None when they are not known."""
    if step[0] == INDEX and isinstance(step[1], int):
        return step[1], step[1]
    if step[0] == RANGE and isinstance(step[1], int) and isinstance(step[2], int):
        return step[1], step[2]
    return None


def _steps_disjoint(a: RegionStep, b: RegionStep, distinct_members_disjoint: bool) -> bool:
    if a[0] == FIELD and b[0] == FIELD:
        return distinct_members_disjoint and a[1] != b[1]
    first, second = _bounds(a), _bounds(b)
    if first is None or second is None:
        return False
    return first[1] < second[0] or second[1] < first[0]


def regions_may_overlap(a: WriteRegion, b: WriteRegion, *, distinct_members_disjoint: bool = False) -> bool:
    """False only when the two regions are provably disjoint: some pair of aligned steps shares no value.

    Anything not known, and any pair of steps of different kinds, counts as overlapping. Two members of a
    packed union overlap, so distinct field names are disjoint only when the caller knows the symbol is a
    struct and passes `distinct_members_disjoint`."""
    return not any(_steps_disjoint(x, y, distinct_members_disjoint) for x, y in zip(a, b))
