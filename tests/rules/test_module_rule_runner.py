from typing import Any

from src.pkg.rules.base_symbol_rule import BaseSymbolRule
from src.pkg.rules.module_rule_runner import ModuleRuleRunner
from src.pkg.rules.rule_selection import RuleSelection


class TestModuleRuleRunnerSelection:
    def test_run_filters_by_profile(self) -> None:
        runner = ModuleRuleRunner()

        class TaggedRule(BaseSymbolRule):
            code = "MODULE_TAGGED"
            category = "module_correctness"
            default_profiles = ("rtl_strict",)

            def run(self, symbol_table: Any) -> list[dict[str, Any]]:
                return [{"code": self.code}]

        class OtherRule(BaseSymbolRule):
            code = "MODULE_OTHER"
            category = "module_correctness"
            default_profiles = ("legacy_verilog",)

            def run(self, symbol_table: Any) -> list[dict[str, Any]]:
                return [{"code": self.code}]

        runner.register(TaggedRule)
        runner.register(OtherRule)

        diagnostics = runner.run(
            object(),  # type: ignore[arg-type]
            RuleSelection(enabled_profiles=frozenset({"rtl_strict"})),
        )

        assert diagnostics == [{"code": "MODULE_TAGGED"}]
