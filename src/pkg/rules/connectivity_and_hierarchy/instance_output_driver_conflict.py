from typing import Any

from ...semantic.symbol_table import SymbolTable
from ..base_symbol_rule import BaseSymbolRule
from ..connection_analysis import instance_output_driver_conflicts
from ..module_rule_runner import module_rule_runner


@module_rule_runner.register
class InstanceOutputDriverConflictRule(BaseSymbolRule):
    code = "INSTANCE_OUTPUT_DRIVER_CONFLICT"
    category = "module_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        for inst in symbol_table.instantiations:
            loc = dict(inst.get("location", {"line": 0, "col": 0}))
            for port_name, signal_name in instance_output_driver_conflicts(symbol_table, inst):
                diagnostics.append(
                    {
                        "code": self.code,
                        "line": loc.get("line", 0),
                        "col": loc.get("col", 0),
                        "file": loc.get("file"),
                        "message": (
                            f"Instance '{inst.get('instance_name')}' drives output port '{port_name}' "
                            f"onto '{signal_name}', which is also written elsewhere in module "
                            f"'{inst.get('parent_module')}' -- possible multi-driver conflict"
                        ),
                    }
                )
        return diagnostics
