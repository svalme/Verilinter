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
    branch_signature: NotRequired[tuple[tuple[str, int], ...]]
    statement_id: NotRequired[str]
    in_port_connection: NotRequired[bool]
    is_nonblocking_write: NotRequired[bool]
    loop_ids: NotRequired[tuple[str, ...]]

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
        self.is_function_return: bool = False
        self.port_direction: str | None = None  # "input" / "output" / "inout" / "ref" when is_port
        self.bit_width: int | None = None
        self.msb: int | None = None
        self.lsb: int | None = None
        self.is_signed: bool | None = None
        self.value: int | None = None
        self.is_read: bool = False
        self.is_written: bool = False
        self.use_count: int = 0
        self.read_count: int = 0
        self.write_count: int = 0
        self.is_used_in_port_connection: bool = False

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
        branch_signature: tuple[tuple[str, int], ...] | None = None,
        statement_id: str | None = None,
        in_port_connection: bool = False,
        is_nonblocking_write: bool = False,
        loop_ids: tuple[str, ...] = (),
    ) -> None:
        self.uses.append(loc)
        event: UseEvent = {"location": loc, "read": read, "write": write}
        if driver_id is not None:
            event["driver_id"] = driver_id
        if driver_location is not None:
            event["driver_location"] = driver_location
        if branch_signature is not None:
            event["branch_signature"] = branch_signature
        if statement_id is not None:
            event["statement_id"] = statement_id
        if in_port_connection:
            event["in_port_connection"] = True
        if is_nonblocking_write:
            event["is_nonblocking_write"] = True
        if loop_ids:
            event["loop_ids"] = loop_ids
        self.use_events.append(event)
        self.is_read |= read
        self.is_written |= write
        self.use_count += 1
        self.read_count += 1 if read else 0
        self.write_count += 1 if write else 0
        self.is_used_in_port_connection |= in_port_connection

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
