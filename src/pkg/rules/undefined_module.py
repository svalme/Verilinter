from .base_symbol_rule import BaseSymbolRule
from ..ast.symbol_table import SymbolTable
from .symbol_rule_runner import symbol_rule_runner

@symbol_rule_runner.register
class UndefinedModuleRule(BaseSymbolRule):
    code = "UNDEFINED_MODULE"
    message = "Instantiation of undefined module"

    def run(self, symbol_table: SymbolTable):
        diagnostics = []

        for name, loc in symbol_table.module_references:
            if symbol_table.lookup_module(name) is not None:
                continue

            diagnostic = {
                "line": loc.get("line", 0),
                "col": loc.get("col", 0),
                "message": f"Instantiation of undefined module '{name}'",
            }
            if "file" in loc:
                diagnostic["file"] = loc["file"]
            diagnostics.append(diagnostic)

        return diagnostics
