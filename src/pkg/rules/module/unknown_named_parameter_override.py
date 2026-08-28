from typing import Any

from ...semantic.symbol_table import SymbolTable
from ..base_symbol_rule import BaseSymbolRule
from .connection_analysis import unknown_named_parameter_override_names
from .module_rule_runner import module_rule_runner


@module_rule_runner.register
class UnknownNamedParameterOverrideRule(BaseSymbolRule):
    code = "UNKNOWN_NAMED_PARAMETER_OVERRIDE"
    category = "module_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        for inst in symbol_table.instantiations:
            unknown = unknown_named_parameter_override_names(symbol_table, inst)
            if not unknown:
                continue
            loc = dict(inst.get("location", {"line": 0, "col": 0}))
            diagnostics.append(
                {
                    "code": self.code,
                    "line": loc.get("line", 0),
                    "col": loc.get("col", 0),
                    "file": loc.get("file"),
                    "message": (
                        f"Instance '{inst.get('instance_name')}' overrides parameters that do not exist on "
                        f"module '{inst.get('child_module')}': {', '.join(unknown)}"
                    ),
                }
            )
        return diagnostics
