import pytest
from unittest.mock import Mock

from src.pkg.ast.symbol_table import Symbol, Scope, SymbolTable
from src.pkg.vnodes.base_vnode import Location


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
        """Test that lookup() returns None when symbol is not found anywhere in the hierarchy."""
        parent = Scope(kind="module", name="parent")
        child = Scope(kind="block", name="child")
        child.set_parent(parent)

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
        st._scope_stack = []

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
        
        # Create always block (new_scope sets parent=top automatically)
        always = st.new_scope(kind="always")

        # Create internal variable in always block
        temp = Symbol(name="temp", kind="variable")
        temp.add_declaration(mock_location)
        always.define(temp)

        # Verify lookups
        assert st.lookup_from_scope("clk", always) == clk  # From parent
        assert always.lookup("temp") == temp               # Local
        assert top.lookup("temp") is None                  # Not visible upward
        assert top.lookup("clk") == clk                    # Local


# ---------------------------------------------------------------------------
# New: Scope.children and set_parent registration
# ---------------------------------------------------------------------------

class TestScopeChildren:
    """Tests for Scope.children tracking via set_parent."""

    def test_scope_initializes_with_empty_children(self) -> None:
        scope = Scope(kind="module", name="top")
        assert scope.children == []

    def test_set_parent_registers_child_in_parent_children(self) -> None:
        parent = Scope(kind="module", name="top")
        child = Scope(kind="always")
        child.set_parent(parent)
        assert child in parent.children

    def test_set_parent_does_not_duplicate_children(self) -> None:
        parent = Scope(kind="module", name="top")
        child = Scope(kind="always")
        child.set_parent(parent)
        child.set_parent(parent)
        assert parent.children.count(child) == 1

    def test_set_parent_none_does_not_add_to_children(self) -> None:
        parent = Scope(kind="module", name="top")
        child = Scope(kind="always")
        child.set_parent(None)
        assert parent.children == []

    def test_new_scope_registers_child_with_parent(self, symbol_table=None) -> None:
        st = SymbolTable()
        module = st.new_scope(kind="module", name="top")
        always = st.new_scope(kind="always")
        assert always in module.children

    def test_multiple_children_all_registered(self) -> None:
        st = SymbolTable()
        module = st.new_scope(kind="module", name="top")
        a1 = st.new_scope(kind="always")
        st.pop_scope()
        a2 = st.new_scope(kind="always")
        assert a1 in module.children
        assert a2 in module.children


# ---------------------------------------------------------------------------
# File tracking
# ---------------------------------------------------------------------------

class TestFileTracking:
    """Tests for set_current_file and file stamping on scopes."""

    def test_set_current_file_updates_attribute(self) -> None:
        st = SymbolTable()
        st.set_current_file("a.sv")
        assert st.current_file == "a.sv"

    def test_new_scope_stamps_current_file(self) -> None:
        st = SymbolTable()
        st.set_current_file("a.sv")
        scope = st.new_scope(kind="module", name="top")
        assert scope.file == "a.sv"

    def test_file_updates_between_files(self) -> None:
        st = SymbolTable()
        st.set_current_file("a.sv")
        scope_a = st.new_scope(kind="module", name="a")
        st.pop_scope()
        st.set_current_file("b.sv")
        scope_b = st.new_scope(kind="module", name="b")
        assert scope_a.file == "a.sv"
        assert scope_b.file == "b.sv"

    def test_scope_file_is_none_before_set(self) -> None:
        st = SymbolTable()
        scope = st.new_scope(kind="module", name="top")
        assert scope.file is None


# ---------------------------------------------------------------------------
# Module registration
# ---------------------------------------------------------------------------

class TestModuleRegistry:
    """Tests for register_module, lookup_module, is_duplicate_module."""

    def test_register_module_stores_scope(self) -> None:
        st = SymbolTable()
        scope = st.new_scope(kind="module", name="top")
        st.register_module("top", scope)
        assert st.lookup_module("top") is scope

    def test_lookup_module_returns_none_for_unknown(self) -> None:
        st = SymbolTable()
        assert st.lookup_module("missing") is None

    def test_register_module_appends_on_duplicate(self) -> None:
        st = SymbolTable()
        s1 = st.new_scope(kind="module", name="foo")
        st.pop_scope()
        st.set_current_file("b.sv")
        s2 = st.new_scope(kind="module", name="foo")
        st.register_module("foo", s1)
        st.register_module("foo", s2)
        assert len(st.modules["foo"]) == 2

    def test_lookup_module_returns_first_on_duplicate(self) -> None:
        st = SymbolTable()
        s1 = st.new_scope(kind="module", name="foo")
        st.pop_scope()
        s2 = st.new_scope(kind="module", name="foo")
        st.register_module("foo", s1)
        st.register_module("foo", s2)
        assert st.lookup_module("foo") is s1

    def test_is_duplicate_module_false_for_single(self) -> None:
        st = SymbolTable()
        scope = st.new_scope(kind="module", name="foo")
        st.register_module("foo", scope)
        assert st.is_duplicate_module("foo") is False

    def test_is_duplicate_module_true_for_duplicate(self) -> None:
        st = SymbolTable()
        s1 = st.new_scope(kind="module", name="foo")
        st.pop_scope()
        s2 = st.new_scope(kind="module", name="foo")
        st.register_module("foo", s1)
        st.register_module("foo", s2)
        assert st.is_duplicate_module("foo") is True

    def test_is_duplicate_module_false_for_missing(self) -> None:
        st = SymbolTable()
        assert st.is_duplicate_module("nope") is False


# ---------------------------------------------------------------------------
# lookup_downward
# ---------------------------------------------------------------------------

class TestLookupDownward:
    """Tests for SymbolTable.lookup_downward."""

    def _sym(self, name: str) -> Symbol:
        s = Symbol(name=name, kind="wire")
        s.add_declaration({"line": 1, "col": 1})
        return s

    def test_finds_symbol_in_direct_child(self) -> None:
        st = SymbolTable()
        module = st.new_scope(kind="module", name="top")
        child = st.new_scope(kind="always")
        sym = self._sym("clk")
        child.define(sym)
        st.pop_scope()  # exit always
        st.pop_scope()  # exit module

        found = st.lookup_downward("clk", module)
        assert found is sym

    def test_finds_symbol_in_grandchild(self) -> None:
        st = SymbolTable()
        module = st.new_scope(kind="module", name="top")
        child = st.new_scope(kind="always")
        grandchild = st.new_scope(kind="block")
        sym = self._sym("x")
        grandchild.define(sym)
        st.pop_scope()
        st.pop_scope()
        st.pop_scope()

        found = st.lookup_downward("x", module)
        assert found is sym

    def test_does_not_find_in_from_scope_itself(self) -> None:
        st = SymbolTable()
        module = st.new_scope(kind="module", name="top")
        sym = self._sym("x")
        module.define(sym)

        found = st.lookup_downward("x", module)
        assert found is None

    def test_returns_none_when_not_found(self) -> None:
        st = SymbolTable()
        module = st.new_scope(kind="module", name="top")
        st.new_scope(kind="always")

        found = st.lookup_downward("missing", module)
        assert found is None

    def test_uses_current_scope_when_no_from_scope(self) -> None:
        st = SymbolTable()
        module = st.new_scope(kind="module", name="top")
        child = st.new_scope(kind="always")
        sym = self._sym("y")
        child.define(sym)
        # current scope is child; lookup_downward from child finds nothing (no grandchildren)
        found = st.lookup_downward("y")
        assert found is None


# ---------------------------------------------------------------------------
# lookup_sibling
# ---------------------------------------------------------------------------

class TestLookupSibling:
    """Tests for SymbolTable.lookup_sibling."""

    def _sym(self, name: str) -> Symbol:
        s = Symbol(name=name, kind="wire")
        s.add_declaration({"line": 1, "col": 1})
        return s

    def test_finds_symbol_in_sibling_scope(self) -> None:
        st = SymbolTable()
        module = st.new_scope(kind="module", name="top")
        sibling_a = st.new_scope(kind="always")
        sym = self._sym("clk")
        sibling_a.define(sym)
        st.pop_scope()
        sibling_b = st.new_scope(kind="always")

        found = st.lookup_sibling("clk", sibling_b)
        assert found is sym

    def test_does_not_find_in_self(self) -> None:
        st = SymbolTable()
        module = st.new_scope(kind="module", name="top")
        only_child = st.new_scope(kind="always")
        sym = self._sym("x")
        only_child.define(sym)

        # only_child has no siblings, so nothing found
        found = st.lookup_sibling("x", only_child)
        assert found is None

    def test_returns_none_when_no_parent(self) -> None:
        st = SymbolTable()
        orphan = Scope(kind="module", name="orphan")
        found = st.lookup_sibling("x", orphan)
        assert found is None

    def test_returns_none_when_symbol_not_in_any_sibling(self) -> None:
        st = SymbolTable()
        module = st.new_scope(kind="module", name="top")
        st.new_scope(kind="always")
        st.pop_scope()
        sibling_b = st.new_scope(kind="always")

        found = st.lookup_sibling("missing", sibling_b)
        assert found is None

    def test_uses_current_scope_when_no_from_scope(self) -> None:
        st = SymbolTable()
        module = st.new_scope(kind="module", name="top")
        sibling_a = st.new_scope(kind="always")
        sym = self._sym("sig")
        sibling_a.define(sym)
        st.pop_scope()
        st.new_scope(kind="always")  # now current scope

        found = st.lookup_sibling("sig")
        assert found is sym


# ---------------------------------------------------------------------------
# lookup_qualified
# ---------------------------------------------------------------------------

class TestLookupQualified:
    """Tests for SymbolTable.lookup_qualified."""

    def _sym(self, name: str) -> Symbol:
        s = Symbol(name=name, kind="wire")
        s.add_declaration({"line": 1, "col": 1})
        return s

    def test_navigates_to_nested_scope_and_finds_symbol(self) -> None:
        st = SymbolTable()
        top = st.new_scope(kind="module", name="top")
        sub = st.new_scope(kind="module", name="sub")
        sym = self._sym("clk")
        sub.define(sym)

        found = st.lookup_qualified(["top", "sub", "clk"])
        assert found is sym

    def test_returns_none_on_bad_intermediate_segment(self) -> None:
        st = SymbolTable()
        st.new_scope(kind="module", name="top")

        found = st.lookup_qualified(["top", "nonexistent", "clk"])
        assert found is None

    def test_returns_none_on_empty_path(self) -> None:
        st = SymbolTable()
        found = st.lookup_qualified([])
        assert found is None

    def test_single_segment_looks_up_in_global(self) -> None:
        st = SymbolTable()
        sym = self._sym("g")
        st.global_scope.define(sym)

        found = st.lookup_qualified(["g"])
        assert found is sym

    def test_returns_none_when_symbol_missing_in_target_scope(self) -> None:
        st = SymbolTable()
        st.new_scope(kind="module", name="top")

        found = st.lookup_qualified(["top", "missing"])
        assert found is None


# ---------------------------------------------------------------------------
# lookup_global
# ---------------------------------------------------------------------------

class TestLookupGlobal:
    """Tests for SymbolTable.lookup_global."""

    def _sym(self, name: str) -> Symbol:
        s = Symbol(name=name, kind="wire")
        s.add_declaration({"line": 1, "col": 1})
        return s

    def test_finds_symbol_in_global_scope(self) -> None:
        st = SymbolTable()
        sym = self._sym("g")
        st.global_scope.define(sym)

        found = st.lookup_global("g")
        assert found is sym

    def test_finds_symbol_in_nested_scope(self) -> None:
        st = SymbolTable()
        st.new_scope(kind="module", name="top")
        always = st.new_scope(kind="always")
        sym = self._sym("deep")
        always.define(sym)

        found = st.lookup_global("deep")
        assert found is sym

    def test_finds_symbol_in_sibling_module(self) -> None:
        st = SymbolTable()
        mod_a = st.new_scope(kind="module", name="a")
        sym = self._sym("sig")
        mod_a.define(sym)
        st.pop_scope()
        st.new_scope(kind="module", name="b")

        found = st.lookup_global("sig")
        assert found is sym

    def test_returns_none_when_not_found_anywhere(self) -> None:
        st = SymbolTable()
        st.new_scope(kind="module", name="top")

        found = st.lookup_global("nowhere")
        assert found is None
