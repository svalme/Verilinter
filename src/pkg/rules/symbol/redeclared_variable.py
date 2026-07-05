from ..base_symbol_rule import BaseSymbolRule
from ...ast.symbol_table import SymbolTable
from .symbol_rule_runner import symbol_rule_runner

@symbol_rule_runner.register
class RedeclaredVariableRule(BaseSymbolRule):

    def run(self, symbol_table: SymbolTable):
        diagnostics = []

        for scope in symbol_table.scopes:
            for sym in scope.symbols.values():
                if not sym.is_implicit and len(sym.declarations) > 1:
                    for loc in sym.declarations[1:]:
                        diagnostic = {
                            "line": loc["line"],
                            "col": loc["col"],
                            "message": f"Redeclared symbol '{sym.name}' (first declared at line {sym.declarations[0]['line']})",
                        }
                        if "file" in loc:
                            diagnostic["file"] = loc["file"]
                        diagnostics.append(diagnostic)

        return diagnostics
