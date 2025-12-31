import pytest
from unittest.mock import Mock

from src.pkg.ast.symbol_table import Symbol, Scope, SymbolTable
from src.pkg.vnode.base_vnode import Location


@pytest.fixture
def mock_location() -> Location:
    """Fixture for a mock Location object."""
    loc = Mock(spec=Location)
    loc.line = 42
    loc.col = 10
    return loc


@pytest.fixture
def symbol(mock_location: Location) -> Symbol:
    """Fixture for a Symbol instance."""
    st = Symbol(name="test_var", kind="variable")
    st.add_declaration(mock_location)
    return st


@pytest.fixture
def scope() -> Scope:
    """Fixture for a Scope instance."""
    return Scope(kind="module", name="test_module")


@pytest.fixture
def symbol_table() -> SymbolTable:
    """Fixture for a SymbolTable instance."""
    return SymbolTable()


class TestSymbol:
    """Test cases for the Symbol class."""

    def test_symbol_initializes_with_correct_attributes(self, mock_location: Location) -> None:
        """Test that Symbol initializes with correct attributes."""
        sym = Symbol(name="my_var", kind="wire")
        sym.add_declaration(mock_location)
        
        assert sym.name == "my_var"
        assert sym.kind == "wire"
        assert sym.declarations == [mock_location]
        assert sym.uses == []
        assert sym.scope is None

    def test_symbol_initializes_with_implicit_false(self, mock_location: Location) -> None:
        """Test that Symbol initializes with is_implicit=False."""
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration(mock_location)
        
        assert sym.is_implicit is False
        assert sym.is_read is False
        assert sym.is_written is False

    def test_set_scope_assigns_scope(self, symbol: Symbol, scope: Scope) -> None:
        """Test that set_scope() assigns a Scope to the symbol."""
        symbol.set_scope(scope)
        
        assert symbol.scope == scope

    def test_add_declaration_appends_location(self, symbol: Symbol, mock_location: Location) -> None:
        """Test that add_declaration() appends a location."""
        new_loc = Mock(spec=Location)
        new_loc.line = 50
        new_loc.col = 5
        
        symbol.add_declaration(new_loc)
        
        assert len(symbol.declarations) == 2
        assert symbol.declarations[1] == new_loc

    def test_add_use_appends_location(self, symbol: Symbol, mock_location: Location) -> None:
        """Test that add_use() appends a location to uses."""
        symbol.add_use(mock_location)
        
        assert len(symbol.uses) == 1
        assert symbol.uses[0] == mock_location

    def test_add_use_with_read_flag(self, symbol: Symbol, mock_location: Location) -> None:
        """Test that add_use() with read=True sets is_read."""
        symbol.add_use(mock_location, read=True)
        
        assert symbol.is_read is True
        assert symbol.is_written is False

    def test_add_use_with_write_flag(self, symbol: Symbol, mock_location: Location) -> None:
        """Test that add_use() with write=True sets is_written."""
        symbol.add_use(mock_location, write=True)
        
        assert symbol.is_written is True
        assert symbol.is_read is False

    def test_add_use_with_read_and_write_flags(self, symbol: Symbol, mock_location: Location) -> None:
        """Test that add_use() with both flags sets both."""
        symbol.add_use(mock_location, read=True, write=True)
        
        assert symbol.is_read is True
        assert symbol.is_written is True

    def test_add_use_accumulates_flags(self, symbol: Symbol, mock_location: Location) -> None:
        """Test that multiple add_use() calls accumulate flags."""
        loc1 = Mock(spec=Location)
        loc2 = Mock(spec=Location)
        
        symbol.add_use(loc1, read=True)
        symbol.add_use(loc2, write=True)
        
        assert symbol.is_read is True
        assert symbol.is_written is True
        assert len(symbol.uses) == 2

    def test_is_declared_true_when_has_declarations(self, symbol: Symbol) -> None:
        """Test that is_declared returns True when symbol has declarations."""
        assert symbol.is_declared is True

    def test_is_declared_false_when_no_declarations(self, mock_location: Location) -> None:
        """Test that is_declared returns False when symbol has no declarations."""
        sym = Symbol(name="x", kind="variable")
        
        assert sym.is_declared is False

    def test_is_declared_true_after_add_declaration(self, mock_location: Location) -> None:
        """Test that is_declared returns True after add_declaration()."""
        sym = Symbol(name="x", kind="variable")
        assert sym.is_declared is False
        sym.add_declaration(mock_location)
        assert sym.is_declared is True


class TestScope:
    """Test cases for the Scope class."""

    def test_scope_initializes_with_correct_attributes(self) -> None:
        """Test that Scope initializes with correct attributes."""
        scope = Scope(kind="module", name="top")
        
        assert scope.kind == "module"
        assert scope.name == "top"
        assert scope.parent is None
        assert scope.symbols == {}

    def test_scope_initializes_without_name(self) -> None:
        """Test that Scope can be initialized without a name."""
        scope = Scope(kind="always")
        
        assert scope.kind == "always"
        assert scope.name is None

    def test_scope_initializes_with_parent(self) -> None:
        """Test that Scope can be initialized with a parent."""
        parent = Scope(kind="module", name="parent")
        child = Scope(kind="block", name="child")
        child.set_parent(parent)
        
        assert child.parent == parent

    def test_define_adds_symbol_to_scope(self, scope: Scope, symbol: Symbol) -> None:
        """Test that define() adds a Symbol to the scope."""
        scope.define(symbol)
        
        assert "test_var" in scope.symbols
        assert scope.symbols["test_var"] == symbol

    """
    def test_define_overwrites_existing_symbol(self, scope: Scope, mock_location: Location) -> None:
        # Test that define() overwrites an existing symbol with the same name.
        sym1 = Symbol(name="x", kind="variable")
        sym1.add_declaration(mock_location)
        sym2 = Symbol(name="x", kind="wire")
        sym2.add_declaration(mock_location)
        
        scope.define(sym1)
        assert scope.symbols["x"] == sym1
        
        scope.define(sym2)
        assert scope.symbols["x"] == sym2
    """
        
    def test_lookup_finds_symbol_in_current_scope(self, scope: Scope, symbol: Symbol) -> None:
        """Test that lookup() finds a Symbol in the current scope."""
        scope.define(symbol)
        
        found = scope.lookup("test_var")
        
        assert found == symbol

    def test_lookup_returns_none_for_missing_symbol(self, scope: Scope) -> None:
        """Test that lookup() returns None for a missing symbol."""
        found = scope.lookup("nonexistent")
        
        assert found is None

    def test_lookup_traverses_parent_scope(self, mock_location: Location) -> None:
        """Test that SymbolTable.lookup() traverses the parent scope hierarchy."""
        parent = Scope(kind="module", name="parent")
        child = Scope(kind="block", name="child")
        child.set_parent(parent)
        
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration(mock_location)
        parent.define(sym)

        sym_tab = SymbolTable()
        sym_tab.add_scope(parent)
        sym_tab.add_scope(child)
        
        found = sym_tab.lookup("x")
        
        assert found == sym

    def test_lookup_prefers_local_symbol_over_parent(self, mock_location: Location) -> None:
        """Test that lookup() returns local symbol before checking parent."""
        parent = Scope(kind="module", name="parent")
        child = Scope(kind="block", name="child")

        sym_parent = Symbol(name="x", kind="wire")
        sym_parent.add_declaration(mock_location)
        sym_child = Symbol(name="x", kind="variable")
        sym_child.add_declaration(mock_location)

        parent.define(sym_parent)
        child.define(sym_child)
        
        found = child.lookup("x")
        
        assert found == sym_child

    def test_lookup_returns_none_when_not_in_hierarchy(self, mock_location: Location) -> None:
        """Test that lookup() returns None when symbol is not in hierarchy."""
        parent = Scope(kind="module", name="parent")
        child = Scope(kind="block", name="child")
        
        symbol_table = SymbolTable()
        symbol_table.add_scope(parent)
        symbol_table.add_scope(child)

        found = symbol_table.lookup("nonexistent")
        
        assert found is None


class TestSymbolTable:
    """Test cases for the SymbolTable class."""

    def test_symbol_table_initializes_with_global_scope(self, symbol_table: SymbolTable) -> None:
        """Test that SymbolTable initializes with a global scope."""
        assert symbol_table.global_scope is not None
        assert symbol_table.global_scope.kind == "global"
        assert symbol_table.scopes == [symbol_table.global_scope]

    def test_new_scope_creates_scope_with_global_parent(
        self, symbol_table: SymbolTable
    ) -> None:
        """Test that new_scope() creates a scope with global_scope as default parent."""
        scope = symbol_table.new_scope(kind="module", name="top")
        
        assert scope.kind == "module"
        assert scope.name == "top"
        assert scope.parent == symbol_table.global_scope
        assert scope in symbol_table.scopes

    def test_new_scope_with_custom_parent(self, symbol_table: SymbolTable) -> None:
        """Test that new_scope() accepts a custom parent."""
        parent = symbol_table.new_scope(kind="module", name="parent")
        child = symbol_table.new_scope(kind="block", name="child", parent=parent)
        
        assert child.parent == parent
        assert child in symbol_table.scopes
        assert len(symbol_table.scopes) == 3  # global + parent + child

    def test_new_scope_without_name(self, symbol_table: SymbolTable) -> None:
        """Test that new_scope() can create a scope without a name."""
        scope = symbol_table.new_scope(kind="always")
        
        assert scope.kind == "always"
        assert scope.name is None

    def test_current_scope_returns_most_recent(self, symbol_table: SymbolTable) -> None:
        """Test that current_scope() returns the most recently created scope."""
        assert symbol_table.current_scope() == symbol_table.global_scope
        
        scope1 = symbol_table.new_scope(kind="module", name="m1")
        assert symbol_table.current_scope() == scope1
        
        scope2 = symbol_table.new_scope(kind="module", name="m2")
        assert symbol_table.current_scope() == scope2

    def test_current_scope_returns_none_on_empty(self) -> None:
        """Test that current_scope() returns None when scopes is empty."""
        st = SymbolTable()
        st.scopes = []
        
        assert st.current_scope() is None

    def test_symbol_table_maintains_scope_list(self, symbol_table: SymbolTable) -> None:
        """Test that SymbolTable maintains a list of all scopes."""
        initial_count = len(symbol_table.scopes)
        
        symbol_table.new_scope(kind="module", name="m1")
        assert len(symbol_table.scopes) == initial_count + 1
        
        symbol_table.new_scope(kind="block", name="b1")
        assert len(symbol_table.scopes) == initial_count + 2

    def test_nested_scope_symbol_lookup(self, symbol_table: SymbolTable, mock_location: Location) -> None:
        """Test that symbols can be looked up across nested scopes."""
        # Create module scope
        module = symbol_table.new_scope(kind="module", name="top")
        
        # Define symbol in module
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration(mock_location)
        module.define(sym)
        
        # Create block scope within module
        block = symbol_table.new_scope(kind="always")
        block.set_parent(module)
        
        # Block should be able to find symbol from module
        found = symbol_table.lookup("x")
        assert found == sym

    def test_symbol_table_integration_scenario(self, mock_location: Location) -> None:
        """Integration test: create nested scopes and manage symbols."""
        st = SymbolTable()
        
        # Create top-level module
        top = st.new_scope(kind="module", name="top")
        
        # Define global variables
        clk = Symbol(name="clk", kind="wire")
        clk.add_declaration(mock_location)
        top.define(clk)
        
        # Create always block
        always = st.new_scope(kind="always")
        #always.set_parent(top)
        #st.add_scope(always)
        
        # Create internal variable in always block
        temp = Symbol(name="temp", kind="variable")
        temp.add_declaration(mock_location)
        always.define(temp)
        
        # Verify lookups
        assert st.lookup_from_scope("clk", always) == clk  # From parent
        #assert always.lookup("temp") == temp  # Local
        #assert top.lookup("temp") is None  # Not visible upward
        #assert top.lookup("clk") == clk  # Local
