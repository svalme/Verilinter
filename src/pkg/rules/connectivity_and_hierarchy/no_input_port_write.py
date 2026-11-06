from typing import Any

from ...semantic.symbol_table import SymbolTable
from ...semantic.symbol_kind import SymbolKind
from ..base_symbol_rule import BaseSymbolRule
from ..symbol_rule_runner import symbol_rule_runner
from ...semantic.scope_kinds import SUBROUTINE_SCOPE_KINDS


@symbol_rule_runner.register
class NoInputPortWriteRule(BaseSymbolRule):
    code = "NO_INPUT_PORT_WRITE"
    category = "semantic_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    overlaps_with = ("NO_WRITE_ONLY_INPUT_PORT",)

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        for scope in symbol_table.scopes:
            # Input formals are local copies and may legally be assigned.
            if scope.kind in SUBROUTINE_SCOPE_KINDS:
                continue
            for sym in scope.symbols.values():
                if not sym.is_explicit_kind(SymbolKind.VARIABLE):
                    continue
                if sym.port_direction != "input":
                    continue

                for event in sym.use_events:
                    if not event["write"]:
                        continue
                    loc = event.get("location") or {}
                    diagnostic: dict[str, Any] = {
                        "code": self.code,
                        "line": loc.get("line", 0),
                        "col": loc.get("col", 0),
                        "message": f"Input port '{sym.name}' should not be written",
                    }
                    if "file" in loc:
                        diagnostic["file"] = loc["file"]
                    diagnostics.append(diagnostic)
                    break

        return diagnostics
