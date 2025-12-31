from .base_symbol_rule import BaseSymbolRule
from ..ast.symbol_table import SymbolTable
from .symbol_rule_runner import symbol_rule_runner

@symbol_rule_runner.register
class UndeclaredVariableRule(BaseSymbolRule):

    def run(self, symbol_table: SymbolTable):
        diagnostics = []

        for scope in symbol_table.scopes:
            for sym in scope.symbols.values():
                if sym.uses and not sym.declarations:
                    diagnostics.append({
                        "line": sym.uses[0]["line"],
                        "col": sym.uses[0]["col"],
                        "message": f"Undeclared variable '{sym.name}'",
                    })

        return diagnostics
