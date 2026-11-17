from typing import Any

from ...semantic.driver_resolver import DriverResolver
from ...semantic.symbol_table import SymbolTable
from ...semantic.symbol_kind import SymbolKind
from ..base_symbol_rule import BaseSymbolRule
from ..symbol_rule_runner import symbol_rule_runner


@symbol_rule_runner.register
class NoWriteOnlyVariableRule(BaseSymbolRule):
    code = "NO_WRITE_ONLY_VARIABLE"
    category = "semantic_correctness"
    confidence = "heuristic"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    overlaps_with = ("UNUSED_VARIABLE", "UNREAD_INSTANCE_OUTPUT")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        drivers = DriverResolver(symbol_table)

        for scope in symbol_table.scopes:
            for sym in scope.symbols.values():
                if not sym.is_explicit_kind(SymbolKind.VARIABLE):
                    continue
                if sym.is_port or sym.is_intentionally_unused:
                    continue
                # Only a write made here counts. A variable whose only writer is an instance output port is
                # UNREAD_INSTANCE_OUTPUT's finding (it names the instance and port), so it is not reported twice.
                if not drivers.other_writes(sym) or sym.is_read:
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
