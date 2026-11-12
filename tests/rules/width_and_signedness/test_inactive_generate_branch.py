import pytest

from src.pkg.parser.parse import parse_text
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner

from tests.support.parse_diagnostics import assert_no_parse_errors


def _codes(code: str) -> list[str]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)
    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/width_and_signedness/test_inactive_generate_branch.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)
    return [d["code"] for d in rule_runner.run(walker.results)]


_TEMPLATE = """
module top #(parameter W = 1)(input logic [7:0] wide, output logic [3:0] narrow);
    {body}
endmodule
"""


def _truncations(body: str) -> int:
    return _codes(_TEMPLATE.format(body=body)).count("ASSIGNMENT_TRUNCATION")


class TestInactiveGenerateBranch:
    def test_live_if_branch_is_checked(self) -> None:
        assert _truncations("if (W == 1) begin : g assign narrow = wide; end") == 1

    def test_dead_if_branch_is_skipped(self) -> None:
        assert _truncations("if (W == 2) begin : g assign narrow = wide; end") == 0

    def test_live_else_branch_is_checked(self) -> None:
        body = "if (W == 2) begin : a assign narrow = 4'd0; end else begin : b assign narrow = wide; end"
        assert _truncations(body) == 1

    def test_dead_else_branch_is_skipped(self) -> None:
        body = "if (W == 1) begin : a assign narrow = 4'd0; end else begin : b assign narrow = wide; end"
        assert _truncations(body) == 0

    def test_unevaluable_condition_keeps_branch_checked(self) -> None:
        body = "if (EXTERNAL == 2) begin : g assign narrow = wide; end"
        assert _truncations(body) == 1

    def test_nested_dead_branch_is_skipped(self) -> None:
        body = "if (W == 1) begin : a if (W == 3) begin : b assign narrow = wide; end end"
        assert _truncations(body) == 0

    @pytest.mark.parametrize("selector, expected", [(1, 1), (2, 0), (3, 0)])
    def test_case_generate_branch_taken_by_defaults(self, selector: int, expected: int) -> None:
        body = f"""case (W)
            {selector}: begin : sel assign narrow = wide; end
            default: begin : other assign narrow = 4'd0; end
        endcase"""
        assert _truncations(body) == expected

    def test_case_generate_default_item_taken_when_no_label_matches(self) -> None:
        body = """case (W)
            5: begin : five assign narrow = 4'd0; end
            default: begin : other assign narrow = wide; end
        endcase"""
        assert _truncations(body) == 1

    def test_ordinary_code_outside_generate_is_checked(self) -> None:
        assert _truncations("assign narrow = wide;") == 1


_PORT_SOURCE = """
module child(input [7:0] d);
endmodule
module top #(parameter W = 1);
  wire [3:0] narrow;
  if (W == {value}) begin : g
    child u(.d(narrow));
  end
endmodule
"""


class TestInactiveGenerateBranchInstances:
    def test_live_branch_instance_is_checked(self, lint_inline_case) -> None:
        lint_inline_case({"top.sv": _PORT_SOURCE.format(value=1)}).expect_code_once("PORT_CONNECTION_WIDTH_MISMATCH")

    def test_dead_branch_instance_is_skipped(self, lint_inline_case) -> None:
        lint_inline_case({"top.sv": _PORT_SOURCE.format(value=2)}).expect_no_code("PORT_CONNECTION_WIDTH_MISMATCH")
