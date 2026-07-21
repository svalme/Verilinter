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
        self.is_read: bool = False
        self.is_written: bool = False

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
    ) -> None:
        self.uses.append(loc)
        event: UseEvent = {"location": loc, "read": read, "write": write}
        if driver_id is not None:
            event["driver_id"] = driver_id
        if driver_location is not None:
            event["driver_location"] = driver_location
        self.use_events.append(event)
        self.is_read |= read
        self.is_written |= write

    @property
    def is_declared(self) -> bool:
        return bool(self.declarations)
