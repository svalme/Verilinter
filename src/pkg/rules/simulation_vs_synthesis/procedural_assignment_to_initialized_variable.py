from typing import Any

from ...semantic.symbol_table import SymbolTable
from ..base_symbol_rule import BaseSymbolRule
from ..symbol_rule_runner import symbol_rule_runner
from ...semantic.scope_kinds import SUBROUTINE_SCOPE_KINDS


@symbol_rule_runner.register
class ProceduralAssignmentToInitializedVariableRule(BaseSymbolRule):
    code = "PROCASSINIT"
    category = "semantic_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        for scope in symbol_table.scopes:
            if scope.kind in SUBROUTINE_SCOPE_KINDS:
                continue
            for sym in scope.symbols.values():
                if not sym.has_declaration_initializer:
                    continue
                if sym.is_compile_time_constant or sym.is_port:
                    continue

                decl_loc = sym.declarations[0] if sym.declarations else None
                if not decl_loc:
                    continue

                has_proc_write = False
                for ev in sym.use_events:
                    if not ev.get("write"):
                        continue
                    did = ev.get("driver_id")
                    if not did:
                        continue
                    if did in symbol_table.initial_driver_ids:
                        continue
                    if did in symbol_table.tristate_driver_ids or did.startswith("ContinuousAssign:"):
                        continue
                    if ev.get("location") == decl_loc:
                        continue
                    if (
                        did in symbol_table.combinational_driver_ids
                        or did in symbol_table.sequential_driver_ids
                        or did.startswith("ProceduralBlock:")
                        or did.startswith("SyntaxKind.Always")
                    ):
                        has_proc_write = True
                        break

                if has_proc_write:
                    diagnostic: dict[str, Any] = {
                        "code": self.code,
                        "line": decl_loc["line"],
                        "col": decl_loc["col"],
                        "message": (
                            f"Procedural assignment to declaration with initial value: '{sym.name}'"
                        ),
                    }
                    if "file" in decl_loc:
                        diagnostic["file"] = decl_loc["file"]
                    diagnostics.append(diagnostic)

        return diagnostics
