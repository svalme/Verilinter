from typing import Any

from ...semantic.symbol_table import SymbolTable
from ..base_symbol_rule import BaseSymbolRule
from ..connection_analysis import multiple_instance_driver_conflicts
from ..module_rule_runner import module_rule_runner


@module_rule_runner.register
class MultipleInstanceDriverConflictRule(BaseSymbolRule):
    code = "MULTIPLE_INSTANCE_DRIVER_CONFLICT"
    category = "module_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        for inst, port_name, signal_name, first_inst, first_port_name in multiple_instance_driver_conflicts(
            symbol_table
        ):
            loc = dict(inst.get("location", {"line": 0, "col": 0}))
            diagnostics.append(
                {
                    "code": self.code,
                    "line": loc.get("line", 0),
                    "col": loc.get("col", 0),
                    "file": loc.get("file"),
                    "message": (
                        f"Instance '{inst.get('instance_name')}' drives output port '{port_name}' "
                        f"onto '{signal_name}', which is also driven by instance "
                        f"'{first_inst.get('instance_name')}' port '{first_port_name}' in module "
                        f"'{inst.get('parent_module')}' -- possible multi-driver conflict"
                    ),
                }
            )
        return diagnostics
