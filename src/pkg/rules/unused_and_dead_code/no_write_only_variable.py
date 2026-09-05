from typing import Any

from ...semantic.symbol_table import SymbolTable
from ..base_symbol_rule import BaseSymbolRule
from ..symbol_rule_runner import symbol_rule_runner


@symbol_rule_runner.register
class NoWriteOnlyVariableRule(BaseSymbolRule):
    code = "NO_WRITE_ONLY_VARIABLE"
    category = "semantic_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    overlaps_with = ("UNUSED_VARIABLE",)

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        for scope in symbol_table.scopes:
            for sym in scope.symbols.values():
                if not sym.is_explicit_kind("variable"):
                    continue
                if sym.is_port:
                    continue
                if not sym.is_written or sym.is_read:
                    continue

                loc = sym.declarations[0]
                diagnostic: dict[str, Any] = {
                    "code": self.code,
                    "line": loc["line"],
                    "col": loc["col"],
                    "message": f"Variable '{sym.name}' is written but never read",
                }
                if "file" in loc:
                    diagnostic["file"] = loc["file"]
                diagnostics.append(diagnostic)

        return diagnostics
