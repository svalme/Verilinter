"""Gives a driver block its id and records what kind of driver it is."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ...parser.syntax import driver_block_category, driver_id_of
from ...semantic.driver_kind import DriverKind
from ...vnodes.base_vnode import Location

if TYPE_CHECKING:
    from ...semantic.symbol_table import SymbolTable
    from ...vnodes.base_vnode import BaseVNode


def register_driver_block(driver_block: BaseVNode, symbol_table: SymbolTable) -> tuple[str, Location]:
    """The id and the location a use event records for the procedural block or continuous assign that owns a
    write. The block's kind is recorded under the id once, here, from its syntax, so no rule has to read it
    back out of the id text."""
    driver_id = driver_id_of(driver_block)
    symbol_table.record_driver_kind(driver_id, DriverKind(driver_block_category(driver_block)))
    return driver_id, driver_block.location
