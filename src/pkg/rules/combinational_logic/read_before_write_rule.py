from ..base_symbol_rule import BaseSymbolRule
from ...semantic.symbol_table import SymbolTable
from ..symbol_rule_runner import symbol_rule_runner


@symbol_rule_runner.register
class ReadBeforeWriteRule(BaseSymbolRule):
    code = "READ_BEFORE_WRITE"
    message = "Variable read before write"
    category = "semantic_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    overlaps_with = ("NO_UNDRIVEN_OUTPUT_PORT",)

    def run(self, symbol_table: SymbolTable) -> list[dict]:
        diagnostics = []

        for scope in symbol_table.scopes:
            for sym in scope.symbols.values():
                if not sym.is_explicit_kind("variable"):
                    continue
                # A read with no local write is the normal, intended case for input and
                # inout/ref ports (the value comes from outside this scope) -- mirrors the
                # same is_port/port_direction exclusion NO_UNDRIVEN_OUTPUT_PORT and
                # NO_WRITE_ONLY_INPUT_PORT already use. Output ports keep the check: a read
                # before any local write there is the real "undriven output" bug shape.
                if sym.is_port and sym.port_direction in ("input", "inout", "ref"):
                    continue

                seen_write = False
                for event in sym.use_events:
                    if event["read"] and not seen_write:
                        loc = event["location"]
                        diagnostic = {
                            "code": self.code,
                            "line": loc["line"],
                            "col": loc["col"],
                            "message": f"Variable '{sym.name}' read before write",
                        }
                        if "file" in loc:
                            diagnostic["file"] = loc["file"]
                        diagnostics.append(diagnostic)
                        break
                    if event["write"]:
                        seen_write = True

        return diagnostics
