from typing import Any

from ..base_symbol_rule import BaseSymbolRule
from ...semantic.driver_evidence import DriverEvidence
from ...semantic.driver_kind import DriverKind
from ...semantic.scope_kinds import SUBROUTINE_SCOPE_KINDS
from ...semantic.symbol import Symbol, UseEvent
from ...semantic.symbol_table import SymbolTable
from ...semantic.symbol_kind import SymbolKind
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
                if not sym.is_explicit_kind(SymbolKind.VARIABLE):
                    continue
                # A read with no local write is the normal, intended case for input and
                # inout/ref ports (the value comes from outside this scope) -- mirrors the
                # same is_port/port_direction exclusion NO_UNDRIVEN_OUTPUT_PORT and
                # NO_WRITE_ONLY_INPUT_PORT already use. Output ports keep the check: a read
                # before any local write there is the real "undriven output" bug shape.
                if sym.is_port and sym.port_direction in ("input", "inout", "ref"):
                    continue
                # A signal an instance drives, or one that something this file cannot see may
                # drive, is driven outside any locally visible assignment, so a read of it is
                # not a read before write.
                if sym.driver_evidence in (DriverEvidence.UNSEEN, DriverEvidence.INSTANCE):
                    continue
                if sym.is_event:
                    continue

                event = self._disqualifying_read(sym, symbol_table)
                if event is not None:
                    diagnostics.append(self._diagnostic(sym, event))

        return diagnostics

    def _disqualifying_read(self, sym: Symbol, symbol_table: SymbolTable) -> UseEvent | None:
        if sym.driver_evidence is DriverEvidence.NONE and not sym.has_declaration_initializer:
            # Never driven anywhere in this scope and has no declaration initializer --
            # the first read is a real uninitialized-read/undriven-signal bug, order aside.
            return next((event for event in sym.use_events if event["read"]), None)

        # If the symbol holds persistent state (has a declaration initializer, is driven
        # by a sequential/clocked block, has non-blocking writes, or is initialized in an
        # initial block), it represents persistent state across clock cycles / evaluations
        # rather than an uninitialized combinational temporary.
        if sym.is_persistent_state(symbol_table):
            return None

        # Purely combinational variable or uninitialized temporary from here on.
        # Only a same-block blocking-assignment ordering violation in a combinational
        # block (or initial block) is a hazard:
        # - Sequential clocked blocks are excluded because reads there represent sequential state feedback.
        # - Different driver blocks have no execution-order relationship.
        blocking_write_driver_ids = {
            event.get("driver_id")
            for event in sym.use_events
            if event["write"]
            and not event.get("is_nonblocking_write")
            and symbol_table.driver_kind(event.get("driver_id")) is not DriverKind.SEQUENTIAL
        }
        if not self._is_local_to_subroutine(sym):
            # An event with no driver sits in a function or task body. A module-level variable read there is
            # read when the subroutine is called, so its position in the file says nothing about the order.
            blocking_write_driver_ids.discard(None)
        seen_unconditional_write_by_driver: dict[object, bool] = {}
        seen_branch_write_signatures: dict[object, set[tuple[tuple[str, int], ...]]] = {}
        seen_write_for_none: bool = False

        for event in sym.use_events:
            driver_id = event.get("driver_id")
            if (
                event["read"]
                and driver_id in blocking_write_driver_ids
            ):
                if driver_id is None:
                    if not seen_write_for_none:
                        return event
                else:
                    branch_sig = event.get("branch_signature") or ()
                    # If an unconditional write was already seen in this block, the variable is
                    # guaranteed initialized for all subsequent paths in the block.
                    if not seen_unconditional_write_by_driver.get(driver_id, False):
                        prior_branches = seen_branch_write_signatures.get(driver_id, set())
                        if not self._is_covered_by_writes(branch_sig, prior_branches):
                            return event

            if event["write"] and not event.get("is_nonblocking_write"):
                if driver_id is None:
                    seen_write_for_none = True
                else:
                    branch_sig = event.get("branch_signature") or ()
                    driver_written_sigs = seen_branch_write_signatures.setdefault(driver_id, set())
                    driver_written_sigs.add(branch_sig)
                    if not branch_sig:
                        seen_unconditional_write_by_driver[driver_id] = True
                    else:
                        self._collapse_exhaustive_branches(driver_written_sigs, symbol_table.branch_constructs)
                        if () in driver_written_sigs:
                            seen_unconditional_write_by_driver[driver_id] = True

        return None

    @staticmethod
    def _is_local_to_subroutine(sym: Symbol) -> bool:
        scope = sym.scope
        depth = 0
        while scope is not None and depth < 64:
            depth += 1
            if scope.kind in SUBROUTINE_SCOPE_KINDS:
                return True
            scope = scope.parent
        return False

    @staticmethod
    def _collapse_exhaustive_branches(
        written_sigs: set[tuple[tuple[str, int], ...]],
        branch_constructs: dict[str, tuple[set[int] | None, tuple[tuple[str, int], ...]]],
    ) -> None:
        """Propagate complete write coverage up enclosing branching constructs.

        If all required branch alternatives of a construct are present in `written_sigs`
        under the same parent signature, that construct's parent signature is added to
        `written_sigs`, repeating until no more constructs can be collapsed.
        """
        if () in written_sigs:
            return

        changed = True
        iteration = 0
        while changed and iteration < 64:
            iteration += 1
            changed = False
            branches_by_construct_and_parent: dict[tuple[str, tuple[tuple[str, int], ...]], set[int]] = {}
            for sig in list(written_sigs):
                if sig:
                    cid, branch_idx = sig[0]
                    parent_sig = sig[1:]
                    branches_by_construct_and_parent.setdefault((cid, parent_sig), set()).add(branch_idx)

            for (cid, parent_sig), written_branches in branches_by_construct_and_parent.items():
                if parent_sig in written_sigs:
                    continue
                metadata = branch_constructs.get(cid)
                if metadata is None:
                    continue
                req_branches, _ = metadata
                if req_branches is not None and req_branches.issubset(written_branches):
                    written_sigs.add(parent_sig)
                    changed = True
                    if parent_sig == ():
                        return

    @staticmethod
    def _is_covered_by_writes(
        read_sig: tuple[tuple[str, int], ...],
        written_sigs: set[tuple[tuple[str, int], ...]],
    ) -> bool:
        """Return True if `read_sig` is covered by prior writes in `written_sigs`.

        A read is covered if an unconditional write occurred (`()` in `written_sigs`),
        or if `read_sig` matches a prior written branch signature or is nested inside
        an ancestor branch that was fully written.
        """
        if () in written_sigs:
            return True
        for k in range(len(read_sig) + 1):
            if read_sig[k:] in written_sigs:
                return True
        return False

    def _diagnostic(self, sym: Symbol, event: UseEvent) -> dict[str, Any]:
        loc = event.get("location") or {}
        diagnostic: dict[str, Any] = {
            "code": self.code,
            "line": loc.get("line", 0),
            "col": loc.get("col", 0),
            "message": f"Variable '{sym.name}' read before write",
        }
        if "file" in loc:
            diagnostic["file"] = loc["file"]
        return diagnostic
