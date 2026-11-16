from typing import Any

from ....parser.syntax import is_mutually_exclusive_branch_pair
from ....semantic.instance_effects import instance_driver_parts, is_instance_driver_id
from ....semantic.scope import enclosing_module_scope
from ....semantic.symbol_kind import SymbolKind
from ....semantic.symbol_table import SymbolTable
from ....semantic.write_region import regions_may_overlap
from ...base_symbol_rule import BaseSymbolRule
from ...symbol_rule_runner import symbol_rule_runner


@symbol_rule_runner.register
class InstanceOutputDriverConflictRule(BaseSymbolRule):
    """An instance's output or inout port drives a signal that something else in the module also writes.

    Reads the write events that `apply_instance_port_effects` gives the signal, so the signal is the one the
    connection names in the scope the instance sits in (a wire inside a generate block is not the module-level
    wire of the same name)."""

    code = "INSTANCE_OUTPUT_DRIVER_CONFLICT"
    category = "module_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        for scope in symbol_table.scopes:
            for sym in scope.symbols.values():
                if not sym.is_explicit_kind(SymbolKind.VARIABLE):
                    continue
                writes = [event for event in sym.use_events if event["write"]]
                instance_writes = [event for event in writes if is_instance_driver_id(event.get("driver_id"))]
                other_writes = [event for event in writes if not is_instance_driver_id(event.get("driver_id"))]
                if not instance_writes or not other_writes:
                    continue
                module = enclosing_module_scope(sym.scope)
                reported: set[str] = set()
                for event in instance_writes:
                    driver_id = str(event.get("driver_id"))
                    if driver_id in reported:
                        continue
                    # A write confined to a `generate if`/`else` branch mutually exclusive with this
                    # instantiation's own branch can never coexist with this connection. Only skip when
                    # every other write is exclusive; a genuine co-existing write anywhere still flags.
                    if not any(
                        regions_may_overlap(
                            event.get("write_region", ()), other.get("write_region", ()), distinct_members_disjoint=True
                        )
                        and not is_mutually_exclusive_branch_pair(
                            event.get("branch_signature", ()), other.get("branch_signature", ())
                        )
                        for other in other_writes
                    ):
                        continue
                    reported.add(driver_id)
                    instance_name, port_name = instance_driver_parts(driver_id)
                    loc = dict(event.get("driver_location") or {})
                    diagnostics.append(
                        {
                            "code": self.code,
                            "line": loc.get("line", 0),
                            "col": loc.get("col", 0),
                            "file": loc.get("file"),
                            "message": (
                                f"Instance '{instance_name}' drives output port '{port_name}' "
                                f"onto '{sym.name}', which is also written elsewhere in module "
                                f"'{module.name if module is not None else ''}' -- possible multi-driver conflict"
                            ),
                        }
                    )
        return diagnostics
