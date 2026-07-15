from typing import Any

from ...semantic.symbol_table import SymbolTable
from ..base_symbol_rule import BaseSymbolRule


class SymbolRuleRunner:
    def __init__(self) -> None:
        self._rules: list[BaseSymbolRule] = []

    def register(self, rule_cls: type[BaseSymbolRule]) -> type[BaseSymbolRule]:
        self._rules.append(rule_cls())
        return rule_cls

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        for rule in self._rules:
            diagnostics.extend(rule.run(symbol_table))
        return diagnostics


symbol_rule_runner = SymbolRuleRunner()
