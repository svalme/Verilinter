from typing import Any

from ....parser.syntax import is_mutually_exclusive_branch_pair
from ....semantic.instance_effects import instance_driver_parts, is_instance_driver_id
from ....semantic.scope import enclosing_module_scope
from ....semantic.symbol import UseEvent
from ....semantic.symbol_kind import SymbolKind
from ....semantic.symbol_table import SymbolTable
from ....semantic.write_region import regions_may_overlap
from ...base_symbol_rule import BaseSymbolRule
from ...symbol_rule_runner import symbol_rule_runner


def _instance_key(event: UseEvent) -> tuple[object, object, object]:
    location = event.get("driver_location") or {}
    return (location.get("file"), location.get("line"), location.get("col"))


@symbol_rule_runner.register
class MultipleInstanceDriverConflictRule(BaseSymbolRule):
    """Two or more instances bind their output or inout ports to the same signal.

    Reads the write events that `apply_instance_port_effects` gives the signal, so two instances in different
    generate blocks that each connect their own wire of the same name are not a conflict. Deliberately scoped
    to distinct instances: one instance binding two of its own ports to one net is a different bug shape."""

    code = "MULTIPLE_INSTANCE_DRIVER_CONFLICT"
    category = "module_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        for scope in symbol_table.scopes:
            for sym in scope.symbols.values():
                if not sym.is_explicit_kind(SymbolKind.VARIABLE):
                    continue
                drivers: dict[str, UseEvent] = {}
                for event in sym.use_events:
                    driver_id = event.get("driver_id")
                    if event["write"] and is_instance_driver_id(driver_id):
                        drivers.setdefault(str(driver_id), event)
                if len(drivers) < 2:
                    continue
                module = enclosing_module_scope(sym.scope)
                ordered = list(drivers.items())
                for index, (driver_id, event) in enumerate(ordered):
                    prior = next(
                        (
                            (prior_id, prior_event)
                            for prior_id, prior_event in ordered[:index]
                            if _instance_key(prior_event) != _instance_key(event)
                            and regions_may_overlap(
                                prior_event.get("write_region", ()),
                                event.get("write_region", ()),
                                distinct_members_disjoint=True,
                            )
                            and not is_mutually_exclusive_branch_pair(
                                event.get("branch_signature", ()), prior_event.get("branch_signature", ())
                            )
                        ),
                        None,
                    )
                    if prior is None:
                        continue
                    instance_name, port_name = instance_driver_parts(driver_id)
                    first_name, first_port = instance_driver_parts(prior[0])
                    loc = dict(event.get("driver_location") or {})
                    diagnostics.append(
                        {
                            "code": self.code,
                            "line": loc.get("line", 0),
                            "col": loc.get("col", 0),
                            "file": loc.get("file"),
                            "message": (
                                f"Instance '{instance_name}' drives output port '{port_name}' "
                                f"onto '{sym.name}', which is also driven by instance "
                                f"'{first_name}' port '{first_port}' in module "
                                f"'{module.name if module is not None else ''}' -- possible multi-driver conflict"
                            ),
                        }
                    )
        return diagnostics
