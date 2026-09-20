from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..symbol import Symbol


class AssignmentTarget:
    """Represents a resolved target of an assignment construct.

    Unifies whole-symbol targets (`assign a = ...;`) with indexed, sliced, or
    part-selected targets (`assign a[i] = ...;`, `assign a[7:0] = ...;`), and
    concatenated assignment targets (`assign {a, b} = ...;`).

    Delegates all other symbol attributes (declarations, uses, scope, etc.)
    transparently to `base_symbol` when `base_symbol` is present.
    """

    def __init__(
        self,
        base_symbol: Symbol | None = None,
        slice_width: int | None = None,
        is_sliced: bool = False,
        selectors: list[object] | None = None,
        is_concatenated: bool = False,
        elements: list[AssignmentTarget] | None = None,
        total_width: int | None = None,
    ) -> None:
        self.base_symbol = base_symbol
        self.slice_width = slice_width
        self.is_sliced = is_sliced
        self.selectors = list(selectors or [])
        self.is_concatenated = is_concatenated
        self.elements = list(elements or [])
        self.total_width = total_width

    @property
    def bit_width(self) -> int | None:
        if self.is_concatenated:
            return self.total_width
        if self.is_sliced:
            return self.slice_width
        if self.base_symbol is not None:
            return getattr(self.base_symbol, "bit_width", None)
        return None

    @property
    def is_signed(self) -> bool | None:
        if self.is_concatenated or self.is_sliced:
            return None
        if self.base_symbol is not None:
            return getattr(self.base_symbol, "is_signed", None)
        return None

    def __getattr__(self, name: str) -> object:
        if self.base_symbol is not None:
            return getattr(self.base_symbol, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __repr__(self) -> str:
        if self.is_concatenated:
            elems_str = ", ".join(repr(e) for e in self.elements)
            return f"AssignmentTarget({{{elems_str}}}, width={self.bit_width})"
        name = getattr(self.base_symbol, "name", "<unnamed>")
        if self.is_sliced:
            return f"AssignmentTarget({name}[...], width={self.bit_width})"
        return f"AssignmentTarget({name}, width={self.bit_width})"

