from typing import Any

from ..base_symbol_rule import BaseSymbolRule
from ...semantic.resolution import ResolutionStatus
from ...semantic.symbol_table import SymbolTable
from ..symbol_rule_runner import symbol_rule_runner


@symbol_rule_runner.register
class NoImplicitNetRule(BaseSymbolRule):
    code = "NO_IMPLICIT_NET"
    category = "semantic_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        for ref in symbol_table.unresolved_references:
            if ref.status is not ResolutionStatus.UNRESOLVED_IMPLICIT_NET or not ref.is_unresolved:
                continue
            if not ref.symbol.uses:
                continue

            loc = ref.symbol.uses[0]
            diagnostic = {
                "code": self.code,
                "line": loc["line"],
                "col": loc["col"],
                "message": f"Implicit net '{ref.name}' is not allowed",
            }
            if "file" in loc:
                diagnostic["file"] = loc["file"]
            diagnostics.append(diagnostic)

        return diagnostics
