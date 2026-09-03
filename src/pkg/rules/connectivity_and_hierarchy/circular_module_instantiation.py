from typing import Any

from ..base_symbol_rule import BaseSymbolRule
from ...semantic.symbol_table import SymbolTable
from ..module_rule_runner import module_rule_runner

_WHITE, _GRAY, _BLACK = 0, 1, 2


@module_rule_runner.register
class CircularModuleInstantiationRule(BaseSymbolRule):
    code = "CIRCULAR_MODULE_INSTANTIATION"
    category = "module_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        graph: dict[str, list[tuple[str, Any]]] = {}
        for from_module, to_module, loc in symbol_table.instantiation_edges:
            graph.setdefault(from_module, []).append((to_module, loc))

        color: dict[str, int] = {}
        path: list[str] = []
        reported: set[frozenset[str]] = set()

        def visit(node: str) -> None:
            color[node] = _GRAY
            path.append(node)

            for neighbor, loc in graph.get(node, []):
                state = color.get(neighbor, _WHITE)
                if state == _WHITE:
                    visit(neighbor)
                elif state == _GRAY:
                    cycle_start = path.index(neighbor)
                    cycle_nodes = path[cycle_start:] + [neighbor]
                    signature = frozenset(cycle_nodes)
                    if signature in reported:
                        continue
                    reported.add(signature)

                    diagnostic = {
                        "code": self.code,
                        "line": loc.get("line", 0),
                        "col": loc.get("col", 0),
                        "message": (
                            "Circular module instantiation: "
                            + " -> ".join(f"'{name}'" for name in cycle_nodes)
                        ),
                    }
                    if "file" in loc:
                        diagnostic["file"] = loc["file"]
                    diagnostics.append(diagnostic)

            path.pop()
            color[node] = _BLACK

        for module_name in graph:
            if color.get(module_name, _WHITE) == _WHITE:
                visit(module_name)

        return diagnostics
