from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.naming_and_style.instance_name_prefix import InstanceNamePrefixRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "INSTANCE_NAME_PREFIX"]


class TestInstanceNamePrefixRule:
    @pytest.fixture
    def rule(self) -> InstanceNamePrefixRule:
        return InstanceNamePrefixRule()

    def test_rule_has_correct_code(self, rule: InstanceNamePrefixRule) -> None:
        assert rule.code == "INSTANCE_NAME_PREFIX"

    def test_flags_instance_missing_prefix(self) -> None:
        diagnostics = _diagnostics(
            """
            module child;
            endmodule

            module top;
              child my_child();
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_u_prefixed_instance(self) -> None:
        diagnostics = _diagnostics(
            """
            module child;
            endmodule

            module top;
              child u_child();
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_i_prefixed_instance(self) -> None:
        diagnostics = _diagnostics(
            """
            module child;
            endmodule

            module top;
              child i_child();
            endmodule
            """
        )

        assert diagnostics == []
