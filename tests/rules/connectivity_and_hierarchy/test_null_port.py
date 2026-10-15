from __future__ import annotations

import pytest

from src.pkg.handlers.register_handlers import *
from src.pkg.parser.parse import parse_text
from src.pkg.rules.connectivity_and_hierarchy.null_port import NullPortRule
from src.pkg.rules.register_rules import rule_runner
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.lint_harness import run_inline_lint_case


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "NULLPORT"]


class TestNullPortRule:
    @pytest.fixture
    def rule(self) -> NullPortRule:
        return NullPortRule()

    def test_rule_has_correct_code(self, rule: NullPortRule) -> None:
        assert rule.code == "NULLPORT"

    def test_flags_trailing_comma_empty_port(self) -> None:
        code = "module t(a,); input a; endmodule"
        diags = _diagnostics(code)
        assert len(diags) == 1
        assert diags[0]["line"] == 1
        assert diags[0]["col"] == 12
        assert "Null port on module" in diags[0]["message"]

    def test_flags_middle_empty_port(self) -> None:
        code = "module t(a,,b); input a, b; endmodule"
        diags = _diagnostics(code)
        assert len(diags) == 1
        assert diags[0]["line"] == 1
        assert diags[0]["col"] == 12
        assert "Null port on module" in diags[0]["message"]

    def test_flags_leading_empty_port(self) -> None:
        code = "module t(,a); input a; endmodule"
        diags = _diagnostics(code)
        assert len(diags) == 1
        assert diags[0]["line"] == 1
        assert diags[0]["col"] == 10
        assert "Null port on module" in diags[0]["message"]

    def test_flags_only_comma_empty_port(self) -> None:
        code = "module t(,); endmodule"
        diags = _diagnostics(code)
        assert len(diags) == 2
        assert all("Null port on module" in d["message"] for d in diags)

    def test_flags_multiple_consecutive_empty_ports(self) -> None:
        code = "module t(a,,,b); input a, b; endmodule"
        diags = _diagnostics(code)
        assert len(diags) == 2

    def test_flags_instance_empty_port_connection(self) -> None:
        code = """
        module top;
          wire a, b;
          sub u(a, , b);
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 1
        assert "Empty (null) port connection in module instance" in diags[0]["message"]

    def test_flags_instance_trailing_empty_port_connection(self) -> None:
        code = """
        module top;
          wire a;
          sub u(a,);
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 1
        assert "Empty (null) port connection in module instance" in diags[0]["message"]

    def test_allows_clean_module_and_instance(self) -> None:
        code = """
        module top(input logic a_i, output logic b_o);
          sub u(.x(a_i), .y(b_o));
        endmodule
        """
        diags = _diagnostics(code)
        assert len(diags) == 0

    def test_allows_empty_parentheses(self) -> None:
        code = "module top(); endmodule"
        diags = _diagnostics(code)
        assert len(diags) == 0

    def test_allows_no_parentheses(self) -> None:
        code = "module top; endmodule"
        diags = _diagnostics(code)
        assert len(diags) == 0

    def test_pipeline_integration_with_expect_diagnostics(self) -> None:
        result = run_inline_lint_case({"t.v": "module t(a,); input a; endmodule"})
        result.expect_diagnostics([(1, "NULLPORT")], filter_code="NULLPORT")
