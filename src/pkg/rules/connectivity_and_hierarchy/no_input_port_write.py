from typing import Any

from ...semantic.symbol_table import SymbolTable
from ..base_symbol_rule import BaseSymbolRule
from ..symbol_rule_runner import symbol_rule_runner


@symbol_rule_runner.register
class NoInputPortWriteRule(BaseSymbolRule):
    code = "NO_INPUT_PORT_WRITE"
    category = "semantic_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        for scope in symbol_table.scopes:
            for sym in scope.symbols.values():
                if sym.kind != "variable" or not sym.declarations or sym.is_implicit:
                    continue
                if sym.port_direction != "input":
                    continue

                for event in sym.use_events:
                    if not event["write"]:
                        continue
                    loc = event["location"]
                    diagnostic: dict[str, Any] = {
                        "code": self.code,
                        "line": loc["line"],
                        "col": loc["col"],
                        "message": f"Input port '{sym.name}' should not be written",
                    }
                    if "file" in loc:
                        diagnostic["file"] = loc["file"]
                    diagnostics.append(diagnostic)
                    break

        return diagnostics
