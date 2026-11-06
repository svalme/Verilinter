"""`classify_operand` is the one place that decides what an operand is; every comparison rule asks it."""
from __future__ import annotations

import pyslang as sl
import pytest

from src.pkg.handlers.register_handlers import *  # noqa: F401,F403
from src.pkg.parser.parse import parse_text
from src.pkg.parser.syntax import comparison_operands
from src.pkg.rules.width_and_signedness.operand import (
    OperandKind,
    classify_operand,
    selectors_into_element_bits,
)
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.lint_harness import run_inline_lint_case
from tests.support.parse_diagnostics import assert_no_parse_errors

_DECLARATIONS = """
  localparam P = 3;
  typedef enum logic [1:0] {E0, E1} e_t;
  logic [3:0] r;
  logic signed [3:0] s;
  logic [7:0] mem [0:3];
"""


def _operands(comparison: str):
    code = f"module top;\n{_DECLARATIONS}\n  wire x = {comparison};\nendmodule\n"
    table = SymbolTable()
    ctx = Context(scope=table.global_scope)
    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/width_and_signedness/test_operand.py", tree)
    Walker(dispatch).walk(tree.root, tree, ctx, table)
    module_scope = table.modules["top"][0]

    found: list[object] = []

    def visit(node: object) -> object:
        if getattr(node, "kind", None) in (sl.SyntaxKind.EqualityExpression, sl.SyntaxKind.GreaterThanExpression):
            found.append(node)
        return sl.VisitAction.Advance

    tree.root.visit(visit)
    left, right, _ = comparison_operands(found[0])
    return classify_operand(module_scope, left, tree), classify_operand(module_scope, right, tree)


@pytest.mark.parametrize(
    ("expression", "kind"),
    [
        ("r == 3", OperandKind.LITERAL),
        ("r == -1", OperandKind.LITERAL),
        ("r == P", OperandKind.CONSTANT_SYMBOL),
        ("r == E1", OperandKind.CONSTANT_SYMBOL),
        ("r == (P)", OperandKind.CONSTANT_SYMBOL),
        ("r == s", OperandKind.WIDTH_BOUNDED),
        ("r == mem[1]", OperandKind.WIDTH_BOUNDED),
        ("r == {r, r}", OperandKind.WIDTH_BOUNDED),
        ("r == (r + s)", OperandKind.COMPUTED),
    ],
)
def test_right_operand_kind(expression: str, kind: OperandKind) -> None:
    _left, right = _operands(expression)

    assert right.kind is kind


def test_a_variable_is_width_bounded_and_not_constant() -> None:
    left, _ = _operands("r == 3")

    assert left.is_width_bounded
    assert not left.is_constant_symbol
    assert not left.is_literal


def test_a_literal_carries_its_value() -> None:
    _, right = _operands("r == -7")

    assert right.value == -7


def test_width_and_signedness_come_from_the_declaration() -> None:
    left, right = _operands("r == s")

    assert (left.width, left.signed) == (4, False)
    assert (right.width, right.signed) == (4, True)


def test_selectors_after_the_unpacked_dimensions_index_the_element_bits() -> None:
    class Symbol:
        unpacked_dimensions = [("0", "3")]

    assert list(selectors_into_element_bits(Symbol(), ["array", "bits"])) == ["bits"]
    assert list(selectors_into_element_bits(object(), ["bits"])) == ["bits"]


@pytest.mark.parametrize("condition", ["P > 1", "P < 0", "u >= P", "N < u", "N == u"])
def test_a_parameter_operand_is_skipped_by_every_comparison_rule(condition: str) -> None:
    """The guard lives in the classifier, so each comparison rule that asks it gets the same answer."""
    result = run_inline_lint_case(
        {
            "top.sv": f"""
            module top;
              localparam P = 3;
              localparam signed [3:0] N = -1;
              bit [2:0] u;
              initial begin
                if ({condition}) $stop;
              end
            endmodule
            """
        }
    )

    result.expect_no_code("COMPARISON_ALWAYS_CONSTANT")
    result.expect_no_code("COMPARISON_SIGNEDNESS_MISMATCH")
