from typing import Any

from ..base_symbol_rule import BaseSymbolRule
from ...semantic.symbol import Symbol, UseEvent
from ...semantic.symbol_table import SymbolTable
from ..symbol_rule_runner import symbol_rule_runner


@symbol_rule_runner.register
class ReadBeforeWriteRule(BaseSymbolRule):
    code = "READ_BEFORE_WRITE"
    message = "Variable read before write"
    category = "semantic_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    overlaps_with = ("NO_UNDRIVEN_OUTPUT_PORT",)

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        for scope in symbol_table.scopes:
            for sym in scope.symbols.values():
                if not sym.is_explicit_kind("variable"):
                    continue
                # A read with no local write is the normal, intended case for input and
                # inout/ref ports (the value comes from outside this scope) -- mirrors the
                # same is_port/port_direction exclusion NO_UNDRIVEN_OUTPUT_PORT and
                # NO_WRITE_ONLY_INPUT_PORT already use. Output ports keep the check: a read
                # before any local write there is the real "undriven output" bug shape.
                if sym.is_port and sym.port_direction in ("input", "inout", "ref"):
                    continue
                # A signal wired into any instance port connection may be driven by
                # that instance's output/inout port -- IdentifierNameHandler always
                # records that occurrence as a plain read since the connected port's
                # direction generally isn't resolvable here (see
                # enclosing_port_connection's docstring), so trusting it would
                # misreport a signal that's actually driven, just not through a
                # locally-visible assignment, as read before write.
                if sym.is_used_in_port_connection:
                    continue

                event = self._disqualifying_read(sym)
                if event is not None:
                    diagnostics.append(self._diagnostic(sym, event))

        return diagnostics

    def _disqualifying_read(self, sym: Symbol) -> UseEvent | None:
        if not sym.is_written:
            # Never driven anywhere in this scope -- the first read is a real
            # uninitialized-read/undriven-signal bug, order aside.
            return next((event for event in sym.use_events if event["read"]), None)

        # Written somewhere, so only a same-block *blocking*-assignment ordering
        # violation is a real hazard from here on:
        # - A write in a different procedural block/continuous assign (a
        #   different `driver_id`) has no execution-order relationship to this
        #   read at all -- they are concurrent constructs, not a sequence, so a
        #   read "before" it in file order proves nothing.
        # - A non-blocking (`<=`) write updates a register that already holds a
        #   value from the previous clock edge; reading it beforehand -- in
        #   this same block (`if (timer) ...; timer <= timer - 1;`) or a
        #   different one -- is normal sequential feedback, not an
        #   uninitialized read.
        # Only a genuine same-block blocking write (`initial begin y = x; x =
        # 1; end`) still means the read really did happen before any value was
        # assigned.
        blocking_write_driver_ids = {
            event.get("driver_id")
            for event in sym.use_events
            if event["write"] and not event.get("is_nonblocking_write")
        }
        seen_blocking_write_by_driver: dict[object, bool] = {}
        for event in sym.use_events:
            driver_id = event.get("driver_id")
            if (
                event["read"]
                and driver_id in blocking_write_driver_ids
                and not seen_blocking_write_by_driver.get(driver_id, False)
            ):
                return event
            if event["write"] and not event.get("is_nonblocking_write"):
                seen_blocking_write_by_driver[driver_id] = True
        return None

    def _diagnostic(self, sym: Symbol, event: UseEvent) -> dict[str, Any]:
        loc = event["location"]
        diagnostic: dict[str, Any] = {
            "code": self.code,
            "line": loc["line"],
            "col": loc["col"],
            "message": f"Variable '{sym.name}' read before write",
        }
        if "file" in loc:
            diagnostic["file"] = loc["file"]
        return diagnostic
