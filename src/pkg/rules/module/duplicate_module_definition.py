from ..base_symbol_rule import BaseSymbolRule
from ...ast.symbol_table import SymbolTable
from .module_rule_runner import module_rule_runner

@module_rule_runner.register
class DuplicateModuleDefinitionRule(BaseSymbolRule):
    code = "DUPLICATE_MODULE"
    message = "Duplicate module definition"

    def run(self, symbol_table: SymbolTable):
        diagnostics = []

        for name, scopes in symbol_table.modules.items():
            if len(scopes) <= 1:
                continue

            first = scopes[0]
            first_file = first.location.get("file") if first.location else first.file

            for scope in scopes[1:]:
                loc = scope.location or {"line": 0, "col": 0}
                diagnostic = {
                    "line": loc.get("line", 0),
                    "col": loc.get("col", 0),
                    "message": f"Duplicate module '{name}' (first defined in {first_file})",
                }
                if "file" in loc:
                    diagnostic["file"] = loc["file"]
                diagnostics.append(diagnostic)

        return diagnostics
