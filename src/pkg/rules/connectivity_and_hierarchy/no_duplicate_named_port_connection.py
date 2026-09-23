from typing import Any

from ...semantic.symbol_table import SymbolTable
from ..base_symbol_rule import BaseSymbolRule
from ..connection_analysis import duplicate_named_port_names
from ..module_rule_runner import module_rule_runner


@module_rule_runner.register
class NoDuplicateNamedPortConnectionRule(BaseSymbolRule):
    code = "NO_DUPLICATE_NAMED_PORT_CONNECTION"
    category = "module_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        for inst in symbol_table.instantiations:
            duplicates = duplicate_named_port_names(inst)
            if not duplicates:
                continue
            loc = dict(inst.get("location") or {})
            diagnostics.append(
                {
                    "code": self.code,
                    "line": loc.get("line", 0),
                    "col": loc.get("col", 0),
                    "file": loc.get("file"),
                    "message": (
                        f"Instance '{inst.get('instance_name')}' duplicates named port connections: "
                        f"{', '.join(duplicates)}"
                    ),
                }
            )
        return diagnostics
