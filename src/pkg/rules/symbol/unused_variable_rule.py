from typing import Any

from ..base_symbol_rule import BaseSymbolRule
from ...semantic.symbol_table import SymbolTable
from .symbol_rule_runner import symbol_rule_runner

@symbol_rule_runner.register
class UnusedVariableRule(BaseSymbolRule):
    code = "UNUSED_VARIABLE"

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        for scope in symbol_table.scopes:
            for sym in scope.symbols.values():
                if sym.kind == "variable" and not sym.uses:
                    loc = sym.declarations[0]
                    diagnostic = {
                        "code": self.code,
                        "line": loc["line"],
                        "col": loc["col"],
                        "message": f"Unused variable '{sym.name}'",
                    }
                    if "file" in loc:
                        diagnostic["file"] = loc["file"]
                    diagnostics.append(diagnostic)

        return diagnostics
