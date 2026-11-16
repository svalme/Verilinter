"""Typedef widths, struct member widths, `$bits`, and the width of a variable declared with a named type."""
from __future__ import annotations

from src.pkg.handlers.register_handlers import *  # noqa: F401,F403
from src.pkg.parser.parse import parse_text
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.lint_harness import run_inline_lint_case
from tests.support.parse_diagnostics import assert_no_parse_errors


def _module_scope(code: str):
    table = SymbolTable()
    tree = parse_text(code)
    assert_no_parse_errors("tests/semantic/types/test_named_type_widths.py", tree)
    Walker(dispatch).walk(tree.root, tree, Context(scope=table.global_scope), table)
    return table.modules["top"][0]


DECLARATIONS = """
module top #(parameter int N = 4);
  typedef struct packed { logic [3:0] a; logic b; } s_t;
  typedef enum logic [2:0] { X, Y } e_t;
  typedef enum { Z } e32_t;
  typedef logic signed [7:0] byte_t;
  typedef byte_t alias_t;
  typedef int unsigned u_t;
  typedef union packed { logic [7:0] x; logic [7:0] y; } un_t;
  typedef logic [N-1:0] vec_t;
  typedef struct { logic a; } unpacked_t;
  s_t sv;
  s_t [1:0] sa;
  s_t arr [2];
  e_t ev;
  alias_t av;
  vec_t vv;
  unpacked_t uv;
endmodule
"""


class TestTypedefWidths:
    def test_packed_struct_is_the_sum_of_its_members(self) -> None:
        scope = _module_scope(DECLARATIONS)
        assert scope.lookup("s_t").bit_width == 5
        assert scope.lookup("s_t").member_widths == {"a": 4, "b": 1}

    def test_enum_takes_its_base_type_width_or_32(self) -> None:
        scope = _module_scope(DECLARATIONS)
        assert scope.lookup("e_t").bit_width == 3
        assert scope.lookup("e32_t").bit_width == 32

    def test_vector_alias_and_atom_typedefs(self) -> None:
        scope = _module_scope(DECLARATIONS)
        assert scope.lookup("byte_t").bit_width == 8 and scope.lookup("byte_t").is_signed is True
        assert scope.lookup("alias_t").bit_width == 8
        assert scope.lookup("u_t").bit_width == 32 and scope.lookup("u_t").is_signed is False

    def test_packed_union_is_as_wide_as_a_member(self) -> None:
        assert _module_scope(DECLARATIONS).lookup("un_t").bit_width == 8

    def test_parameterized_width_uses_the_default(self) -> None:
        assert _module_scope(DECLARATIONS).lookup("vec_t").bit_width == 4

    def test_unpacked_struct_has_no_packed_width(self) -> None:
        assert _module_scope(DECLARATIONS).lookup("unpacked_t").bit_width is None


class TestVariablesOfNamedTypes:
    def test_variable_takes_the_typedef_width_and_member_widths(self) -> None:
        sv = _module_scope(DECLARATIONS).lookup("sv")
        assert sv.bit_width == 5 and sv.member_widths == {"a": 4, "b": 1}

    def test_packed_dimensions_after_the_type_name_multiply_the_width(self) -> None:
        assert _module_scope(DECLARATIONS).lookup("sa").bit_width == 10

    def test_unpacked_array_of_a_named_type_keeps_the_element_width(self) -> None:
        arr = _module_scope(DECLARATIONS).lookup("arr")
        assert arr.bit_width == 5 and arr.whole_width == 10

    def test_variable_of_an_unpacked_struct_has_no_width(self) -> None:
        assert _module_scope(DECLARATIONS).lookup("uv").bit_width is None


def test_struct_member_selects_and_named_types_match_a_child_port():
    result = run_inline_lint_case({
        "top.sv": """
        module child(input logic [4:0] d, input logic [2:0] e, input logic g, input logic [3:0] h);
        endmodule
        module top;
          typedef struct packed { logic [3:0] a; logic b; } s_t;
          typedef enum logic [2:0] { X, Y } e_t;
          s_t sv;
          e_t ev;
          s_t arr [2];
          child u0 (.d(sv), .e(ev), .g(arr[0].b), .h(sv.a));
        endmodule
        """
    })
    result.expect_no_code("PORT_CONNECTION_WIDTH_UNKNOWN")
    result.expect_no_code("PORT_CONNECTION_WIDTH_MISMATCH")


def test_bits_of_a_typedef_sizes_a_parameter_override():
    result = run_inline_lint_case({
        "top.sv": """
        module child #(parameter int Width = 32) (input logic [Width-1:0] d);
        endmodule
        module top;
          typedef struct packed { logic [3:0] a; logic b; } s_t;
          s_t sv;
          child #(.Width($bits(s_t))) u0 (.d(sv));
        endmodule
        """
    })
    result.expect_no_code("PORT_CONNECTION_WIDTH_MISMATCH")
    result.expect_no_code("PORT_CONNECTION_WIDTH_UNKNOWN")


def test_override_that_cannot_be_evaluated_leaves_the_port_width_unknown():
    result = run_inline_lint_case({
        "top.sv": """
        module child #(parameter int Width = 32) (input logic [Width-1:0] d);
        endmodule
        module top;
          logic [5:0] x;
          child #(.Width($bits(missing_t))) u0 (.d(x));
        endmodule
        """
    })
    result.expect_no_code("PORT_CONNECTION_WIDTH_MISMATCH")
