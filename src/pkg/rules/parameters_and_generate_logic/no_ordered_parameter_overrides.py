from typing import Any

from ...semantic.symbol_table import SymbolTable
from ..base_symbol_rule import BaseSymbolRule
from ..connection_analysis import has_ordered_parameter_overrides
from ..module_rule_runner import module_rule_runner


@module_rule_runner.register
class NoOrderedParameterOverridesRule(BaseSymbolRule):
    code = "NO_ORDERED_PARAMETER_OVERRIDES"
    category = "module_style"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        for inst in symbol_table.instantiations:
            if not has_ordered_parameter_overrides(inst):
                continue
            loc = dict(inst.get("location") or {})
            diagnostics.append(
                {
                    "code": self.code,
                    "line": loc.get("line", 0),
                    "col": loc.get("col", 0),
                    "file": loc.get("file"),
                    "message": (
                        f"Instance '{inst.get('instance_name')}' uses ordered parameter overrides; "
                        "prefer explicit named parameter bindings"
                    ),
                }
            )
        return diagnostics
