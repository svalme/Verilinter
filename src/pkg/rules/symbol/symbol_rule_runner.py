from ...ast.symbol_table import SymbolTable


class SymbolRuleRunner:
    def __init__(self):
        self._rules = []

    def register(self, rule_cls):
        self._rules.append(rule_cls())
        return rule_cls

    def run(self, symbol_table: SymbolTable) -> list[dict]:
        diagnostics = []
        for rule in self._rules:
            diagnostics.extend(rule.run(symbol_table))
        return diagnostics

symbol_rule_runner = SymbolRuleRunner()
