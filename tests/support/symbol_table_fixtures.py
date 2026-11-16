"""Helpers shared by the node-rule tests."""

import pytest
from unittest.mock import Mock
from src.pkg.semantic.scope import Scope
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.vnodes.base_vnode import Location


@pytest.fixture
def mock_location() -> Location:
    """Fixture for a mock Location object."""
    loc = Mock(spec=Location)
    loc.line = 42
    loc.col = 10
    return loc


@pytest.fixture
def scope() -> Scope:
    """Fixture for a Scope instance."""
    return Scope(kind="module", name="test_module")


@pytest.fixture
def symbol_table() -> SymbolTable:
    """Fixture for a SymbolTable instance."""
    return SymbolTable()
