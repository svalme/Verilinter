import pytest

from src.pkg.parser.parse import parse_text
from src.pkg.parser.syntax import (
    evaluate_constant_expression,
    natural_expression_width_and_signed,
    simple_expression_width_and_signed,
    unwrap_parentheses,
)
from src.pkg.parser.syntax_kinds import IDENTIFIER_NAME_KIND
from src.pkg.semantic.symbol import Symbol
from src.pkg.semantic.symbol_table import SymbolTable


@pytest.fixture
def test_scope():
    symtab = SymbolTable()
    scope = symtab.global_scope

    sym_w = Symbol("WIDTH", "parameter")
    sym_w.value = 8
    scope.define(sym_w)

    sym_d = Symbol("DEPTH", "parameter")
    sym_d.value = 256
    scope.define(sym_d)

    sym_a = Symbol("a", "wire")
    sym_a.bit_width = 8
    sym_a.msb, sym_a.lsb = 7, 0
    sym_a.is_signed = False
    scope.define(sym_a)

    sym_b = Symbol("b", "wire")
    sym_b.bit_width = 4
    sym_b.msb, sym_b.lsb = 3, 0
    sym_b.is_signed = False
    scope.define(sym_b)

    sym_s = Symbol("s", "wire")
    sym_s.bit_width = 16
    sym_s.msb, sym_s.lsb = 15, 0
    sym_s.is_signed = True
    scope.define(sym_s)

    return scope


def _get_rhs(code: str, index: int = 0):
    tree = parse_text(f"module top;\n{code}\nendmodule")
    members = [m for m in tree.root.members if hasattr(m, "assignments")]
    return members[index].assignments[0].right, tree


class TestExpressionEngine:
    def test_unwrap_parentheses(self):
        rhs, _ = _get_rhs("assign w = (((a)));")
        unwrapped = unwrap_parentheses(rhs)
        assert unwrapped.kind == IDENTIFIER_NAME_KIND

    def test_identifier_lookup(self, test_scope):
        rhs, tree = _get_rhs("assign w = a;")
        width, is_signed = simple_expression_width_and_signed(test_scope, rhs, tree)
        assert width == 8
        assert is_signed is False

        rhs_s, tree_s = _get_rhs("assign w = s;")
        width_s, is_signed_s = simple_expression_width_and_signed(test_scope, rhs_s, tree_s)
        assert width_s == 16
        assert is_signed_s is True

    def test_sized_vector_literals(self, test_scope):
        rhs, tree = _get_rhs("assign w = 8'hFF;")
        width, is_signed = simple_expression_width_and_signed(test_scope, rhs, tree)
        assert width == 8
        assert is_signed is False

        rhs_signed, tree_signed = _get_rhs("assign w = 16'shABCD;")
        width_s, is_signed_s = simple_expression_width_and_signed(test_scope, rhs_signed, tree_signed)
        assert width_s == 16
        assert is_signed_s is True

    def test_unsized_literals(self, test_scope):
        rhs, tree = _get_rhs("assign w = 42;")
        width, is_signed = simple_expression_width_and_signed(test_scope, rhs, tree)
        assert width is None
        assert is_signed is False

    def test_bit_select(self, test_scope):
        rhs, tree = _get_rhs("assign w = a[3];")
        width, is_signed = simple_expression_width_and_signed(test_scope, rhs, tree)
        assert width == 1
        assert is_signed is None

    def test_range_select(self, test_scope):
        rhs, tree = _get_rhs("assign w = a[6:2];")
        width, is_signed = simple_expression_width_and_signed(test_scope, rhs, tree)
        assert width == 5
        assert is_signed is None

    def test_indexed_part_select(self, test_scope):
        rhs_asc, tree_asc = _get_rhs("assign w = a[0+:4];")
        width_asc, _ = simple_expression_width_and_signed(test_scope, rhs_asc, tree_asc)
        assert width_asc == 4

        rhs_desc, tree_desc = _get_rhs("assign w = a[7-:3];")
        width_desc, _ = simple_expression_width_and_signed(test_scope, rhs_desc, tree_desc)
        assert width_desc == 3

    def test_concatenation(self, test_scope):
        rhs, tree = _get_rhs("assign w = {a, b};")
        width, is_signed = simple_expression_width_and_signed(test_scope, rhs, tree)
        assert width == 12
        assert is_signed is False

    def test_concatenation_with_unsized_literal_ieee1800(self, test_scope):
        # Per IEEE 1800, unsized decimal literals inside concatenations are 32 bits
        rhs, tree = _get_rhs("assign w = {a, 5};")
        width, is_signed = simple_expression_width_and_signed(test_scope, rhs, tree)
        assert width == 40
        assert is_signed is False

    def test_multiple_concatenation_replication(self, test_scope):
        rhs, tree = _get_rhs("assign w = {3{b}};")
        width, is_signed = simple_expression_width_and_signed(test_scope, rhs, tree)
        assert width == 12
        assert is_signed is False

    def test_shift_expression_natural_width(self, test_scope):
        rhs, tree = _get_rhs("assign w = a << 2;")
        width, is_signed = simple_expression_width_and_signed(test_scope, rhs, tree)
        assert width == 8
        assert is_signed is False

    def test_natural_expression_arithmetic(self, test_scope):
        # simple_expression_width_and_signed leaves arithmetic unhandled for rule isolation
        rhs_add, tree_add = _get_rhs("assign w = a + b;")
        assert simple_expression_width_and_signed(test_scope, rhs_add, tree_add) == (None, None)

        # natural_expression_width_and_signed computes natural result widths
        nat_add_w, nat_add_s = natural_expression_width_and_signed(test_scope, rhs_add, tree_add)
        assert nat_add_w == 8
        assert nat_add_s is False

        rhs_mul, tree_mul = _get_rhs("assign w = a * b;")
        nat_mul_w, nat_mul_s = natural_expression_width_and_signed(test_scope, rhs_mul, tree_mul)
        assert nat_mul_w == 12
        assert nat_mul_s is False

    def test_evaluate_constant_expression_arithmetic(self, test_scope):
        rhs, _ = _get_rhs("assign w = 10 + 5;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 15

        rhs, _ = _get_rhs("assign w = 10 - 3;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 7

        rhs, _ = _get_rhs("assign w = 4 * 6;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 24

        rhs, _ = _get_rhs("assign w = 20 / 4;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 5

        rhs, _ = _get_rhs("assign w = 23 % 5;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 3

        rhs, _ = _get_rhs("assign w = 2 ** 4;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 16

    def test_evaluate_constant_expression_unary(self, test_scope):
        rhs, _ = _get_rhs("assign w = +42;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 42

        rhs, _ = _get_rhs("assign w = -42;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == -42

        rhs, _ = _get_rhs("assign w = ~0;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == -1

        rhs, _ = _get_rhs("assign w = !0;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 1

        rhs, _ = _get_rhs("assign w = !5;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 0

    def test_evaluate_constant_expression_shifts_and_bitwise(self, test_scope):
        rhs, _ = _get_rhs("assign w = 1 << 4;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 16

        rhs, _ = _get_rhs("assign w = 32 >> 2;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 8

        rhs, _ = _get_rhs("assign w = 8 <<< 1;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 16

        rhs, _ = _get_rhs("assign w = 16 >>> 2;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 4

        rhs, _ = _get_rhs("assign w = 12 & 10;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 8

        rhs, _ = _get_rhs("assign w = 12 | 10;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 14

        rhs, _ = _get_rhs("assign w = 12 ^ 10;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 6

    def test_evaluate_constant_expression_clog2(self, test_scope):
        rhs, _ = _get_rhs("assign w = $clog2(16);")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 4

        rhs, _ = _get_rhs("assign w = $clog2(17);")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 5

        rhs, _ = _get_rhs("assign w = $clog2(1);")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 0

        rhs, _ = _get_rhs("assign w = $clog2(0);")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 0

        rhs, _ = _get_rhs("assign w = $clog2(DEPTH);")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 8

    def test_evaluate_constant_expression_parameters(self, test_scope):
        rhs, _ = _get_rhs("assign w = WIDTH - 1;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 7

        rhs, _ = _get_rhs("assign w = (WIDTH * 2) - 1;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 15

        rhs, _ = _get_rhs("assign w = (1 << WIDTH) - 1;")
        assert evaluate_constant_expression(rhs, scope=test_scope) == 255

    def test_evaluate_constant_expression_safety_guards(self, test_scope):
        rhs, _ = _get_rhs("assign w = 10 / 0;")
        assert evaluate_constant_expression(rhs, scope=test_scope) is None

        rhs, _ = _get_rhs("assign w = 10 % 0;")
        assert evaluate_constant_expression(rhs, scope=test_scope) is None

        rhs, _ = _get_rhs("assign w = 2 ** 100;")
        assert evaluate_constant_expression(rhs, scope=test_scope) is None

        rhs, _ = _get_rhs("assign w = 1 << 200;")
        assert evaluate_constant_expression(rhs, scope=test_scope) is None

        rhs, _ = _get_rhs("assign w = 1 >> -1;")
        assert evaluate_constant_expression(rhs, scope=test_scope) is None

        rhs, _ = _get_rhs("assign w = NON_EXISTENT + 1;")
        assert evaluate_constant_expression(rhs, scope=test_scope) is None

    def test_parameterized_range_select(self, test_scope):
        rhs, tree = _get_rhs("assign w = a[WIDTH-1:0];")
        width, is_signed = simple_expression_width_and_signed(test_scope, rhs, tree)
        assert width == 8

    def test_parameterized_indexed_part_select(self, test_scope):
        rhs, tree = _get_rhs("assign w = a[0+:WIDTH];")
        width, _ = simple_expression_width_and_signed(test_scope, rhs, tree)
        assert width == 8

    def test_parameterized_multiple_concatenation(self, test_scope):
        rhs, tree = _get_rhs("assign w = {WIDTH{1'b0}};")
        width, is_signed = simple_expression_width_and_signed(test_scope, rhs, tree)
        assert width == 8
        assert is_signed is False
