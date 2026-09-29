from __future__ import annotations

from src.pkg.parser.syntax_kinds import CASE_STATEMENT_KIND, CONDITIONAL_STATEMENT_KIND
from src.pkg.parser.syntax import raw_node_children
from src.pkg.vnodes.base_vnode import BaseVNode
from tests.support.fakes import FakeNode, fake_vnode


def test_unset_field_reads_as_missing_not_truthy() -> None:
    node = FakeNode(CASE_STATEMENT_KIND)
    assert getattr(node, "beginName", None) is None


def test_set_fields_and_parent_links() -> None:
    child = FakeNode(CONDITIONAL_STATEMENT_KIND)
    parent = FakeNode(CASE_STATEMENT_KIND, children=(child,), uniqueOrPriority="unique")
    assert parent.uniqueOrPriority == "unique"
    assert child.parent is parent
    assert list(parent) == [child]


def test_fake_vnode_is_a_real_base_vnode() -> None:
    vnode = fake_vnode(CASE_STATEMENT_KIND)
    assert isinstance(vnode, BaseVNode)
    assert vnode.raw.kind == CASE_STATEMENT_KIND
    assert vnode.location is None


def test_raw_node_children_ignores_non_pyslang_nodes() -> None:
    """Documents the isinstance boundary: fakes are not walked as syntax children."""
    parent = FakeNode(CASE_STATEMENT_KIND, children=(FakeNode(CONDITIONAL_STATEMENT_KIND),))
    assert raw_node_children(parent) == []
