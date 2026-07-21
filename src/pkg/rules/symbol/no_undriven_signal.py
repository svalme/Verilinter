from typing import Any

from ..base_symbol_rule import BaseSymbolRule
from ...semantic.symbol_table import SymbolTable
from .symbol_rule_runner import symbol_rule_runner


@symbol_rule_runner.register
class NoUndrivenSignalRule(BaseSymbolRule):
    code = "NO_UNDRIVEN_SIGNAL"

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        for scope in symbol_table.scopes:
            for sym in scope.symbols.values():
                if sym.kind != "variable" or not sym.declarations or sym.is_implicit or sym.is_port:
                    continue
                if not sym.is_read or sym.is_written:
                    continue

                loc = sym.declarations[0]
                diagnostic = {
                    "code": self.code,
                    "line": loc["line"],
                    "col": loc["col"],
                    "message": f"Signal '{sym.name}' is read but never driven",
                }
                if "file" in loc:
                    diagnostic["file"] = loc["file"]
                diagnostics.append(diagnostic)

        return diagnostics
