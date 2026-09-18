import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.declarations_and_types.no_implicit_real_conversion import NoImplicitRealConversionRule
from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    assert_no_parse_errors("tests/rules/declarations_and_types/test_no_implicit_real_conversion.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "NO_IMPLICIT_REAL_CONVERSION"]


class TestNoImplicitRealConversion:
    def test_real_literal_with_fraction_flags(self) -> None:
        code = """
        module top;
            integer i = 23.1;
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 1
        assert "Implicit conversion of real or fractional value" in diags[0]["message"]

    def test_real_literal_integer_equivalent_clean(self) -> None:
        code = """
        module top;
            integer i = 23.0;
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 0

    def test_fractional_time_literal_flags_on_time_target(self) -> None:
        code = """
        `timescale 1ns / 1ps
        module top;
            time t1 = 9.001ns;
            time t2 = 9ps;
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 2

    def test_exact_time_literal_clean(self) -> None:
        code = """
        `timescale 1ns / 1ps
        module top;
            time t1 = 9ns;
            time t2 = 9.001us; // 9001 ns is an integer
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 0

    def test_realtime_target_clean(self) -> None:
        code = """
        `timescale 1ns / 1ps
        module top;
            realtime rt1 = 9.001ns;
            realtime rt2 = 9ps;
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 0

    def test_assignment_real_literal_flags(self) -> None:
        code = """
        module top;
            logic [31:0] x;
            assign x = 3.14159;
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 1
