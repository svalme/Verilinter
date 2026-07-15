from ..base_symbol_rule import BaseSymbolRule
from ...semantic.symbol_table import SymbolTable
from .symbol_rule_runner import symbol_rule_runner


@symbol_rule_runner.register
class ReadBeforeWriteRule(BaseSymbolRule):
    code = "READ_BEFORE_WRITE"
    message = "Variable read before write"

    def run(self, symbol_table: SymbolTable) -> list[dict]:
        diagnostics = []

        for scope in symbol_table.scopes:
            for sym in scope.symbols.values():
                if sym.kind != "variable" or not sym.declarations or sym.is_implicit:
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
