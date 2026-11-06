"""The kinds of symbol the analysis records, and what each kind implies."""
from __future__ import annotations

from enum import StrEnum


class SymbolKind(StrEnum):
    """Values equal the plain strings older code and cached results compared against."""

    VARIABLE = "variable"  # nets, variables, ports, function and task formals, and function return values
    PARAMETER = "parameter"  # `parameter` and `localparam` (`Symbol.is_localparam` tells them apart)
    ENUM_MEMBER = "enum_member"
    FIELD = "field"  # a struct or union member
    TYPEDEF = "typedef"  # a typedef name or a `parameter type` name
    GENVAR = "genvar"
    INSTANCE = "instance"
    IMPLICIT_NET = "implicit_net"  # a placeholder for a name used with no declaration under `default_nettype wire`

    @property
    def is_compile_time_constant(self) -> bool:
        """The name stands for a value fixed at elaboration, so its declared width does not bound uses of it."""
        return self in (SymbolKind.PARAMETER, SymbolKind.ENUM_MEMBER)

    @property
    def is_type_name(self) -> bool:
        return self is SymbolKind.TYPEDEF
