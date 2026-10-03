"""Unit tests for the TraversalGuard and ActivePath architecture subsystem."""
from __future__ import annotations

from typing import Iterator
from unittest.mock import Mock

import pytest

from src.pkg.parser.traversal_guard import (
    ActivePath,
    ast_descendants_iter,
    guarded_generator,
    guarded_traversal,
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
