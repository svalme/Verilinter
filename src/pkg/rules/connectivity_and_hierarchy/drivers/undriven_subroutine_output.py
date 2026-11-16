from typing import Any

from ...base_symbol_rule import BaseSymbolRule
from ....semantic.symbol_table import SymbolTable
from ...symbol_rule_runner import symbol_rule_runner

SUBROUTINE_SCOPE_KINDS = ("task", "function")


@symbol_rule_runner.register
class UndrivenSubroutineOutputRule(BaseSymbolRule):
    code = "UNDRIVEN_SUBROUTINE_OUTPUT"
    category = "semantic_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    overlaps_with = ("UNUSED_VARIABLE",)

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        for scope in symbol_table.scopes:
            if scope.kind not in SUBROUTINE_SCOPE_KINDS:
                continue
            for sym in scope.symbols.values():
                if sym.port_direction != "output" or sym.is_written or not sym.declarations:
                    continue

                loc = sym.declarations[0]
                diagnostic = {
                    "code": self.code,
                    "line": loc["line"],
                    "col": loc["col"],
                    "message": f"Output '{sym.name}' of {scope.kind} '{scope.name}' is never assigned",
                }
                if "file" in loc:
                    diagnostic["file"] = loc["file"]
                diagnostics.append(diagnostic)

        return diagnostics
