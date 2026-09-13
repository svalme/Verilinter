from typing import Any

from ..base_symbol_rule import BaseSymbolRule
from ...semantic.symbol_table import SymbolTable
from ...vnodes.base_vnode import Location
from ..symbol_rule_runner import symbol_rule_runner

_WHITE, _GRAY, _BLACK = 0, 1, 2


@symbol_rule_runner.register
class CombinationalLoopRule(BaseSymbolRule):
    code = "COMBINATIONAL_LOOP"
    category = "semantic_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        for scope in symbol_table.scopes:
            Event = tuple[str, Location, str | None]
            buckets: dict[str, dict[str, list[Event]]] = {}
            for symbol in scope.symbols.values():
                for event in symbol.use_events:
                    driver_id = event.get("driver_id")
                    if driver_id is None or driver_id not in symbol_table.combinational_driver_ids:
                        continue
                    bucket = buckets.setdefault(driver_id, {"reads": [], "writes": []})
                    key = "writes" if event["write"] else "reads"
                    bucket[key].append((symbol.name, event["location"], event.get("statement_id")))

            graph: dict[str, list[tuple[str, Location]]] = {}
            for bucket in buckets.values():
                for read_name, _read_loc, read_statement_id in bucket["reads"]:
                    for write_name, write_loc, write_statement_id in bucket["writes"]:
                        if read_name == write_name:
                            # Self-feedback in one statement (`x = x;`) is
                            # NO_SELF_ASSIGNMENT's concern, not a cycle to report
                            # here.
                            continue
                        if (
                            read_statement_id is None
                            or write_statement_id is None
                            or read_statement_id != write_statement_id
                        ):
                            # A block-level bucket groups every read/write in the
                            # whole procedural block or continuous assign, but a
                            # write only actually depends on a read when that
                            # read appears in *this* write's own assignment
                            # expression -- not merely somewhere else in the same
                            # block. See enclosing_assignment_expression's
                            # docstring for the false positive this closes.
                            continue
                        graph.setdefault(read_name, []).append((write_name, write_loc))

            diagnostics.extend(self._find_cycles(graph))

        return diagnostics

    def _find_cycles(self, graph: dict[str, list[tuple[str, Location]]]) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
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
                            "Combinational feedback loop: "
                            + " -> ".join(f"'{name}'" for name in cycle_nodes)
                        ),
                    }
                    if "file" in loc:
                        diagnostic["file"] = loc["file"]
                    diagnostics.append(diagnostic)

            path.pop()
            color[node] = _BLACK

        for node_name in graph:
            if color.get(node_name, _WHITE) == _WHITE:
                visit(node_name)

        return diagnostics
