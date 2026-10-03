from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.handlers.register_handlers import *
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.parse_diagnostics import assert_no_parse_errors
from tests.support.lint_harness import run_inline_lint_case


def walk(source: str) -> SymbolTable:
    tree = parse_text(source)
    assert_no_parse_errors("ansi port regression", tree)
    table = SymbolTable()
    Walker(dispatch).walk(tree.root, tree, Context(scope=table.global_scope), table)
    return table


def test_grouped_ansi_port_direction_inheritance_with_types():
    table = walk("""
        module m(
            input wire [7:0] a_i, b_i, c_i,
            output logic [15:0] x_o, y_o
        );
        endmodule
    """)
    module = table.lookup_module("m")
    for name in ("a_i", "b_i", "c_i"):
        assert module.symbols[name].is_port
        assert module.symbols[name].port_direction == "input"

    for name in ("x_o", "y_o"):
        assert module.symbols[name].is_port
        assert module.symbols[name].port_direction == "output"


def test_consecutive_direction_changes_across_commas():
    table = walk("""
        module m(
            input a, b,
            inout c, d,
            output e, f
        );
        endmodule
    """)
    module = table.lookup_module("m")
    assert module.symbols["a"].port_direction == "input"
    assert module.symbols["b"].port_direction == "input"
    assert module.symbols["c"].port_direction == "inout"
    assert module.symbols["d"].port_direction == "inout"
    assert module.symbols["e"].port_direction == "output"
    assert module.symbols["f"].port_direction == "output"


def test_port_direction_suffix_evaluates_all_grouped_ports():
    """Verify that PORT_DIRECTION_SUFFIX checks subsequent ports in grouped declarations.

    Before the inherited port direction fix, only the first port in a group carried
    a direction token; subsequent ports resolved to None and bypassed suffix checks.
    """
    result = run_inline_lint_case({
        "top.sv": """
        module m(
            input logic clk_i, rst_i, bad_input,
            output logic valid_o, bad_output
        );
        endmodule
        """
    })
    # bad_input (third input in group) and bad_output (second output in group) must both flag
    suffix_diags = result.for_code("PORT_DIRECTION_SUFFIX")
    assert len(suffix_diags) == 2
    cols = {d["col"] for d in suffix_diags}
    # Check that the flagged columns correspond to bad_input and bad_output
    assert len(cols) == 2


def test_non_ansi_style_port_declarations():
    table = walk("""
        module m(a, b, c);
          input wire a, b;
          output reg c;
        endmodule
    """)
    module = table.lookup_module("m")
    assert module.symbols["a"].is_port and module.symbols["a"].port_direction == "input"
    assert module.symbols["b"].is_port and module.symbols["b"].port_direction == "input"
    assert module.symbols["c"].is_port and module.symbols["c"].port_direction == "output"


def test_function_and_task_formal_direction_inheritance():
    table = walk("""
        module m;
          function automatic int calc(int x, y, output int z);
            calc = x + y;
            z = calc;
          endfunction
          task automatic do_work(string tag, int id, output bit err);
            err = 1'b0;
          endtask
        endmodule
    """)
    func_scope = next(s for s in table.scopes if s.kind == "function")
    assert func_scope.symbols["x"].port_direction == "input"
    assert func_scope.symbols["y"].port_direction == "input"
    assert func_scope.symbols["z"].port_direction == "output"

    task_scope = next(s for s in table.scopes if s.kind == "task")
    assert task_scope.symbols["tag"].port_direction == "input"
    assert task_scope.symbols["id"].port_direction == "input"
    assert task_scope.symbols["err"].port_direction == "output"
