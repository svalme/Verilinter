from typing import Any

from ...semantic.symbol_table import SymbolTable
from ..base_symbol_rule import BaseSymbolRule
from ..connection_analysis import unconnected_port_names
from ..module_rule_runner import module_rule_runner


@module_rule_runner.register
class NoUnconnectedInstancePortsRule(BaseSymbolRule):
    code = "NO_UNCONNECTED_INSTANCE_PORTS"
    category = "module_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        for inst in symbol_table.instantiations:
            names = unconnected_port_names(symbol_table, inst)
            if not names:
                continue
            loc = dict(inst.get("location", {"line": 0, "col": 0}))
            diagnostics.append(
                {
                    "code": self.code,
                    "line": loc.get("line", 0),
                    "col": loc.get("col", 0),
                    "file": loc.get("file"),
                    "message": (
                        f"Instance '{inst.get('instance_name')}' of module '{inst.get('child_module')}' "
                        f"leaves ports unconnected: {', '.join(names)}"
                    ),
                }
            )
        return diagnostics
