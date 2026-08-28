import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.syntax.no_if_without_begin_end import NoElseWithoutBeginEndRule, NoIfWithoutBeginEndRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return rule_runner.run(walker.results)


def _for_code(code: str, diagnostics: list[dict]) -> list[dict]:
    return [d for d in diagnostics if d["code"] == code]


class TestNoIfWithoutBeginEndRule:
    @pytest.fixture
    def rule(self) -> NoIfWithoutBeginEndRule:
        return NoIfWithoutBeginEndRule()

    def test_rule_has_correct_code(self, rule: NoIfWithoutBeginEndRule) -> None:
        assert rule.code == "NO_IF_WITHOUT_BEGIN_END"

    def test_flags_bare_if_body(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg x;
              always @(*) begin
                if (1'b1) x = 1'b0;
              end
            endmodule
            """
        )

        assert len(_for_code("NO_IF_WITHOUT_BEGIN_END", diagnostics)) == 1

    def test_does_not_flag_begin_end_wrapped_if_body(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg x;
              always @(*) begin
                if (1'b1) begin
                  x = 1'b0;
                end
              end
            endmodule
            """
        )

        assert _for_code("NO_IF_WITHOUT_BEGIN_END", diagnostics) == []

    def test_flags_non_chained_nested_bare_if(self) -> None:
        """`if (a) if (b) x=1;` with no `else` is a genuinely bare nested if, not
        an else-if chain -- both the outer and inner if bodies are bare."""
        diagnostics = _diagnostics(
            """
            module top;
              reg x;
              always @(*) begin
                if (1'b1) if (1'b0) x = 1'b1;
              end
            endmodule
            """
        )

        assert len(_for_code("NO_IF_WITHOUT_BEGIN_END", diagnostics)) == 2


class TestNoElseWithoutBeginEndRule:
    @pytest.fixture
    def rule(self) -> NoElseWithoutBeginEndRule:
        return NoElseWithoutBeginEndRule()

    def test_rule_has_correct_code(self, rule: NoElseWithoutBeginEndRule) -> None:
        assert rule.code == "NO_ELSE_WITHOUT_BEGIN_END"

    def test_flags_bare_else_body(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg x;
              always @(*) begin
                if (1'b1) begin
                  x = 1'b0;
                end else x = 1'b1;
              end
            endmodule
            """
        )

        assert len(_for_code("NO_ELSE_WITHOUT_BEGIN_END", diagnostics)) == 1

    def test_does_not_flag_begin_end_wrapped_else_body(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg x;
              always @(*) begin
                if (1'b1) begin
                  x = 1'b0;
                end else begin
                  x = 1'b1;
                end
              end
            endmodule
            """
        )

        assert _for_code("NO_ELSE_WITHOUT_BEGIN_END", diagnostics) == []

    def test_does_not_flag_else_if_chain(self) -> None:
        """`else if (...)` is idiomatic chaining, not a bare unwrapped else body --
        the chained if's own body is independently checked by
        NO_IF_WITHOUT_BEGIN_END instead."""
        diagnostics = _diagnostics(
            """
            module top;
              reg x;
              always @(*) begin
                if (1'b1) begin
                  x = 1'b0;
                end else if (1'b0) begin
                  x = 1'b1;
                end else begin
                  x = 1'b0;
                end
              end
            endmodule
            """
        )

        assert _for_code("NO_ELSE_WITHOUT_BEGIN_END", diagnostics) == []

    def test_flags_bare_else_in_else_if_chain(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              reg x;
              always @(*) begin
                if (1'b1) begin
                  x = 1'b0;
                end else if (1'b0) begin
                  x = 1'b1;
                end else x = 1'b0;
              end
            endmodule
            """
        )

        assert len(_for_code("NO_ELSE_WITHOUT_BEGIN_END", diagnostics)) == 1
