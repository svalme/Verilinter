import pyslang as sl

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *


class TestForLoopStatementHandler:
    """A procedural `for` loop's inline-declared loop variable must get its own
    nested scope, distinct from the enclosing block/module scope."""

    def test_for_loop_is_registered_with_dispatch(self) -> None:
        assert sl.ForLoopStatementSyntax in dispatch._registry

    def test_inline_loop_variable_gets_its_own_scope(self) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(
            "module m; initial begin for (int i = 0; i < 4; i = i + 1) begin end end endmodule"
        )
        walker.walk(tree.root, tree, ctx, symbol_table)

        module_scope = symbol_table.lookup_module("m")
        assert module_scope is not None
        assert "i" not in module_scope.symbols

    def test_reused_loop_variable_across_independent_loops_does_not_collide(self) -> None:
        """`i` declared inline in two unrelated `for` loops in the same module
        -- each should get its own independent declaration, not merge into one
        symbol with two declarations (which REDECLARED_VARIABLE would flag)."""
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(
            """
            module m;
              initial begin
                for (int i = 0; i < 4; i = i + 1) begin end
                for (int i = 0; i < 8; i = i + 1) begin end
              end
            endmodule
            """
        )
        walker.walk(tree.root, tree, ctx, symbol_table)

        for_scopes = [s for s in symbol_table.scopes if s.kind == "for"]
        assert len(for_scopes) == 2
        for scope in for_scopes:
            assert len(scope.symbols["i"].declarations) == 1

    def test_module_level_signal_still_resolves_from_inside_loop_body(self) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(
            """
            module m;
              reg [7:0] counter;
              initial begin
                for (int i = 0; i < 4; i = i + 1) begin
                  counter = counter + i;
                end
              end
            endmodule
            """
        )
        walker.walk(tree.root, tree, ctx, symbol_table)

        module_scope = symbol_table.lookup_module("m")
        assert module_scope is not None
        counter = module_scope.lookup("counter")
        assert counter is not None
        assert counter.read_count == 1
        assert counter.write_count == 1
