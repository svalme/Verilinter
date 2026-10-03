from src.pkg.parser.parse import parse_text
from src.pkg.parser.types import PackageImportDeclarationNode
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *


class TestPackageDeclarationRegistration:
    """A `package` declaration must register into SymbolTable.packages, not
    .modules -- pyslang gives both the same wrapper class, distinguishable
    only by `.kind`."""

    def test_package_registers_its_own_scope(self) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text("package my_pkg; parameter int FOO = 1; endpackage")
        walker.walk(tree.root, tree, ctx, symbol_table)

        package_scope = symbol_table.lookup_package("my_pkg")
        assert package_scope is not None
        assert package_scope.kind == "package"
        assert "FOO" in package_scope.symbols

    def test_package_does_not_register_as_module(self) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text("package my_pkg; endpackage")
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert symbol_table.lookup_module("my_pkg") is None
        assert "my_pkg" not in symbol_table.modules

    def test_module_still_registers_as_module(self) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text("module top; endmodule")
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert symbol_table.lookup_module("top") is not None
        assert symbol_table.lookup_package("top") is None


class TestPackageImportHandler:
    def test_wildcard_import_syntax_is_registered_with_dispatch(self) -> None:
        assert PackageImportDeclarationNode in dispatch._registry

    def test_wildcard_import_records_none_as_imported_name(self) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text("module top; import my_pkg::*; endmodule")
        walker.walk(tree.root, tree, ctx, symbol_table)

        module_scope = symbol_table.lookup_module("top")
        assert module_scope is not None
        assert module_scope.imports == [("my_pkg", None)]

    def test_explicit_import_records_imported_name(self) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text("module top; import my_pkg::FOO; endmodule")
        walker.walk(tree.root, tree, ctx, symbol_table)

        module_scope = symbol_table.lookup_module("top")
        assert module_scope is not None
        assert module_scope.imports == [("my_pkg", "FOO")]

    def test_multiple_imports_all_recorded_in_order(self) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text(
            "module top; import pkg_a::*; import pkg_b::BAR; endmodule"
        )
        walker.walk(tree.root, tree, ctx, symbol_table)

        module_scope = symbol_table.lookup_module("top")
        assert module_scope is not None
        assert module_scope.imports == [("pkg_a", None), ("pkg_b", "BAR")]

    def test_header_import_is_recorded_on_the_module_scope(self) -> None:
        """`module top import pkg::*; #(...) (...);` puts the import inside the
        module header, not the body -- must still land on the module's own
        scope since the whole header is a descendant of the same declaration."""
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text(
            "module top import my_pkg::*; (input logic clk_i); endmodule"
        )
        walker.walk(tree.root, tree, ctx, symbol_table)

        module_scope = symbol_table.lookup_module("top")
        assert module_scope is not None
        assert module_scope.imports == [("my_pkg", None)]
