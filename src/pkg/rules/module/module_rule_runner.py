from ...semantic.symbol_table import SymbolTable


class ModuleRuleRunner:
    """Runs rules that need a cross-file view (the module registry / instantiation
    references), kept separate from SymbolRuleRunner's single-file symbol rules."""

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

module_rule_runner = ModuleRuleRunner()
