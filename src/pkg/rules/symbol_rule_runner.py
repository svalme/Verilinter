# src/pkg/rules/runner.py

from .base_symbol_rule import BaseSymbolRule

class SymbolRuleRunner(BaseSymbolRule):
    def __init__(self):
        self._rules = []

    def register(self, rule_cls):
        self._rules.append(rule_cls())
        return rule_cls

    def run(self, symbol_table):
        diagnostics = []
        for rule in self._rules:
            diagnostics.extend(rule.run(symbol_table))
        return diagnostics

symbol_rule_runner = SymbolRuleRunner()