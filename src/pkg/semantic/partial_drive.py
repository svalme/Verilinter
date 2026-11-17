"""Which bits of a packed vector no write reaches.

A signal is read but never written is reported as a whole. A vector some of whose bits are written
(`assign x[0] = a; assign x[3:2] = b;`) is covered here: each write event carries the part it touches (see
`write_region`), so the bits that no event covers can be listed. The answer is None whenever it cannot be
given with certainty, so a caller reports nothing rather than guessing."""
from __future__ import annotations

from .driver_resolver import write_events
from .symbol import Symbol
from .write_region import INDEX, NEVER, RANGE, SPAN

Interval = tuple[int, int]


def _declared_span(symbol: Symbol) -> Interval | None:
    """`(low, high)` of a plain one-dimensional packed vector, None for anything else (scalars, arrays,
    multiple packed dimensions, a declared type name, unknown bounds)."""
    if len(symbol.packed_dimensions) != 1 or symbol.unpacked_dimensions or symbol.unpacked_dimension_widths:
        return None
    if symbol.interface_type_name or symbol.named_type_dimension_count is not None:
        return None
    if not isinstance(symbol.msb, int) or not isinstance(symbol.lsb, int):
        return None
    return min(symbol.msb, symbol.lsb), max(symbol.msb, symbol.lsb)


def _written_intervals(symbol: Symbol) -> list[Interval] | None:
    """The bit intervals the write events of `symbol` cover, or None when any write has an unknown reach or
    the whole vector is written (which leaves no bit uncovered, so the caller has nothing to report)."""
    intervals: list[Interval] = []
    for event in write_events(symbol):
        region = event.get("write_region") or ()
        if not region:
            return None
        if len(region) != 1:
            return None
        step = region[0]
        kind = step[0]
        if kind == NEVER:
            continue
        if kind == INDEX and isinstance(step[1], int):
            intervals.append((step[1], step[1]))
        elif kind == RANGE and isinstance(step[1], int) and isinstance(step[2], int):
            intervals.append((step[1], step[2]))
        elif kind == SPAN:
            intervals.extend((int(low), int(high)) for low, high in step[1])  # type: ignore[arg-type,union-attr]
        else:
            return None
    return intervals


def undriven_bits(symbol: Symbol) -> list[Interval] | None:
    """The `(high, low)` runs of bits of `symbol` that no write covers, highest first; an empty list when
    every bit is written, None when the answer is not known (see the module docstring)."""
    span = _declared_span(symbol)
    if span is None:
        return None
    intervals = _written_intervals(symbol)
    if not intervals:
        return None
    low, high = span
    uncovered: list[Interval] = []
    cursor = low
    for start, end in sorted(intervals):
        if start > cursor:
            uncovered.append((min(start - 1, high), cursor))
        cursor = max(cursor, end + 1)
        if cursor > high:
            break
    if cursor <= high:
        uncovered.append((high, cursor))
    uncovered = [(top, bottom) for top, bottom in uncovered if bottom <= top and bottom >= low and top <= high]
    return sorted(uncovered, reverse=True)


def format_bit_runs(runs: list[Interval]) -> str:
    """`[14:13], [11]` for the runs `(14, 13)` and `(11, 11)`."""
    return ", ".join(f"[{top}]" if top == bottom else f"[{top}:{bottom}]" for top, bottom in runs)
