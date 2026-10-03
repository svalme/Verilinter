from src.pkg.parser.parse import parse_text
from src.pkg.parser.types import FunctionDeclarationNode
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *


class TestFunctionDeclarationHandler:
    """A `function`/`task` declaration must get its own nested scope, distinct
    from the enclosing module scope."""

    def test_function_registers_is_registered_with_dispatch(self) -> None:
        assert FunctionDeclarationNode in dispatch._registry

    def test_function_gets_its_own_scope(self) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text(
            "module m; function automatic int add1(input int a); add1 = a + 1; endfunction endmodule"
        )
        walker.walk(tree.root, tree, ctx, symbol_table)

        module_scope = symbol_table.lookup_module("m")
        assert module_scope is not None
        assert "a" not in module_scope.symbols

        function_scopes = [c for c in module_scope.children if c.kind == "function"]
        assert len(function_scopes) == 1
        assert function_scopes[0].name == "add1"
        assert "a" in function_scopes[0].symbols

    def test_task_gets_its_own_scope(self) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text(
            "module m; task automatic do_thing(input int x); x = x; endtask endmodule"
        )
        walker.walk(tree.root, tree, ctx, symbol_table)

        module_scope = symbol_table.lookup_module("m")
        assert module_scope is not None
        assert "x" not in module_scope.symbols

        task_scopes = [c for c in module_scope.children if c.kind == "task"]
        assert len(task_scopes) == 1
        assert task_scopes[0].name == "do_thing"
        assert "x" in task_scopes[0].symbols

    def test_reused_parameter_name_across_independent_functions_does_not_collide(self) -> None:
        """`x` is an ordinary parameter name in two unrelated functions -- each
        should get its own independent declaration, not merge into one symbol
        with two declarations (which REDECLARED_VARIABLE would flag)."""
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text(
            """
            module m;
               function automatic int f1(input int x); f1 = x + 1; endfunction
               function automatic int f2(input int x); f2 = x + 2; endfunction
            endmodule
            """
        )
        walker.walk(tree.root, tree, ctx, symbol_table)

        module_scope = symbol_table.lookup_module("m")
        assert module_scope is not None
        function_scopes = {c.name: c for c in module_scope.children if c.kind == "function"}
        assert set(function_scopes) == {"f1", "f2"}
        assert len(function_scopes["f1"].symbols["x"].declarations) == 1
        assert len(function_scopes["f2"].symbols["x"].declarations) == 1

    def test_module_level_signal_still_resolves_from_inside_function(self) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text(
            """
            module m;
              reg [7:0] counter;
              function automatic int add1(input int a); add1 = a + counter; endfunction
            endmodule
            """
        )
        walker.walk(tree.root, tree, ctx, symbol_table)

        module_scope = symbol_table.lookup_module("m")
        assert module_scope is not None
        counter = module_scope.lookup("counter")
        assert counter is not None
        assert counter.read_count == 1
