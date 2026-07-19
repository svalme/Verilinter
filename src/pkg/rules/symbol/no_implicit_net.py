from typing import Any

from ..base_symbol_rule import BaseSymbolRule
from ...semantic.symbol_table import SymbolTable
from .symbol_rule_runner import symbol_rule_runner


@symbol_rule_runner.register
class NoImplicitNetRule(BaseSymbolRule):
    code = "NO_IMPLICIT_NET"

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        for scope in symbol_table.scopes:
            for sym in scope.symbols.values():
                if not sym.is_implicit or sym.kind != "implicit_net" or not sym.uses:
                    continue

                loc = sym.uses[0]
                diagnostic = {
                    "code": self.code,
                    "line": loc["line"],
                    "col": loc["col"],
                    "message": f"Implicit net '{sym.name}' is not allowed",
                }
                if "file" in loc:
                    diagnostic["file"] = loc["file"]
                diagnostics.append(diagnostic)

        return diagnostics
