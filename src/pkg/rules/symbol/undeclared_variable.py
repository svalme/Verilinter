from typing import Any

from ..base_symbol_rule import BaseSymbolRule
from ...semantic.symbol_table import SymbolTable
from .symbol_rule_runner import symbol_rule_runner

@symbol_rule_runner.register
class UndeclaredVariableRule(BaseSymbolRule):
    code = "UNDECLARED_VARIABLE"

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        for scope in symbol_table.scopes:
            for sym in scope.symbols.values():
                if sym.uses and not sym.declarations:
                    loc = sym.uses[0]
                    diagnostic = {
                        "code": self.code,
                        "line": loc["line"],
                        "col": loc["col"],
                        "message": f"Undeclared variable '{sym.name}'",
                    }
                    if "file" in loc:
                        diagnostic["file"] = loc["file"]
                    diagnostics.append(diagnostic)

        return diagnostics
