from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.conditional_and_case_statements.no_default_case_statement import NoDefaultCaseStatementRule


from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/conditional_and_case_statements/test_no_default_case_statement.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "NO_DEFAULT_CASE_STATEMENT"]


class TestNoDefaultCaseStatementRule:
    @pytest.fixture
    def rule(self) -> NoDefaultCaseStatementRule:
        return NoDefaultCaseStatementRule()

    def test_rule_has_correct_code(self, rule: NoDefaultCaseStatementRule) -> None:
        assert rule.code == "NO_DEFAULT_CASE_STATEMENT"

    def test_flags_case_statement_missing_default(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic [1:0] sel, output logic y);
              always_comb begin
                case (sel)
                  2'b00: y = 1'b0;
                  2'b01: y = 1'b1;
                endcase
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_DEFAULT_CASE_STATEMENT"

    def test_does_not_flag_case_statement_with_default(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic [1:0] sel, output logic y);
              always_comb begin
                case (sel)
                  2'b00: y = 1'b0;
                  default: y = 1'b1;
                endcase
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_flags_casex_missing_default(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic [1:0] sel, output logic y);
              always_comb begin
                casex (sel)
                  2'b0?: y = 1'b0;
                endcase
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_case_generate(self) -> None:
        """Case generate has its own dedicated rule, DEFAULT_CASE; this rule is
        specifically for procedural case statements and must not double-report."""
        diagnostics = _diagnostics(
            """
            module m;
              generate
                case (1)
                  0: begin
                    wire a;
                  end
                endcase
              endgenerate
            endmodule
            """
        )

        assert diagnostics == []

    def test_nested_case_statements_are_checked_independently(self) -> None:
        """The outer case has a default; the inner one doesn't. Only the inner
        one should be flagged -- Context flags accumulate downward and never
        clear, so a flag-based implementation would have inherited the outer's
        default and missed this. This rule resolves the enclosing case
        statement directly instead, so nesting doesn't leak."""
        diagnostics = _diagnostics(
            """
            module top(input logic [1:0] sel, input logic [1:0] sel2, output logic y);
              always_comb begin
                case (sel)
                  2'b00: begin
                    case (sel2)
                      2'b00: y = 1'b0;
                    endcase
                  end
                  default: y = 1'b0;
                endcase
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_each_case_statement_separately(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic a, input logic b, output logic y, output logic z);
              always_comb begin
                case (a)
                  1'b0: y = 1'b0;
                endcase
                case (b)
                  1'b0: z = 1'b0;
                endcase
              end
            endmodule
            """
        )

        assert len(diagnostics) == 2
