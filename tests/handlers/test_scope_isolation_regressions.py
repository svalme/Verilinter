"""Scope regressions need both legal reuse and genuinely invalid-use controls."""
import pytest
import pyslang as sl

from src.pkg.handlers.register_handlers import *
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.parse_diagnostics import assert_no_parse_errors
from tests.support.lint_harness import run_inline_lint_case


def walk(source):
    tree = sl.SyntaxTree.fromText(source)
    assert_no_parse_errors("scope regression", tree)
    table = SymbolTable()
    Walker(dispatch).walk(tree.root, tree, Context(scope=table.global_scope), table)
    return table


def test_function_shadowing_keeps_module_and_function_uses_separate():
    table = walk("""
        module m(input int x, output int y);
          function automatic int f(input int x); f = x + 1; endfunction
          assign y = x;
        endmodule
    """)
    module = table.lookup_module("m")
    function = next(s for s in module.children if s.kind == "function")
    assert module.symbols["x"] is not function.symbols["x"]
    assert module.symbols["x"].read_count == 1
    assert function.symbols["x"].read_count == 1
    assert "y" in module.symbols  # Scope restored after the function.


def test_nested_loops_shadow_and_restore_outer_loop_variable():
    table = walk("""
        module m; int sink;
          initial begin
            for (int i = 0; i < 4; i = i + 1) begin
              for (int i = 0; i < 2; i = i + 1) sink = i;
              sink = i;
            end
          end
        endmodule
    """)
    scopes = [s for s in table.scopes if s.kind == "for"]
    assert len(scopes) == 2
    assert scopes[1].parent is scopes[0]
    assert scopes[0].symbols["i"] is not scopes[1].symbols["i"]
    assert scopes[0].symbols["i"].read_count == 3
    assert scopes[1].symbols["i"].read_count == 3


@pytest.mark.parametrize("declaration", [
    "function automatic int f(input int local_x); return local_x; endfunction",
    "task automatic t(input int local_x); $display(local_x); endtask",
    "initial for (int local_x = 0; local_x < 2; local_x++) begin end",
])
def test_local_name_does_not_escape_to_module(declaration):
    result = run_inline_lint_case({"top.sv": f"""
        module m(output int y);
          {declaration}
          assign y = local_x;
        endmodule
    """})
    result.expect_code_once("NO_IMPLICIT_NET")


def test_assignment_to_function_return_name_is_not_an_implicit_net():
    result = run_inline_lint_case({"top.sv": """
        module m;
          function automatic int f(input int x); f = x; endfunction
        endmodule
    """})
    result.expect_no_code("NO_IMPLICIT_NET")
    result.expect_no_code("NO_WRITE_ONLY_VARIABLE")


def test_function_input_is_available_on_entry():
    result = run_inline_lint_case({"top.sv": """
        module m;
          function automatic int f(input int x); return x + 1; endfunction
        endmodule
    """})
    result.expect_no_code("READ_BEFORE_WRITE")
    result.expect_no_code("NO_UNDRIVEN_SIGNAL")
    result.expect_no_code("UNUSED_VARIABLE")


@pytest.mark.parametrize("aggregate", ["struct", "union"])
def test_aggregate_fields_are_separate_from_each_other_and_module(aggregate):
    table = walk(f"""
        module m;
          typedef {aggregate} packed {{ int x; }} a_t;
          typedef {aggregate} packed {{ int x; }} b_t;
          int x;
        endmodule
    """)
    module = table.lookup_module("m")
    assert len(module.symbols["x"].declarations) == 1
    fields = [s.symbols["x"] for s in table.scopes if s.kind == "aggregate"]
    assert len(fields) == 2
    assert all(s.kind == "field" and len(s.declarations) == 1 for s in fields)


def test_generate_loop_names_can_be_reused_but_cannot_escape():
    source = """
        module m(output int y);
          for(genvar i=0; i<2; i++) begin:a wire x = i; end
          for(genvar i=0; i<2; i++) begin:b wire x = i; end
          assign y = i;
        endmodule
    """
    table = walk(source)
    loops = [s for s in table.scopes if s.kind == "generate_for"]
    assert len(loops) == 2
    assert loops[0].symbols["i"] is not loops[1].symbols["i"]
    result = run_inline_lint_case({"top.sv": source})
    result.expect_no_code("REDECLARED_VARIABLE")
    result.expect_code_once("NO_IMPLICIT_NET")


@pytest.mark.parametrize("kind", ["function automatic int", "task automatic"])
def test_formal_direction_inheritance_and_output_read_control(kind):
    end = "endfunction" if kind.startswith("function") else "endtask"
    source = f"""
        module m;
          {kind} f(int a, b, output int c, d);
            int local_value;
            local_value = a + b + c + d;
          {end}
        endmodule
    """
    table = walk(source)
    scope = next(s for s in table.scopes if s.kind in ("function", "task"))
    assert [scope.symbols[n].port_direction for n in ("a", "b", "c", "d")] == ["input", "input", "output", "output"]
    result = run_inline_lint_case({"top.sv": source})
    assert len(result.for_code("READ_BEFORE_WRITE")) == 2


def test_member_access_does_not_consume_same_named_module_variable():
    table = walk("""
        module m(output int y);
          typedef struct packed {int x;} s_t;
          s_t s;
          int x;
          always_comb begin s.x=1; y=s.x; end
        endmodule
    """)
    module = table.lookup_module("m")
    assert module.symbols["x"].uses == []
    assert module.symbols["s"].read_count == 1
    assert module.symbols["s"].write_count == 1


def test_field_name_cannot_be_used_as_a_bare_module_variable():
    result = run_inline_lint_case({"top.sv": """
        module m(output int y);
          typedef struct packed {int x;} s_t;
          assign y=x;
        endmodule
    """})
    result.expect_code_once("NO_IMPLICIT_NET")


def test_assignment_pattern_keys_are_members_but_values_are_variable_uses():
    result = run_inline_lint_case({"top.sv": """
        module m;
          typedef struct packed {int value;} s_t;
          s_t s;
          initial s = '{value: missing};
        endmodule
    """})
    result.expect_code_once("NO_IMPLICIT_NET")
    result.expect_message_contains("NO_IMPLICIT_NET", "missing")


def test_function_input_copy_can_be_written_without_module_port_policy():
    result = run_inline_lint_case({"top.sv": """
        module m;
          function automatic int f(input int x); x = x + 1; f = x; endfunction
        endmodule
    """})
    result.expect_no_code("NO_INPUT_PORT_WRITE")
    result.expect_no_code("PORT_DIRECTION_SUFFIX")
    result.expect_no_code("READ_BEFORE_WRITE")


def test_generate_connection_width_looks_up_enclosing_module_signals():
    result = run_inline_lint_case({"top.sv": """
        module child(input logic [3:0] data_i); endmodule
        module top(input logic [3:0] data_i);
          for(genvar i=0; i<2; i++) begin:g
            child u_child(.data_i(data_i));
          end
        endmodule
    """})
    result.expect_no_code("PORT_CONNECTION_WIDTH_UNKNOWN")
    result.expect_no_code("PORT_CONNECTION_WIDTH_MISMATCH")


def test_multilevel_member_access_records_base_variable_use():
    table = walk("""
        module m;
          typedef struct packed {int c;} inner_t;
          typedef struct packed {inner_t b;} outer_t;
          outer_t a;
          int b;
          int c;
          always_comb begin
            a.b.c = 1;
          end
        endmodule
    """)
    module = table.lookup_module("m")
    assert module.symbols["a"].write_count == 1
    assert module.symbols["b"].uses == []
    assert module.symbols["c"].uses == []


def test_struct_member_access_in_system_task_reads_base_variable():
    result = run_inline_lint_case({"top.sv": """
        module m;
          typedef struct packed {int field;} s_t;
          s_t s;
          initial begin
            s.field = 10;
            $display("%d", s.field);
          end
        endmodule
    """})
    result.expect_no_code("NO_IMPLICIT_NET")
    result.expect_no_code("UNUSED_VARIABLE")
    result.expect_no_code("NO_UNDRIVEN_SIGNAL")


def test_local_struct_variable_name_shadows_imported_package_name():
    result = run_inline_lint_case({"top.sv": """
        package my_pkg;
          int data;
        endpackage
        module m(output int y);
          import my_pkg::*;
          typedef struct packed {int data;} s_t;
          s_t my_pkg;
          always_comb begin
            my_pkg.data = 1;
            y = my_pkg.data;
          end
        endmodule
    """})
    result.expect_no_code("NO_IMPLICIT_NET")
    result.expect_no_code("NO_UNDRIVEN_SIGNAL")


def test_is_scoped_name_qualifier_rejects_dot_separator():
    import pyslang as sl
    from src.pkg.parser._syntax_queries.package_scoping import is_scoped_name_qualifier
    tree = sl.SyntaxTree.fromText("module m; int y; assign y = a.b; endmodule")
    def find_scoped(node):
        if getattr(node, "kind", None) == sl.SyntaxKind.ScopedName:
            return node
        if isinstance(node, sl.SyntaxNode):
            for child in node:
                found = find_scoped(child)
                if found is not None:
                    return found
        return None
    scoped = find_scoped(tree.root)
    assert scoped is not None
    assert not is_scoped_name_qualifier(scoped.left)
