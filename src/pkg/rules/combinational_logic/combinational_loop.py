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
            Event = tuple[str, Location, str | None, tuple[str, ...]]
            buckets: dict[str, dict[str, list[Event]]] = {}
            for symbol in scope.symbols.values():
                for event in symbol.use_events:
                    driver_id = event.get("driver_id")
                    if driver_id is None or driver_id not in symbol_table.combinational_driver_ids:
                        continue
                    bucket = buckets.setdefault(driver_id, {"reads": [], "writes": []})
                    key = "writes" if event["write"] else "reads"
                    bucket[key].append(
                        (symbol.name, event["location"], event.get("statement_id"), event.get("loop_ids", ()))
                    )

            graph: dict[str, list[tuple[str, Location, tuple[str, ...]]]] = {}
            for bucket in buckets.values():
                for read_name, _read_loc, read_statement_id, _read_loop_ids in bucket["reads"]:
                    for write_name, write_loc, write_statement_id, write_loop_ids in bucket["writes"]:
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
                        graph.setdefault(read_name, []).append((write_name, write_loc, write_loop_ids))

            diagnostics.extend(self._find_cycles(graph))

        return diagnostics

    def _find_cycles(self, graph: dict[str, list[tuple[str, Location, tuple[str, ...]]]]) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        color: dict[str, int] = {}
        path: list[tuple[str, frozenset[str]]] = []
        reported: set[frozenset[str]] = set()

        def visit(node: str, incoming_loop_ids: frozenset[str]) -> None:
            color[node] = _GRAY
            path.append((node, incoming_loop_ids))

            for neighbor, loc, loop_ids in graph.get(node, []):
                state = color.get(neighbor, _WHITE)
                edge_loop_ids = frozenset(loop_ids)
                if state == _WHITE:
                    visit(neighbor, edge_loop_ids)
                elif state == _GRAY:
                    cycle_start = next(i for i, (n, _) in enumerate(path) if n == neighbor)
                    cycle_entries = path[cycle_start:] + [(neighbor, edge_loop_ids)]
                    cycle_nodes = [n for n, _ in cycle_entries]
                    signature = frozenset(cycle_nodes)
                    if signature in reported:
                        continue

                    edge_loop_id_sets = [entry_loop_ids for _, entry_loop_ids in cycle_entries[1:]]
                    common_loops = (
                        edge_loop_id_sets[0].intersection(*edge_loop_id_sets[1:]) if edge_loop_id_sets else frozenset()
                    )
                    if common_loops:
                        # Every write forming this cycle happens inside a shared
                        # `for` loop (not necessarily the *same* nesting depth --
                        # e.g. one write directly in an outer loop, another in an
                        # inner loop nested inside it) -- the standard
                        # unrolled-accumulator idiom (`next_rdt = next_rd ^ ...;
                        # next_rd = next_rdt;`, same names reused for
                        # "previous"/"new" value across iterations), not real
                        # simultaneous feedback. See enclosing_for_loop_ids's
                        # docstring.
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
                visit(node_name, frozenset())

        return diagnostics
