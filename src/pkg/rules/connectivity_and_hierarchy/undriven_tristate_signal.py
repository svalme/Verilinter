from typing import Any

from ..base_symbol_rule import BaseSymbolRule
from ..connection_analysis import signal_names_connected_to_instances
from ...semantic.symbol_table import SymbolTable
from ..symbol_rule_runner import symbol_rule_runner


@symbol_rule_runner.register
class UndrivenTristateSignalRule(BaseSymbolRule):
    code = "UNDRIVEN_TRISTATE_SIGNAL"
    category = "semantic_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        for scope in symbol_table.scopes:
            if scope.kind != "module" or not scope.name:
                continue
            connected_names = signal_names_connected_to_instances(symbol_table, scope.name)

            for sym in scope.symbols.values():
                if sym.kind != "variable" or sym.is_implicit or sym.is_port:
                    continue
                if sym.name in connected_names:
                    continue

                driver_ids = {
                    event["driver_id"] for event in sym.use_events if event["write"] and "driver_id" in event
                }
                if len(driver_ids) != 1:
                    continue
                (driver_id,) = driver_ids
                if driver_id not in symbol_table.tristate_driver_ids:
                    continue

                loc = next(
                    event["driver_location"]
                    for event in sym.use_events
                    if event["write"] and event.get("driver_id") == driver_id and "driver_location" in event
                )
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
