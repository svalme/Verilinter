# src/pkg/semantic/symbol.py
from __future__ import annotations

from typing import TYPE_CHECKING, NotRequired, TypedDict

from ..vnodes.base_vnode import Location

if TYPE_CHECKING:
    from .scope import Scope


class UseEvent(TypedDict):
    location: Location
    read: bool
    write: bool
    driver_id: NotRequired[str]
    driver_location: NotRequired[Location]
    branch_signature: NotRequired[tuple[tuple[int, int], ...]]

class Symbol:
    """Represents a declared symbol (variable, signal, etc.) in the design."""

    def __init__(self, name: str, kind: str) -> None:
        self.name = name
        self.kind = kind  # wire, reg, logic, variable, implicit_net, function, task
        self.scope: Scope | None = None

        self.declarations: list[Location] = []
        self.uses: list[Location] = []
        self.use_events: list[UseEvent] = []

        self.is_implicit: bool = False
        self.is_port: bool = False
        self.port_direction: str | None = None  # "input" / "output" / "inout" / "ref" when is_port
        self.bit_width: int | None = None
        self.is_signed: bool | None = None
        self.value: int | None = None
        self.is_read: bool = False
        self.is_written: bool = False
        self.use_count: int = 0
        self.read_count: int = 0
        self.write_count: int = 0

    def set_scope(self, scope: Scope | None) -> None:
        self.scope = scope

    def add_declaration(self, loc: Location) -> None:
        self.declarations.append(loc)

    def add_use(
        self,
        loc: Location,
        read: bool = False,
        write: bool = False,
        driver_id: str | None = None,
        driver_location: Location | None = None,
        branch_signature: tuple[tuple[int, int], ...] | None = None,
    ) -> None:
        self.uses.append(loc)
        event: UseEvent = {"location": loc, "read": read, "write": write}
        if driver_id is not None:
            event["driver_id"] = driver_id
        if driver_location is not None:
            event["driver_location"] = driver_location
        if branch_signature is not None:
            event["branch_signature"] = branch_signature
        self.use_events.append(event)
        self.is_read |= read
        self.is_written |= write
        self.use_count += 1
        self.read_count += 1 if read else 0
        self.write_count += 1 if write else 0

    @property
    def is_declared(self) -> bool:
        return bool(self.declarations)

    def is_explicit_kind(self, kind: str) -> bool:
        """True when this is a genuine, explicitly-declared symbol of `kind`.

        Filters out implicit nets and declaration-less placeholder symbols --
        the entry guard most symbol rules need before applying their own
        condition (e.g. `sym.is_explicit_kind("variable")` for
        `NO_UNDRIVEN_OUTPUT_PORT`/`READ_BEFORE_WRITE`/etc.,
        `sym.is_explicit_kind("parameter")` for `NO_UNUSED_PARAMETER`).
        """
        return self.kind == kind and self.is_declared and not self.is_implicit
