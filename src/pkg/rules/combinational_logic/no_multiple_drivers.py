from typing import Any

from ..base_symbol_rule import BaseSymbolRule
from ...parser.syntax import is_mutually_exclusive_branch_pair
from ...semantic.driver_resolver import DriverResolver
from ...semantic.write_region import regions_may_overlap
from ...semantic.symbol import UseEvent
from ...semantic.symbol_table import SymbolTable
from ...semantic.symbol_kind import SymbolKind
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
                if not sym.is_explicit_kind(SymbolKind.VARIABLE):
                    continue

                # An instance's output port is judged by INSTANCE_OUTPUT_DRIVER_CONFLICT and
                # MULTIPLE_INSTANCE_DRIVER_CONFLICT, so it is not counted twice here.
                drivers = DriverResolver(symbol_table).drivers(sym, instance=False, located=True)
                writes_by_driver: dict[str, list[UseEvent]] = {driver.id: list(driver.events) for driver in drivers}
                driver_locations: dict[str, Location] = {driver.id: driver.location for driver in drivers}  # type: ignore[misc]

                if len(writes_by_driver) <= 1:
                    continue

                # Two drivers only conflict if they can both apply at once to the same bits. A pair
                # confined to mutually exclusive `if`/`else` branches -- most commonly a
                # `generate if (PARAM) ... else ...` module/style choice -- is never simultaneously
                # live, and writes to provably disjoint parts of the variable (`v[0]` and `v[1]`)
                # do not drive the same bits.
                # Report the first pair, in encounter order, that genuinely is.
                ordered = list(writes_by_driver)
                conflict: tuple[Location, UseEvent] | None = None
                for i in range(len(ordered)):
                    for other_id in ordered[i + 1 :]:
                        second = self._first_conflicting_write(writes_by_driver[ordered[i]], writes_by_driver[other_id])
                        if second is not None:
                            conflict = (driver_locations[ordered[i]], second)
                            break
                    if conflict is not None:
                        break

                if conflict is None:
                    continue

                first_driver_loc, second_event = conflict
                loc = second_event.get("location") or {}
                first_driver_line = first_driver_loc.get("line", 0) if isinstance(first_driver_loc, dict) else 0

                diagnostic = {
                    "code": self.code,
                    "line": loc.get("line", 0),
                    "col": loc.get("col", 0),
                    "message": (
                        f"Variable '{sym.name}' is written from multiple drivers "
                        f"(first driver at line {first_driver_line})"
                    ),
                }
                if "file" in loc:
                    diagnostic["file"] = loc["file"]
                diagnostics.append(diagnostic)

        return diagnostics

    @staticmethod
    def _first_conflicting_write(first_writes: list[UseEvent], other_writes: list[UseEvent]) -> UseEvent | None:
        """The first write of the other driver that can drive the same bits at the same time as a write of the first."""
        for other in other_writes:
            for earlier in first_writes:
                if regions_may_overlap(
                    earlier.get("write_region", ()), other.get("write_region", ()), distinct_members_disjoint=True
                ) and not (
                    is_mutually_exclusive_branch_pair(
                        earlier.get("branch_signature", ()), other.get("branch_signature", ())
                    )
                ):
                    return other
        return None
