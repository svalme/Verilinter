from typing import Any

from ..base_symbol_rule import BaseSymbolRule
from ...parser.syntax import is_mutually_exclusive_branch_pair
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
            BranchSignature = tuple[tuple[int, int], ...]
            buckets: dict[str, dict[str, list[tuple[str, Location, BranchSignature]]]] = {}
            for symbol in scope.symbols.values():
                for event in symbol.use_events:
                    driver_id = event.get("driver_id")
                    if driver_id is None or driver_id not in symbol_table.combinational_driver_ids:
                        continue
                    bucket = buckets.setdefault(driver_id, {"reads": [], "writes": []})
                    key = "writes" if event["write"] else "reads"
                    bucket[key].append((symbol.name, event["location"], event.get("branch_signature", ())))

            graph: dict[str, list[tuple[str, Location]]] = {}
            for bucket in buckets.values():
                for read_name, _read_loc, read_signature in bucket["reads"]:
                    for write_name, write_loc, write_signature in bucket["writes"]:
                        if read_name == write_name:
                            # Self-feedback in one statement (`x = x;`) is
                            # NO_SELF_ASSIGNMENT's concern, not a cycle to report
                            # here.
                            continue
                        if is_mutually_exclusive_branch_pair(read_signature, write_signature):
                            # The read and write live in mutually exclusive `if`/
                            # `else` branches of this block (e.g. an unconditional
                            # default computed one way, overridden another way in a
                            # sibling branch) -- they can never both execute in the
                            # same pass, so there is no real dependency edge here.
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
