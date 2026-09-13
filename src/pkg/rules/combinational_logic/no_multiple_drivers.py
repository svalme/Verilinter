from typing import Any

from ..base_symbol_rule import BaseSymbolRule
from ...parser.syntax import is_mutually_exclusive_branch_pair
from ...semantic.symbol import UseEvent
from ...semantic.symbol_table import SymbolTable
from ...vnodes.base_vnode import Location
from ..symbol_rule_runner import symbol_rule_runner


@symbol_rule_runner.register
class NoMultipleDriversRule(BaseSymbolRule):
    code = "NO_MULTIPLE_DRIVERS"
    category = "semantic_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        for scope in symbol_table.scopes:
            for sym in scope.symbols.values():
                if not sym.is_explicit_kind("variable"):
                    continue

                seen_driver_ids: dict[str, tuple[UseEvent, Location]] = {}

                for event in sym.use_events:
                    if not event["write"]:
                        continue

                    driver_id = event.get("driver_id")
                    driver_location = event.get("driver_location")
                    if driver_id is None or driver_location is None:
                        continue

                    if driver_id not in seen_driver_ids:
                        seen_driver_ids[driver_id] = (event, driver_location)
                        continue

                if len(seen_driver_ids) <= 1:
                    continue

                # Two drivers only conflict if they can both apply at once. A driver
                # pair confined to mutually exclusive `if`/`else` branches -- most
                # commonly a `generate if (PARAM) ... else ...` module/style choice --
                # is never simultaneously live, so it is not a real multi-driver
                # conflict.
                # Report the first pair, in encounter order, that genuinely is.
                ordered = list(seen_driver_ids.values())
                conflict: tuple[Location, UseEvent] | None = None
                for i in range(len(ordered)):
                    event_i, loc_i = ordered[i]
                    for event_j, _loc_j in ordered[i + 1 :]:
                        if not is_mutually_exclusive_branch_pair(
                            event_i.get("branch_signature", ()), event_j.get("branch_signature", ())
                        ):
                            conflict = (loc_i, event_j)
                            break
                    if conflict is not None:
                        break

                if conflict is None:
                    continue

                first_driver_loc, second_event = conflict
                loc = second_event["location"]

                diagnostic = {
                    "code": self.code,
                    "line": loc["line"],
                    "col": loc["col"],
                    "message": (
                        f"Variable '{sym.name}' is written from multiple drivers "
                        f"(first driver at line {first_driver_loc['line']})"
                    ),
                }
                if "file" in loc:
                    diagnostic["file"] = loc["file"]
                diagnostics.append(diagnostic)

        return diagnostics
