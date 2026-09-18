import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.latches.no_latch_in_always_latch import NoLatchInAlwaysLatchRule
from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    assert_no_parse_errors("tests/rules/latches/test_no_latch_in_always_latch.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "NO_LATCH_IN_ALWAYS_LATCH"]


class TestNoLatchInAlwaysLatch:

    def test_unconditional_assignment_flags_no_latch(self) -> None:
        code = """
        module top (input logic a, output logic o);
            always_latch begin
                o = a;
            end
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 1

    def test_incomplete_if_infers_latch_clean(self) -> None:
        # Intentional latch pattern: variable not assigned on else branch
        code = """
        module top (input logic en, d, output logic q);
            always_latch begin
                if (en)
                    q = d;
            end
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 0

    def test_always_comb_ignored(self) -> None:
        code = """
        module top (input logic a, b, output logic o);
            always_comb begin
                if (a)
                    o = b;
                else
                    o = ~b;
            end
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 0
