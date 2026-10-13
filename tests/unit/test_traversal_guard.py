"""Unit tests for the TraversalGuard and ActivePath architecture subsystem."""
from __future__ import annotations

from typing import Iterator
from unittest.mock import Mock

import pytest

from src.pkg.parser.traversal_guard import (
    ActivePath,
    TruncationEvent,
    ast_descendants_iter,
    collect_truncations,
    get_current_truncations,
    guarded_generator,
    guarded_traversal,
    record_truncation,
)
from src.pkg.parser.types import SyntaxNode


class MockNode:
    """Mock AST node for traversal guard testing."""

    def __init__(self, name: str, children: list[object] | None = None) -> None:
        self.name = name
        self.children = children if children is not None else []

    def __iter__(self) -> Iterator[object]:
        return iter(self.children)

    def __repr__(self) -> str:
        return f"MockNode({self.name})"


class TestActivePath:
    def test_normal_traversal_enters_and_exits(self) -> None:
        path = ActivePath(max_depth=10)
        n1 = MockNode("n1")
        n2 = MockNode("n2")

        with path.enter(n1) as scope1:
            assert scope1
            child_path = path.next_level()
            assert child_path.depth == 1
            with child_path.enter(n2) as scope2:
                assert scope2

    def test_self_cycle_rejected(self) -> None:
        path = ActivePath(max_depth=10)
        n1 = MockNode("n1")

        with path.enter(n1) as scope1:
            assert scope1
            with path.enter(n1) as scope2:
                assert not scope2

    def test_ring_cycle_rejected(self) -> None:
        path = ActivePath(max_depth=10)
        a = MockNode("a")
        b = MockNode("b")

        with path.enter(a) as s_a:
            assert s_a
            p2 = path.next_level()
            with p2.enter(b) as s_b:
                assert s_b
                p3 = p2.next_level()
                with p3.enter(a) as s_cycle:
                    assert not s_cycle

    def test_depth_limit_rejected(self) -> None:
        path = ActivePath(max_depth=2)
        n0 = MockNode("n0")
        n1 = MockNode("n1")
        n2 = MockNode("n2")

        with path.enter(n0) as s0:
            assert s0
            p1 = path.next_level()
            with p1.enter(n1) as s1:
                assert s1
                p2 = p1.next_level()
                with p2.enter(n2) as s2:
                    assert not s2

    def test_sibling_reused_address_not_rejected(self) -> None:
        path = ActivePath(max_depth=10)
        # Sibling 1 enters and exits
        n1 = MockNode("n1")
        with path.enter(n1) as s1:
            assert s1
        # Sibling 2 (even if it had the same id) enters cleanly
        n2 = MockNode("n2")
        with path.enter(n2) as s2:
            assert s2


class TestGuardedTraversalDecorator:
    def test_recursive_search_with_cycle_immunity(self) -> None:
        @guarded_traversal(max_depth=16, default=False)
        def contains_target(node: object, target_name: str) -> bool:
            if getattr(node, "name", None) == target_name:
                return True
            for child in getattr(node, "children", ()):
                if contains_target(child, target_name):
                    return True
            return False

        # Tree
        root = MockNode("root", [MockNode("c1"), MockNode("c2", [MockNode("target")])])
        assert contains_target(root, "target") is True
        assert contains_target(root, "nonexistent") is False

        # Self cycle
        cycle = MockNode("cycle")
        cycle.children = [cycle]
        assert contains_target(cycle, "nonexistent") is False

        # Multi-node ring cycle
        a = MockNode("a")
        b = MockNode("b")
        c = MockNode("c")
        a.children = [b]
        b.children = [c]
        c.children = [a]
        assert contains_target(a, "nonexistent") is False

    def test_named_node_arg_extraction(self) -> None:
        @guarded_traversal(node_arg="expr", max_depth=16, default=-1)
        def eval_simple(scope: object, expr: object) -> int:
            if getattr(expr, "name", None) == "val":
                return 42
            for child in getattr(expr, "children", ()):
                res = eval_simple(scope, child)
                if res != -1:
                    return res
            return -1

        node = MockNode("parent", [MockNode("val")])
        assert eval_simple("dummy_scope", node) == 42
        assert eval_simple(scope="dummy_scope", expr=node) == 42

        # Cycle on expr
        cyc = MockNode("cyc")
        cyc.children = [cyc]
        assert eval_simple("dummy_scope", cyc) == -1


class TestGuardedGeneratorDecorator:
    def test_recursive_generator_with_cycle_immunity(self) -> None:
        @guarded_generator(max_depth=16)
        def iter_names(node: object) -> Iterator[str]:
            name = getattr(node, "name", None)
            if name:
                yield name
            for child in getattr(node, "children", ()):
                yield from iter_names(child)

        root = MockNode("root", [MockNode("c1"), MockNode("c2")])
        assert list(iter_names(root)) == ["root", "c1", "c2"]

        # Self-cycle terminates safely
        cyc = MockNode("cyc")
        cyc.children = [cyc]
        assert list(iter_names(cyc)) == ["cyc"]

        # Ring cycle terminates safely
        a = MockNode("a")
        b = MockNode("b")
        a.children = [b]
        b.children = [a]
        assert list(iter_names(a)) == ["a", "b"]

    def test_generator_early_break_cleans_up(self) -> None:
        @guarded_generator(max_depth=16)
        def stream_nodes(node: object) -> Iterator[str]:
            yield getattr(node, "name", "")
            for child in getattr(node, "children", ()):
                yield from stream_nodes(child)

        root = MockNode("root", [MockNode("c1"), MockNode("c2")])
        # Partially iterate and break
        for item in stream_nodes(root):
            assert item == "root"
            break

        # A subsequent run starts fresh without path pollution
        assert list(stream_nodes(root)) == ["root", "c1", "c2"]


class TestAstDescendantsIter:
    def test_iterative_walk_tree(self) -> None:
        c1 = MockNode("c1")
        c2 = MockNode("c2")
        root = MockNode("root", [c1, c2])

        descendants = list(ast_descendants_iter(root))
        assert descendants == [c1, c2]

    def test_iterative_walk_filters_stop_at(self) -> None:
        inner = MockNode("inner")
        blocked = MockNode("blocked", [inner])
        allowed = MockNode("allowed")
        root = MockNode("root", [blocked, allowed])

        descendants = list(
            ast_descendants_iter(root, stop_at=lambda n: getattr(n, "name", None) == "blocked")
        )
        assert blocked in descendants
        assert inner not in descendants
        assert allowed in descendants

    def test_real_pyslang_tree_traversal(self) -> None:
        from src.pkg.parser.parse import parse_text
        from src.pkg.parser.syntax_kinds import ASSIGNMENT_EXPRESSION_KIND

        code = """
        module top;
          logic a, b;
          always_comb begin
            a = 1;
            b = 2;
          end
        endmodule
        """
        tree = parse_text(code)
        descendants = list(ast_descendants_iter(tree.root))
        assert len(descendants) > 0

        # Guarded generator on real tree
        @guarded_generator(max_depth=64)
        def find_assigns(node: object) -> Iterator[object]:
            if getattr(node, "kind", None) == ASSIGNMENT_EXPRESSION_KIND:
                yield node
            try:
                children = iter(node)
            except TypeError:
                children = ()
            for c in children:
                if isinstance(c, SyntaxNode):
                    yield from find_assigns(c)

        assigns = list(find_assigns(tree.root))
        assert len(assigns) == 2


class TestTruncationTelemetry:
    def test_truncation_event_dataclass(self) -> None:
        event = TruncationEvent(
            query_name="test_query",
            file="top.sv",
            line=12,
            col=5,
            depth=16,
            limit=16,
            reason="max_depth",
        )
        assert event.query_name == "test_query"
        assert event.file == "top.sv"
        assert event.line == 12
        assert event.col == 5
        assert event.depth == 16
        assert event.limit == 16
        assert event.reason == "max_depth"

        d = event.to_dict()
        assert d == {
            "query_name": "test_query",
            "file": "top.sv",
            "line": 12,
            "col": 5,
            "depth": 16,
            "limit": 16,
            "reason": "max_depth",
        }

    def test_collect_truncations_records_max_depth(self) -> None:
        @guarded_traversal(max_depth=3, default=False)
        def deep_walk(node: object) -> bool:
            for child in getattr(node, "children", ()):
                deep_walk(child)
            return True

        # Chain 5 levels deep
        n4 = MockNode("n4")
        n3 = MockNode("n3", [n4])
        n2 = MockNode("n2", [n3])
        n1 = MockNode("n1", [n2])
        root = MockNode("root", [n1])

        with collect_truncations() as events:
            deep_walk(root)

        assert len(events) >= 1
        assert any(e.reason == "max_depth" and e.limit == 3 and "deep_walk" in e.query_name for e in events)

    def test_collect_truncations_records_cycle_detected(self) -> None:
        @guarded_traversal(max_depth=16, default=False)
        def cycle_walk(node: object) -> bool:
            for child in getattr(node, "children", ()):
                cycle_walk(child)
            return True

        cyc = MockNode("cyc")
        cyc.children = [cyc]

        with collect_truncations() as events:
            cycle_walk(cyc)

        assert len(events) >= 1
        assert any(e.reason == "cycle_detected" and "cycle_walk" in e.query_name for e in events)

    def test_collect_truncations_generator(self) -> None:
        @guarded_generator(max_depth=2)
        def iter_deep(node: object) -> Iterator[str]:
            yield getattr(node, "name", "")
            for child in getattr(node, "children", ()):
                yield from iter_deep(child)

        n3 = MockNode("n3")
        n2 = MockNode("n2", [n3])
        n1 = MockNode("n1", [n2])
        root = MockNode("root", [n1])

        with collect_truncations() as events:
            list(iter_deep(root))

        assert len(events) >= 1
        assert any(e.reason == "max_depth" and e.limit == 2 for e in events)

    def test_active_path_truncation_recording(self) -> None:
        path = ActivePath(max_depth=2)
        n0 = MockNode("n0")
        n1 = MockNode("n1")
        n2 = MockNode("n2")

        with collect_truncations() as events:
            with path.enter(n0, query_name="test_active_path") as s0:
                assert s0
                p1 = path.next_level()
                with p1.enter(n1, query_name="test_active_path") as s1:
                    assert s1
                    p2 = p1.next_level()
                    with p2.enter(n2, query_name="test_active_path") as s2:
                        assert not s2

        assert len(events) == 1
        assert events[0].reason == "max_depth"
        assert events[0].limit == 2
        assert events[0].query_name == "test_active_path"

        # Cycle rejection
        path_cyc = ActivePath(max_depth=10)
        cnode = MockNode("cnode")
        with collect_truncations() as cyc_events:
            with path_cyc.enter(cnode, query_name="cyc_test") as sc1:
                assert sc1
                with path_cyc.enter(cnode, query_name="cyc_test") as sc2:
                    assert not sc2

        assert len(cyc_events) == 1
        assert cyc_events[0].reason == "cycle_detected"

    def test_ast_descendants_iter_truncation(self) -> None:
        n3 = MockNode("n3")
        n2 = MockNode("n2", [n3])
        n1 = MockNode("n1", [n2])
        root = MockNode("root", [n1])

        with collect_truncations() as events:
            list(ast_descendants_iter(root, max_depth=2))

        assert len(events) >= 1
        assert any(e.reason == "max_depth" and e.query_name == "ast_descendants_iter" for e in events)

    def test_location_extraction_from_vnode_and_pyslang(self) -> None:
        from src.pkg.parser.parse import parse_text

        class MockVNodeWithLocation:
            def __init__(self, loc: dict[str, object]) -> None:
                self.location = loc

        vnode = MockVNodeWithLocation({"file": "module.sv", "line": 42, "col": 7})
        with collect_truncations() as events:
            record_truncation("custom_query", vnode, depth=10, limit=10, reason="max_depth")

        assert len(events) == 1
        assert events[0].file == "module.sv"
        assert events[0].line == 42
        assert events[0].col == 7

        # Pyslang SyntaxNode with active tree
        code = """
        module test_loc;
          logic x;
        endmodule
        """
        tree = parse_text(code)
        node = tree.root.members[0]
        with collect_truncations(file_name="test_loc.sv", tree=tree) as tree_events:
            record_truncation("pyslang_query", node, depth=5, limit=5, reason="max_depth")

        assert len(tree_events) == 1
        assert tree_events[0].file == "test_loc.sv"
        assert tree_events[0].line == 3
        assert tree_events[0].col == 11

    def test_zero_overhead_when_inactive(self) -> None:
        assert get_current_truncations() is None
        # Recording truncation when no sink is active does not raise
        record_truncation("dummy", MockNode("n"), depth=1, limit=1)
        assert get_current_truncations() is None

    def test_cycle_detected_precedence_over_max_depth(self) -> None:
        """Verifies that cycles are decoupled from depth limits and recorded as cycle_detected."""
        @guarded_traversal(max_depth=2, default=False)
        def walk(node: object) -> bool:
            for child in getattr(node, "children", ()):
                walk(child)
            return True

        n0 = MockNode("n0")
        n1 = MockNode("n1", [n0])  # Cycle: n0 -> n1 -> n0
        n0.children = [n1]

        with collect_truncations() as events:
            walk(n0)

        assert any(e.reason == "cycle_detected" for e in events)

