from typing import Any

from ..base_symbol_rule import BaseSymbolRule
from ...semantic.symbol_table import SymbolTable
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
                if not sym.is_explicit_kind("variable") or sym.is_port:
                    continue
                if not sym.is_read or sym.is_written:
                    continue
                # A signal wired into any instance port connection may be driven by
                # that instance's output/inout port -- always recorded as a plain
                # read here since the connected port's direction generally isn't
                # resolvable from a single-file walk (see
                # enclosing_port_connection's docstring). Flagging it as never
                # driven would misreport genuine instance-driven wiring.
                if sym.is_used_in_port_connection:
                    continue

                loc = sym.declarations[0]
                diagnostic = {
                    "code": self.code,
                    "line": loc["line"],
                    "col": loc["col"],
                    "message": f"Signal '{sym.name}' is read but never driven",
                }
                if "file" in loc:
                    diagnostic["file"] = loc["file"]
                diagnostics.append(diagnostic)

        return diagnostics
