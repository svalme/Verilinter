from src.pkg.semantic.scope import Scope
from src.pkg.semantic.symbol import Symbol


def _symbol_in(scope: Scope) -> Symbol:
    symbol = Symbol(name="s", kind="variable")
    scope.define(symbol)
    return symbol


def test_plain_module_signal_has_no_unseen_driver() -> None:
    assert not _symbol_in(Scope("module", "m")).may_have_unseen_driver


def test_signal_in_an_unclassified_port_connection_may_have_an_unseen_driver() -> None:
    symbol = _symbol_in(Scope("module", "m"))
    symbol.in_unclassified_port_connection = True
    assert symbol.may_have_unseen_driver


def test_member_of_an_interface_with_no_visible_user_may_have_an_unseen_driver() -> None:
    interface = Scope("module", "bus_if")
    interface.is_interface = True
    assert _symbol_in(interface).may_have_unseen_driver


def test_member_of_an_interface_with_a_visible_user_has_no_unseen_driver() -> None:
    interface = Scope("module", "bus_if")
    interface.is_interface = True
    interface.has_visible_interface_users = True
    assert not _symbol_in(interface).may_have_unseen_driver


def test_signal_in_a_generate_block_of_an_interface_is_a_member() -> None:
    interface = Scope("module", "bus_if")
    interface.is_interface = True
    block = Scope("generate_block", "g")
    block.set_parent(interface)
    assert _symbol_in(block).may_have_unseen_driver
