from typing import Any

from ..semantic.symbol_table import SymbolTable
from .base_symbol_rule import BaseSymbolRule
from .rule_selection import RuleSelection


class ModuleRuleRunner:
    """Runs rules that need a cross-file view (the module registry / instantiation
    references), kept separate from SymbolRuleRunner's single-file symbol rules."""

    def __init__(self, rules: list[BaseSymbolRule] | None = None) -> None:
        self._rules: list[BaseSymbolRule] = []
        if rules is not None:
            for rule in rules:
                self.add_rule(rule)

    def add_rule(self, rule: BaseSymbolRule) -> None:
        self._rules.append(rule)

    def register(self, rule_cls: type[BaseSymbolRule]) -> type[BaseSymbolRule]:
        self.add_rule(rule_cls())
        return rule_cls

    def for_selection(self, selection: RuleSelection | None) -> ModuleRuleRunner:
        if selection is None:
            return self
        return ModuleRuleRunner([rule for rule in self._rules if selection.allows(rule)])

    def _selected_rules(self, selection: RuleSelection | None) -> list[BaseSymbolRule]:
        if selection is None:
            return self._rules
        return [rule for rule in self._rules if selection.allows(rule)]

    def run(
        self,
        symbol_table: SymbolTable,
        selection: RuleSelection | None = None,
    ) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        for rule in self._selected_rules(selection):
            diagnostics.extend(rule.run(symbol_table))
        return diagnostics


module_rule_runner = ModuleRuleRunner()
