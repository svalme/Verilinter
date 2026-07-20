from typing import Any

from ..base_symbol_rule import BaseSymbolRule
from ...semantic.symbol_table import SymbolTable
from .symbol_rule_runner import symbol_rule_runner


@symbol_rule_runner.register
class NoMultipleDriversRule(BaseSymbolRule):
    code = "NO_MULTIPLE_DRIVERS"

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        for scope in symbol_table.scopes:
            for sym in scope.symbols.values():
                if sym.kind != "variable" or not sym.declarations or sym.is_implicit:
                    continue

                seen_driver_ids: dict[str, dict[str, Any]] = {}

                for event in sym.use_events:
                    if not event["write"]:
                        continue

                    driver_id = event.get("driver_id")
                    driver_location = event.get("driver_location")
                    if driver_id is None or driver_location is None:
                        continue

                    if driver_id not in seen_driver_ids:
                        seen_driver_ids[driver_id] = event
                        continue

                if len(seen_driver_ids) <= 1:
                    continue

                ordered_events = list(seen_driver_ids.values())
                first = ordered_events[0]
                second = ordered_events[1]
                loc = second["location"]
                first_driver_loc = first["driver_location"]

                diagnostic = {
                    "code": self.code,
                    "line": loc["line"],
                    "col": loc["col"],
                    "message": (
                        f"Variable '{sym.name}' is written from multiple procedural blocks "
                        f"(first driver at line {first_driver_loc['line']})"
                    ),
                }
                if "file" in loc:
                    diagnostic["file"] = loc["file"]
                diagnostics.append(diagnostic)

        return diagnostics
