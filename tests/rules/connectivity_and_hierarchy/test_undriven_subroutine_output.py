import pytest

from src.pkg.handlers.register_handlers import *
from src.pkg.parser.parse import parse_text
from src.pkg.rules.connectivity_and_hierarchy.undriven_subroutine_output import UndrivenSubroutineOutputRule
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/connectivity_and_hierarchy/test_undriven_subroutine_output.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return UndrivenSubroutineOutputRule().run(symbol_table)


class TestUndrivenSubroutineOutputRule:
    def test_rule_has_correct_code(self) -> None:
        assert UndrivenSubroutineOutputRule().code == "UNDRIVEN_SUBROUTINE_OUTPUT"

    def test_flags_task_output_declared_in_body(self) -> None:
        code = """
module t;
  task x;
    output top;
    begin
    end
  endtask
endmodule
"""
        diags = _diagnostics(code)
        assert len(diags) == 1
        assert "top" in diags[0]["message"]
        assert "task 'x'" in diags[0]["message"]

    def test_flags_function_output_argument(self) -> None:
        code = """
module t;
  function automatic int f(output int fo, input int fi);
    f = fi;
  endfunction
endmodule
"""
        diags = _diagnostics(code)
        assert [d["message"].split("'")[1] for d in diags] == ["fo"]

    def test_flags_function_that_never_assigns_its_return_value(self) -> None:
        code = """
module t;
  function automatic int f(input int fi);
  endfunction
endmodule
"""
        assert len(_diagnostics(code)) == 1

    @pytest.mark.parametrize(
        "body",
        [
            "task x(output o); o = 1; endtask",
            "task x(output [1:0] o); o[0] = 1; endtask",
            "task x(output a, output b); {a, b} = 2'b01; endtask",
            "task x(output o); begin if (1) o = 1; end endtask",
            "function automatic int f(input int i); f = i; endfunction",
            "task x(input i, inout io); io = i; endtask",
        ],
    )
    def test_ignores_assigned_outputs(self, body: str) -> None:
        assert _diagnostics(f"module t; {body} endmodule") == []

    def test_ignores_module_output_ports(self) -> None:
        assert _diagnostics("module t(output o); endmodule") == []

    def test_ignores_dpi_import_prototype(self) -> None:
        code = 'module t; import "DPI-C" function void dpi(output int dx); endmodule'
        assert _diagnostics(code) == []

    def test_flags_class_method_output(self) -> None:
        code = "class c; function void m(output int mo); endfunction endclass"
        assert len(_diagnostics(code)) == 1

    def test_return_statement_drives_the_result(self) -> None:
        code = """
module t;
  function automatic int f(int a);
    return a;
  endfunction
endmodule
"""
        assert _diagnostics(code) == []

    def test_function_that_neither_assigns_nor_returns_is_flagged(self) -> None:
        code = """
module t;
  function automatic int f(int a);
    int x;
    x = a;
  endfunction
endmodule
"""
        diags = _diagnostics(code)
        assert len(diags) == 1
        assert "function 'f'" in diags[0]["message"]

    def test_class_constructor_has_no_result_to_drive(self) -> None:
        code = """
class c;
  function new(int a);
  endfunction
endclass
"""
        assert _diagnostics(code) == []
