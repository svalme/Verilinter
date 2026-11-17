from typing import Any

from ....semantic.driver_resolver import DriverResolver, write_events
from ....semantic.symbol_table import SymbolTable
from ...base_symbol_rule import BaseSymbolRule
from ...symbol_rule_runner import symbol_rule_runner
from ....semantic.scope_kinds import SUBROUTINE_SCOPE_KINDS, ScopeKind


@symbol_rule_runner.register
class ProceduralAssignmentToInitializedVariableRule(BaseSymbolRule):
    code = "PROCASSINIT"
    category = "semantic_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        drivers = DriverResolver(symbol_table)

        for scope in symbol_table.scopes:
            if scope.kind in SUBROUTINE_SCOPE_KINDS:
                continue
            # A variable declared in a for-loop header takes its initializer from the loop and is written by
            # the loop step, so neither is a procedural write to a variable initialized at declaration.
            if scope.kind == ScopeKind.FOR:
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
                for ev in write_events(sym):
                    did = ev.get("driver_id")
                    if not did:
                        continue
                    # Only a write made by an always block counts: a continuous assign, an initial block, a
                    # final block and an instance port are not procedural writes to the declared variable.
                    kind = drivers.kind_of(did)
                    if kind is None or not kind.is_procedural_always:
                        continue
                    if ev.get("location") == decl_loc:
                        continue
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
