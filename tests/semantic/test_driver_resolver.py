"""The driver resolver: how a symbol's write events group into drivers, and what it must not merge."""
from __future__ import annotations

from src.pkg.semantic.driver_resolver import DriverResolver, read_events, write_events
from src.pkg.semantic.instance_effects import INSTANCE_DRIVER_PREFIX
from src.pkg.semantic.symbol import Symbol
from src.pkg.semantic.symbol_table import SymbolTable

BLOCK_A = "SyntaxKind.AlwaysBlock:f.sv:3:1"
BLOCK_B = "SyntaxKind.ContinuousAssign:f.sv:9:1"
INSTANCE = f"{INSTANCE_DRIVER_PREFIX}f.sv:12:1:u0:q"


def _loc(line: int) -> dict:
    return {"file": "f.sv", "line": line, "col": 1}


def _symbol() -> Symbol:
    return Symbol(name="s", kind="variable")


def _resolver() -> DriverResolver:
    return DriverResolver(SymbolTable())


def test_writes_and_reads_are_told_apart() -> None:
    symbol = _symbol()
    symbol.add_use(_loc(1), read=True)
    symbol.add_use(_loc(2), write=True)
    symbol.add_use(_loc(3), read=True, write=True)
    assert len(write_events(symbol)) == 2
    assert len(read_events(symbol)) == 2


def test_writes_of_one_driver_are_grouped_in_first_write_order() -> None:
    symbol = _symbol()
    symbol.add_use(_loc(4), write=True, driver_id=BLOCK_B, driver_location=_loc(9))
    symbol.add_use(_loc(5), write=True, driver_id=BLOCK_A, driver_location=_loc(3))
    symbol.add_use(_loc(6), write=True, driver_id=BLOCK_B, driver_location=_loc(9))
    drivers = _resolver().drivers(symbol)
    assert [driver.id for driver in drivers] == [BLOCK_B, BLOCK_A]
    assert len(drivers[0].events) == 2


def test_a_write_with_no_driver_id_belongs_to_no_driver() -> None:
    symbol = _symbol()
    symbol.add_use(_loc(1), write=True)
    assert _resolver().drivers(symbol) == []
    assert len(_resolver().other_writes(symbol)) == 1


def test_instance_drivers_are_kept_or_left_out_on_request() -> None:
    symbol = _symbol()
    symbol.add_use(_loc(4), write=True, driver_id=BLOCK_A, driver_location=_loc(3))
    symbol.add_use(_loc(12), write=True, driver_id=INSTANCE, driver_location=_loc(12))
    resolver = _resolver()
    assert [driver.id for driver in resolver.drivers(symbol, instance=True)] == [INSTANCE]
    assert [driver.id for driver in resolver.drivers(symbol, instance=False)] == [BLOCK_A]
    assert {driver.id for driver in resolver.drivers(symbol)} == {INSTANCE, BLOCK_A}
    assert resolver.drivers(symbol, instance=True)[0].is_instance
    assert len(resolver.instance_writes(symbol)) == 1
    assert len(resolver.other_writes(symbol)) == 1


def test_located_leaves_out_a_write_that_records_no_driver_location() -> None:
    symbol = _symbol()
    symbol.add_use(_loc(1), write=True, driver_id=BLOCK_A)
    symbol.add_use(_loc(2), write=True, driver_id=BLOCK_B, driver_location=_loc(9))
    resolver = _resolver()
    assert {driver.id for driver in resolver.drivers(symbol)} == {BLOCK_A, BLOCK_B}
    assert [driver.id for driver in resolver.drivers(symbol, located=True)] == [BLOCK_B]


def test_a_driver_location_comes_from_its_first_write_that_records_one() -> None:
    symbol = _symbol()
    symbol.add_use(_loc(1), write=True, driver_id=BLOCK_A)
    symbol.add_use(_loc(2), write=True, driver_id=BLOCK_A, driver_location=_loc(3))
    (driver,) = _resolver().drivers(symbol)
    assert driver.location == _loc(3)
    assert len(driver.events) == 2


def test_reads_never_make_a_driver() -> None:
    symbol = _symbol()
    symbol.add_use(_loc(1), read=True, driver_id=BLOCK_A, driver_location=_loc(3))
    assert _resolver().drivers(symbol) == []
