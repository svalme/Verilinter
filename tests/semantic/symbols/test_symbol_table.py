"""SymbolTable: files, module and package registries."""
from src.pkg.semantic.symbol import Symbol
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.vnodes.base_vnode import Location
from tests.support.symbol_table_fixtures import mock_location, scope, symbol_table


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

    def test_symbol_table_maintains_scope_list(self, symbol_table: SymbolTable) -> None:
        """Test that SymbolTable maintains a list of all scopes."""
        initial_count = len(symbol_table.scopes)
        
        symbol_table.new_scope(kind="module", name="m1")
        assert len(symbol_table.scopes) == initial_count + 1
        
        symbol_table.new_scope(kind="block", name="b1")
        assert len(symbol_table.scopes) == initial_count + 2

    def test_symbol_table_integration_scenario(self, mock_location: Location) -> None:
        """Integration test: create nested scopes and manage symbols."""
        st = SymbolTable()
        
        # Create top-level module
        top = st.new_scope(kind="module", name="top")
        
        # Define global variables
        clk = Symbol(name="clk", kind="variable")
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
# Package registration (kept separate from the module registry -- see
# module_declaration_handler.py's package/module branch)
# ---------------------------------------------------------------------------

class TestPackageRegistry:
    """Tests for register_package, lookup_package."""

    def test_register_package_stores_scope(self) -> None:
        st = SymbolTable()
        scope = st.new_scope(kind="package", name="my_pkg")
        st.register_package("my_pkg", scope)
        assert st.lookup_package("my_pkg") is scope

    def test_lookup_package_returns_none_for_unknown(self) -> None:
        st = SymbolTable()
        assert st.lookup_package("missing") is None

    def test_registering_a_package_does_not_populate_modules(self) -> None:
        """A package must never pollute the module registry (UNDEFINED_MODULE/
        DUPLICATE_MODULE consume `modules` directly)."""
        st = SymbolTable()
        scope = st.new_scope(kind="package", name="foo")
        st.register_package("foo", scope)
        assert st.lookup_module("foo") is None
        assert "foo" not in st.modules

    def test_package_and_module_sharing_a_name_do_not_collide(self) -> None:
        st = SymbolTable()
        package_scope = st.new_scope(kind="package", name="foo")
        st.pop_scope()
        module_scope = st.new_scope(kind="module", name="foo")
        st.register_package("foo", package_scope)
        st.register_module("foo", module_scope)
        assert st.is_duplicate_module("foo") is False
        assert st.lookup_module("foo") is module_scope
        assert st.lookup_package("foo") is package_scope
