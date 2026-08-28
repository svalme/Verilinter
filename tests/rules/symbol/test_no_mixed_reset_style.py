import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.symbol.no_mixed_reset_style import NoMixedResetStyleRule


MIXED_RESET_STYLE_CODE = """
module top(input logic clk, input logic rst_n);
  logic q, r;
  always_ff @(posedge clk) begin
    q <= q + 1;
  end
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) r <= 0;
    else r <= 1;
  end
endmodule
"""

SYNC_ONLY_CODE = """
module top(input logic clk);
  logic q, r;
  always_ff @(posedge clk) begin
    q <= q + 1;
  end
  always_ff @(posedge clk) begin
    r <= r + 1;
  end
endmodule
"""

ASYNC_ONLY_CODE = """
module top(input logic clk, input logic rst_n);
  logic q, r;
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 0;
    else q <= 1;
  end
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) r <= 0;
    else r <= 1;
  end
endmodule
"""

TWO_MODULES_EACH_SINGLE_STYLE_CODE = """
module a(input logic clk);
  logic q;
  always_ff @(posedge clk) begin
    q <= q + 1;
  end
endmodule

module b(input logic clk, input logic rst_n);
  logic r;
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) r <= 0;
    else r <= 1;
  end
endmodule
"""


def _run(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return NoMixedResetStyleRule().run(symbol_table)


class TestNoMixedResetStyleRule:
    @pytest.fixture
    def rule(self) -> NoMixedResetStyleRule:
        return NoMixedResetStyleRule()

    def test_rule_has_correct_code(self, rule: NoMixedResetStyleRule) -> None:
        assert rule.code == "NO_MIXED_RESET_STYLE"

    def test_flags_module_mixing_sync_and_async_reset_style(self) -> None:
        diagnostics = _run(MIXED_RESET_STYLE_CODE)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_MIXED_RESET_STYLE"
        assert "top" in diagnostics[0]["message"]

    def test_does_not_flag_two_sync_blocks(self) -> None:
        assert _run(SYNC_ONLY_CODE) == []

    def test_does_not_flag_two_async_blocks(self) -> None:
        assert _run(ASYNC_ONLY_CODE) == []

    def test_does_not_flag_across_two_different_single_style_modules(self) -> None:
        assert _run(TWO_MODULES_EACH_SINGLE_STYLE_CODE) == []
