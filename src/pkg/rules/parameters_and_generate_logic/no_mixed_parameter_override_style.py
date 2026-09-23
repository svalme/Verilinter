from typing import Any

from ...semantic.symbol_table import SymbolTable
from ..base_symbol_rule import BaseSymbolRule
from ..module_rule_runner import module_rule_runner


@module_rule_runner.register
class NoMixedParameterOverrideStyleRule(BaseSymbolRule):
    code = "NO_MIXED_PARAMETER_OVERRIDE_STYLE"
    category = "module_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        for inst in symbol_table.instantiations:
            if inst.get("parameter_override_style") != "mixed":
                continue
            loc = dict(inst.get("location") or {})
            diagnostics.append(
                {
                    "code": self.code,
                    "line": loc.get("line", 0),
                    "col": loc.get("col", 0),
                    "file": loc.get("file"),
                    "message": (
                        f"Instance '{inst.get('instance_name')}' mixes named and ordered parameter overrides"
                    ),
                }
            )
        return diagnostics
