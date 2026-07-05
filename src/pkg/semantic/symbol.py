# src/pkg/semantic/symbol.py
from ..vnodes.base_vnode import Location

class Symbol:
    """Represents a declared symbol (variable, signal, etc.) in the design."""

    def __init__(self, name: str, kind: str):
        self.name = name
        self.kind = kind  # wire, reg, logic, variable, function, task
        self.scope: "Scope | None" = None

        self.declarations: list[Location] = []
        self.uses: list[Location] = []

        self.is_implicit: bool = False
        self.is_read: bool = False
        self.is_written: bool = False

    def set_scope(self, scope: "Scope | None") -> None:
        self.scope = scope

    def add_declaration(self, loc: Location) -> None:
        self.declarations.append(loc)

    def add_use(self, loc: Location, read: bool = False, write: bool = False) -> None:
        self.uses.append(loc)
        self.is_read |= read
        self.is_written |= write

    @property
    def is_declared(self) -> bool:
        return bool(self.declarations)
