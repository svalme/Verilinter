from typing import Any

from ..base_symbol_rule import BaseSymbolRule
from ...semantic.symbol_table import SymbolTable
from ...semantic.symbol_kind import SymbolKind
from ..symbol_rule_runner import symbol_rule_runner


@symbol_rule_runner.register
class NoUndrivenOutputPortRule(BaseSymbolRule):
    code = "NO_UNDRIVEN_OUTPUT_PORT"
    category = "semantic_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    overlaps_with = ("UNUSED_VARIABLE", "READ_BEFORE_WRITE")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        for scope in symbol_table.scopes:
            for sym in scope.symbols.values():
                if not sym.is_explicit_kind(SymbolKind.VARIABLE):
                    continue
                if sym.port_direction != "output":
                    continue
                if not sym.is_read or sym.is_written or sym.is_driven_by_instance:
                    continue
                # A port that something outside this file may drive is left alone.
                if sym.may_have_unseen_driver:
                    continue

                loc = sym.declarations[0]
                diagnostic = {
                    "code": self.code,
                    "line": loc["line"],
                    "col": loc["col"],
                    "message": f"Output port '{sym.name}' is read but never driven",
                }
                if "file" in loc:
                    diagnostic["file"] = loc["file"]
                diagnostics.append(diagnostic)

        return diagnostics
