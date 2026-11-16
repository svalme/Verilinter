from typing import Any

from ...semantic.partial_drive import format_bit_runs, undriven_bits
from ..base_symbol_rule import BaseSymbolRule
from ...semantic.symbol_table import SymbolTable
from ...semantic.symbol_kind import SymbolKind
from ..symbol_rule_runner import symbol_rule_runner


@symbol_rule_runner.register
class NoUndrivenSignalRule(BaseSymbolRule):
    code = "NO_UNDRIVEN_SIGNAL"
    category = "semantic_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        for scope in symbol_table.scopes:
            for sym in scope.symbols.values():
                if not sym.is_explicit_kind(SymbolKind.VARIABLE) or sym.is_port:
                    continue
                if not sym.is_read:
                    continue
                # A signal wired into a port connection whose direction is not known (the
                # child module is declared in no input file, or the signal is declared in a
                # nested scope) may be driven by that instance, so it is left alone.
                if sym.in_unclassified_port_connection:
                    continue
                if sym.is_unobserved_interface_member:
                    continue
                message = None
                if sym.is_written or sym.is_driven_by_instance:
                    runs = undriven_bits(sym)
                    if runs:
                        message = f"Signal '{sym.name}' is driven only in part: bits {format_bit_runs(runs)} are never driven"
                    else:
                        continue
                else:
                    message = f"Signal '{sym.name}' is read but never driven"

                loc = sym.declarations[0]
                diagnostic = {
                    "code": self.code,
                    "line": loc["line"],
                    "col": loc["col"],
                    "message": message,
                }
                if "file" in loc:
                    diagnostic["file"] = loc["file"]
                diagnostics.append(diagnostic)

        return diagnostics
