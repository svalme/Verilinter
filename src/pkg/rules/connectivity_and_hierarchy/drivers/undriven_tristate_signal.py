from typing import Any

from ...base_symbol_rule import BaseSymbolRule
from ...connection_analysis import signal_names_connected_to_instances
from ....semantic.driver_resolver import DriverResolver
from ....semantic.symbol_table import SymbolTable
from ....semantic.symbol_kind import SymbolKind
from ...symbol_rule_runner import symbol_rule_runner
from ....semantic.scope_kinds import ScopeKind


@symbol_rule_runner.register
class UndrivenTristateSignalRule(BaseSymbolRule):
    code = "UNDRIVEN_TRISTATE_SIGNAL"
    category = "semantic_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        resolver = DriverResolver(symbol_table)

        for scope in symbol_table.scopes:
            if scope.kind != ScopeKind.MODULE or not scope.name:
                continue
            connected_names = signal_names_connected_to_instances(symbol_table, scope.name)

            for sym in scope.symbols.values():
                if sym.kind is not SymbolKind.VARIABLE or sym.is_port:
                    continue
                if sym.name in connected_names:
                    continue

                found = resolver.drivers(sym)
                if len(found) != 1:
                    continue
                (driver,) = found
                if driver.id not in symbol_table.tristate_driver_ids or driver.location is None:
                    continue

                loc = driver.location
                diagnostic = {
                    "code": self.code,
                    "line": loc["line"],
                    "col": loc["col"],
                    "message": (
                        f"Signal '{sym.name}' is purely internal but only ever driven by a tri-state "
                        f"assignment; nothing can drive it when disabled, so it always resolves to X/Z then"
                    ),
                }
                if "file" in loc:
                    diagnostic["file"] = loc["file"]
                diagnostics.append(diagnostic)

        return diagnostics
