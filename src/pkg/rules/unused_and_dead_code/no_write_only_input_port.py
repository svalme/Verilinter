from typing import Any

from ..base_symbol_rule import BaseSymbolRule
from ...semantic.symbol_table import SymbolTable
from ..symbol_rule_runner import symbol_rule_runner


@symbol_rule_runner.register
class NoWriteOnlyInputPortRule(BaseSymbolRule):
    code = "NO_WRITE_ONLY_INPUT_PORT"
    category = "semantic_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        for scope in symbol_table.scopes:
            for sym in scope.symbols.values():
                if sym.kind != "variable" or not sym.declarations or sym.is_implicit:
                    continue
                if sym.port_direction != "input":
                    continue
                if not sym.is_written or sym.is_read:
                    continue

                loc = sym.declarations[0]
                diagnostic = {
                    "code": self.code,
                    "line": loc["line"],
                    "col": loc["col"],
                    "message": f"Input port '{sym.name}' is written but never read",
                }
                if "file" in loc:
                    diagnostic["file"] = loc["file"]
                diagnostics.append(diagnostic)

        return diagnostics
