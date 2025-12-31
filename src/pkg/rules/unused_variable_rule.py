from .base_symbol_rule import BaseSymbolRule
from ..ast.symbol_table import SymbolTable
from .symbol_rule_runner import symbol_rule_runner

@symbol_rule_runner.register
class UnusedVariableRule(BaseSymbolRule):

    def run(self, symbol_table: SymbolTable):
        diagnostics = []

        for scope in symbol_table.scopes:
            for sym in scope.symbols.values():
                if sym.kind == "variable" and not sym.uses:
                    diagnostics.append({
                        "line": sym.declarations[0]["line"],
                        "col": sym.declarations[0]["col"],
                        "message": f"Unused variable '{sym.name}'",
                    })

        return diagnostics
