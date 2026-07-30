from typing import Any

from src.pkg.rules.base_symbol_rule import BaseSymbolRule
from src.pkg.rules.rule_selection import RuleSelection
from src.pkg.rules.symbol.symbol_rule_runner import SymbolRuleRunner


class TestSymbolRuleRunnerSelection:
    def test_run_filters_by_category(self) -> None:
        runner = SymbolRuleRunner()

        class SemanticRule(BaseSymbolRule):
            code = "SEM"
            category = "semantic_correctness"

            def run(self, symbol_table: Any) -> list[dict[str, Any]]:
                return [{"code": self.code}]

        class OtherRule(BaseSymbolRule):
            code = "OTHER"
            category = "module_correctness"

            def run(self, symbol_table: Any) -> list[dict[str, Any]]:
                return [{"code": self.code}]

        runner.register(SemanticRule)
        runner.register(OtherRule)

        diagnostics = runner.run(
            object(),  # type: ignore[arg-type]
            RuleSelection(enabled_categories=frozenset({"semantic_correctness"})),
        )

        assert diagnostics == [{"code": "SEM"}]
