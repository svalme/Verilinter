from src.pkg.semantic.driver_evidence import DriverEvidence
from src.pkg.semantic.scope import Scope
from src.pkg.semantic.symbol import Symbol


def _symbol() -> Symbol:
    symbol = Symbol(name="s", kind="variable")
    Scope("module", "m").define(symbol)
    return symbol


def test_symbol_with_no_write_has_no_driver_evidence() -> None:
    evidence = _symbol().driver_evidence
    assert evidence is DriverEvidence.NONE
    assert not evidence.is_driver_established


def test_written_symbol_is_driven_in_the_file() -> None:
    symbol = _symbol()
    symbol.add_use(None, write=True)
    assert symbol.driver_evidence is DriverEvidence.WRITTEN
    assert symbol.driver_evidence.is_driver_established


def test_instance_output_outranks_a_local_write() -> None:
    symbol = _symbol()
    symbol.add_use(None, write=True)
    symbol.is_driven_by_instance = True
    assert symbol.driver_evidence is DriverEvidence.INSTANCE
    assert symbol.driver_evidence.is_driver_established


def test_unknown_port_direction_outranks_every_other_evidence() -> None:
    symbol = _symbol()
    symbol.add_use(None, write=True)
    symbol.is_driven_by_instance = True
    symbol.in_unclassified_port_connection = True
    assert symbol.driver_evidence is DriverEvidence.UNSEEN
    assert not symbol.driver_evidence.is_driver_established
