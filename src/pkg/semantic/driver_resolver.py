"""Answers who writes and who reads a symbol, from the use events its walk recorded."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..vnodes.base_vnode import Location
from .driver_kind import DriverKind
from .instance_effects import is_instance_driver_id
from .symbol import Symbol, UseEvent

if TYPE_CHECKING:
    from .symbol_table import SymbolTable


@dataclass(frozen=True)
class Driver:
    """One driver of a symbol: the procedural block, continuous assign or instance port that owns a set of
    writes. `location` is where the driver sits (from its first write that records one)."""

    id: str
    location: Location | None
    events: tuple[UseEvent, ...]

    @property
    def is_instance(self) -> bool:
        return is_instance_driver_id(self.id)


def write_events(symbol: Symbol) -> list[UseEvent]:
    """Every write use of the symbol, in the order the walk recorded them."""
    return [event for event in symbol.use_events if event["write"]]


def read_events(symbol: Symbol) -> list[UseEvent]:
    """Every use of the symbol that is not a pure write: a read, or a read and write together."""
    return [event for event in symbol.use_events if event["read"]]


class DriverResolver:
    """Groups a symbol's write events by the driver that owns them.

    A write belongs to a driver when its event carries a driver id. An instance output port is a driver
    like a procedural block, told apart by its id (`Driver.is_instance`), so a rule that judges only
    one kind asks for it. Drivers come in the order of their first write. It reads the symbol and never
    changes it.
    """

    def __init__(self, symbol_table: SymbolTable) -> None:
        self._table = symbol_table

    def writes(self, symbol: Symbol) -> list[UseEvent]:
        return write_events(symbol)

    def reads(self, symbol: Symbol) -> list[UseEvent]:
        return read_events(symbol)

    def instance_writes(self, symbol: Symbol) -> list[UseEvent]:
        return [event for event in write_events(symbol) if is_instance_driver_id(event.get("driver_id"))]

    def other_writes(self, symbol: Symbol) -> list[UseEvent]:
        return [event for event in write_events(symbol) if not is_instance_driver_id(event.get("driver_id"))]

    def kind_of(self, driver_id: str | None) -> DriverKind | None:
        """What owns the writes of a driver id, or None for a driver that is not a continuous assign or a
        procedural block (an instance port, a clocking block) and for an id the walk did not record."""
        return None if driver_id is None else self._table.driver_kinds.get(driver_id)

    def drivers(self, symbol: Symbol, *, instance: bool | None = None, located: bool = False) -> list[Driver]:
        """The drivers of the symbol. `instance` keeps only instance drivers (True) or only the others
        (False); `located` leaves out a write that records no driver location."""
        events_by_id: dict[str, list[UseEvent]] = {}
        locations: dict[str, Location | None] = {}
        for event in write_events(symbol):
            driver_id = event.get("driver_id")
            if driver_id is None:
                continue
            driver_location = event.get("driver_location")
            if located and driver_location is None:
                continue
            if instance is not None and is_instance_driver_id(driver_id) is not instance:
                continue
            events_by_id.setdefault(driver_id, []).append(event)
            if locations.get(driver_id) is None:
                locations[driver_id] = driver_location
        return [Driver(driver_id, locations[driver_id], tuple(events)) for driver_id, events in events_by_id.items()]
