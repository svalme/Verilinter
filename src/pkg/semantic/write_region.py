"""Which part of a symbol one write touches, and when two such parts can overlap.

A region is a tuple of steps, one per selector applied to the written name, outermost first; the empty
tuple is the whole symbol. Steps are positional, so step k of two writes to one symbol refers to the same
dimension or member.

    ("index", value)        `a[3]`; value is None when it cannot be evaluated
    ("range", low, high)    `a[7:4]`, `a[b +: w]`; both None when either end cannot be evaluated
    ("field", name)         `s.mode`
    ("span", intervals)     an index or range that takes several values, one per iteration of an enclosing
                            generate loop: a sorted tuple of (low, high) pairs, `a[2*i]` for i in 0..3
    ("never",)              a write in a generate branch that no value of the enclosing loops selects
"""
from __future__ import annotations

from collections.abc import Iterable

RegionStep = tuple[object, ...]
WriteRegion = tuple[RegionStep, ...]

INDEX = "index"
RANGE = "range"
FIELD = "field"
SPAN = "span"
NEVER = "never"


def _freeze(value: object) -> object:
    """A step part as a tuple: a span's interval list becomes a tuple of pairs (one level of nesting)."""
    if not isinstance(value, (list, tuple)):
        return value
    return tuple(tuple(item) if isinstance(item, list) else item for item in value)


def normalize_region(steps: Iterable[Iterable[object]] | None) -> WriteRegion:
    """Rebuild a region from its serialized form; a JSON round trip turns the tuples into lists."""
    return tuple(tuple(_freeze(part) for part in step) for step in steps or ())  # type: ignore[misc]


def span_step(intervals: Iterable[tuple[int, int]]) -> RegionStep:
    """One step for a set of (low, high) intervals: merged and sorted, and a single value as an index."""
    merged: list[list[int]] = []
    for low, high in sorted(intervals):
        if merged and low <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], high)
        else:
            merged.append([low, high])
    if len(merged) == 1 and merged[0][0] == merged[0][1]:
        return (INDEX, merged[0][0])
    if len(merged) == 1:
        return (RANGE, merged[0][0], merged[0][1])
    return (SPAN, tuple((low, high) for low, high in merged))


def _intervals(step: RegionStep) -> tuple[tuple[int, int], ...] | None:
    """The (low, high) intervals an index, range or span step covers, or None when they are not known."""
    if step[0] == INDEX and isinstance(step[1], int):
        return ((step[1], step[1]),)
    if step[0] == RANGE and isinstance(step[1], int) and isinstance(step[2], int):
        return ((step[1], step[2]),)
    if step[0] == SPAN:
        return tuple(step[1])  # type: ignore[arg-type]
    return None


def _steps_disjoint(a: RegionStep, b: RegionStep, distinct_members_disjoint: bool) -> bool:
    if a[0] == FIELD and b[0] == FIELD:
        return distinct_members_disjoint and a[1] != b[1]
    first, second = _intervals(a), _intervals(b)
    if first is None or second is None:
        return False
    return all(x[1] < y[0] or y[1] < x[0] for x in first for y in second)


def regions_may_overlap(a: WriteRegion, b: WriteRegion, *, distinct_members_disjoint: bool = False) -> bool:
    """False only when the two regions are provably disjoint: some pair of aligned steps shares no value.

    Anything not known, and any pair of steps of different kinds, counts as overlapping. Two members of a
    packed union overlap, so distinct field names are disjoint only when the caller knows the symbol is a
    struct and passes `distinct_members_disjoint`. A region with a `never` step is a write that does not
    exist, so it overlaps nothing."""
    if any(step[0] == NEVER for step in a) or any(step[0] == NEVER for step in b):
        return False
    return not any(_steps_disjoint(x, y, distinct_members_disjoint) for x, y in zip(a, b))
