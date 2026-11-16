from dataclasses import dataclass
from typing import Any

from ...parser.syntax import is_mutually_exclusive_branch_pair
from ..base_symbol_rule import BaseSymbolRule
from ...semantic.symbol_table import SymbolTable
from ...vnodes.base_vnode import Location
from ..symbol_rule_runner import symbol_rule_runner

_WHITE, _GRAY, _BLACK = 0, 1, 2

BranchSignature = tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class _Edge:
    """The value of one variable read in the statement that writes another.

    `read_defined_by` is the statement of the block that last wrote the read variable on every path before
    this read, or None when the read sees the value the block's previous evaluation left."""

    write_name: str
    write_loc: Location
    loop_ids: tuple[str, ...]
    driver_id: str
    write_statement_id: str | None
    read_defined_by: str | None
    branches: tuple[BranchSignature, BranchSignature]


@symbol_rule_runner.register
class CombinationalLoopRule(BaseSymbolRule):
    code = "COMBINATIONAL_LOOP"
    category = "semantic_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        for scope in symbol_table.scopes:
            Event = tuple[str, Location, str | None, tuple[str, ...], BranchSignature]
            buckets: dict[str, dict[str, list[Event]]] = {}
            for symbol in scope.symbols.values():
                for event in symbol.use_events:
                    driver_id = event.get("driver_id")
                    if driver_id is None or driver_id not in symbol_table.combinational_driver_ids:
                        continue
                    bucket = buckets.setdefault(driver_id, {"reads": [], "writes": []})
                    key = "writes" if event["write"] else "reads"
                    bucket[key].append(
                        (
                            symbol.name,
                            event["location"],
                            event.get("statement_id"),
                            event.get("loop_ids", ()),
                            event.get("branch_signature") or (),
                        )
                    )

            graph: dict[str, list[_Edge]] = {}
            for driver_id, bucket in buckets.items():
                for read_name, read_loc, read_statement_id, _read_loop_ids, read_branch in bucket["reads"]:
                    defined_by = self._defining_statement(read_name, read_loc, read_statement_id, bucket["writes"])
                    for write_name, write_loc, write_statement_id, write_loop_ids, write_branch in bucket["writes"]:
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
                        graph.setdefault(read_name, []).append(
                            _Edge(
                                write_name,
                                write_loc,
                                write_loop_ids,
                                driver_id,
                                write_statement_id,
                                defined_by,
                                (read_branch, write_branch),
                            )
                        )

            diagnostics.extend(self._find_cycles(graph))

        return diagnostics

    @staticmethod
    def _defining_statement(
        name: str, read_loc: Location, read_statement_id: str | None, writes: list[Any]
    ) -> str | None:
        """The statement that last wrote `name` on every path before this read, or None for a read of the
        value left by the block's previous evaluation."""
        read_position = (read_loc.get("line", 0), read_loc.get("col", 0))
        best: tuple[tuple[int, int], str | None] | None = None
        for write_name, write_loc, write_statement_id, _loops, write_branch in writes:
            if write_name != name or write_branch or write_statement_id == read_statement_id:
                continue
            position = (write_loc.get("line", 0), write_loc.get("col", 0))
            if position < read_position and (best is None or position > best[0]):
                best = (position, write_statement_id)
        return best[1] if best is not None else None

    @staticmethod
    def _chain_is_consistent(incoming: _Edge, outgoing: _Edge) -> bool:
        """Whether the value that `incoming` writes is the value that `outgoing` reads.

        Within one block, a read that follows an unconditional write of the variable reads that write's value,
        so a cycle can only continue through that same statement. A read of the block's previous value
        continues from the block's final write."""
        if incoming.driver_id != outgoing.driver_id or outgoing.read_defined_by is None:
            return True
        return outgoing.read_defined_by == incoming.write_statement_id

    def _find_cycles(self, graph: dict[str, list[_Edge]]) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        color: dict[str, int] = {}
        path: list[tuple[str, frozenset[str]]] = []
        path_edges: list[_Edge | None] = []
        reported: set[frozenset[str]] = set()

        def visit(node: str, incoming_loop_ids: frozenset[str], depth: int = 0, incoming_edge: _Edge | None = None) -> None:
            if depth >= 256:
                return
            color[node] = _GRAY
            path.append((node, incoming_loop_ids))
            path_edges.append(incoming_edge)

            for edge in graph.get(node, []):
                neighbor, loc, loop_ids = edge.write_name, edge.write_loc, edge.loop_ids
                state = color.get(neighbor, _WHITE)
                edge_loop_ids = frozenset(loop_ids)
                if state == _WHITE:
                    visit(neighbor, edge_loop_ids, depth + 1, edge)
                elif state == _GRAY:
                    cycle_start = next(i for i, (n, _) in enumerate(path) if n == neighbor)
                    cycle_edges = [e for e in path_edges[cycle_start + 1:] if e is not None] + [edge]
                    # Edge k leaves one variable and enters the next, which edge k + 1 then reads.
                    closing = cycle_edges + [cycle_edges[0]]
                    if not all(self._chain_is_consistent(closing[i], closing[i + 1]) for i in range(len(cycle_edges))):
                        continue
                    branches = [b for e in cycle_edges for b in e.branches]
                    if any(
                        is_mutually_exclusive_branch_pair(a, b) for i, a in enumerate(branches) for b in branches[i + 1:]
                    ):
                        # Two edges of the cycle sit in different branches of one if or generate construct, so
                        # at most one of them exists at a time.
                        continue
                    cycle_nodes = [n for n, _ in path[cycle_start:]] + [neighbor]
                    signature = frozenset(cycle_nodes)
                    if signature in reported:
                        continue

                    cycle_entries = path[cycle_start:] + [(neighbor, edge_loop_ids)]
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
            path_edges.pop()
            color[node] = _BLACK

        for node_name in graph:
            if color.get(node_name, _WHITE) == _WHITE:
                visit(node_name, frozenset())

        return diagnostics
