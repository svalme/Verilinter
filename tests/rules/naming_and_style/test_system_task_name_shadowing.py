from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.naming_and_style.system_task_name_shadowing import SystemTaskNameShadowingRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "SYSTEM_TASK_NAME_SHADOWING"]


class TestSystemTaskNameShadowingRule:
    @pytest.fixture
    def rule(self) -> SystemTaskNameShadowingRule:
        return SystemTaskNameShadowingRule()

    def test_rule_has_correct_code(self, rule: SystemTaskNameShadowingRule) -> None:
        assert rule.code == "SYSTEM_TASK_NAME_SHADOWING"

    def test_flags_signal_named_random(self) -> None:
        # Unlike `time`/`realtime` (real reserved type keywords -- pyslang parses
        # those as a type, never a declarator, so this rule can never see them),
        # `random` is an ordinary identifier apart from its `$random` system
        # function, so it is a genuine, reachable shadowing case.
        diagnostics = _diagnostics(
            """
            module top;
              wire random;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_signal_named_display(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire display;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_ordinary_signal_name(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire my_signal;
            endmodule
            """
        )

        assert diagnostics == []

    def test_flags_a_function_named_like_a_system_task(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              function void display();
              endfunction
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_a_task_named_like_a_system_task(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              task finish;
              endtask
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_a_function_or_task_with_a_different_name(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              function void display_state();
              endfunction
              task finish_now;
              endtask
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_a_call_of_the_system_task_itself(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              initial begin
                $display("x");
                $finish;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_flags_each_declaration_that_matches(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire display;
              function void finish();
              endfunction
              task random;
              endtask
            endmodule
            """
        )

        assert len(diagnostics) == 3
