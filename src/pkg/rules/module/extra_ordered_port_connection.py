from typing import Any

from ...semantic.symbol_table import SymbolTable
from ..base_symbol_rule import BaseSymbolRule
from .connection_analysis import extra_ordered_connections, module_ports_for
from .module_rule_runner import module_rule_runner


@module_rule_runner.register
class ExtraOrderedPortConnectionRule(BaseSymbolRule):
    code = "EXTRA_ORDERED_PORT_CONNECTION"
    category = "module_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        for inst in symbol_table.instantiations:
            extras = extra_ordered_connections(symbol_table, inst)
            if not extras:
                continue
            port_count = len(module_ports_for(symbol_table, inst.get("child_module")))
            loc = dict(inst.get("location", {"line": 0, "col": 0}))
            diagnostics.append(
                {
                    "code": self.code,
                    "line": loc.get("line", 0),
                    "col": loc.get("col", 0),
                    "file": loc.get("file"),
                    "message": (
                        f"Instance '{inst.get('instance_name')}' provides {len(extras)} more positional "
                        f"connection(s) than module '{inst.get('child_module')}' has ports ({port_count})"
                    ),
                }
            )
        return diagnostics
