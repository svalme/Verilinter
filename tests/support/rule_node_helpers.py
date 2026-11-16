"""Helpers shared by the node-rule tests."""

import pytest
from src.pkg.parser.parse import parse_text
from src.pkg.parser.types import SystemNameNode, Token
from src.pkg.parser.syntax_kinds import ALWAYS_BLOCK_KIND
from pathlib import Path
from tests.support.fakes import FakeVNode, fake_vnode
from tests.support.parse_diagnostics import assert_no_parse_errors
from src.pkg.vnodes.base_vnode import BaseVNode


DATA = Path(__file__).parent.parent / "data"


@pytest.fixture
def mock_vnode() -> BaseVNode:
    """Fixture for a mock vnode."""
    node = fake_vnode(None)
    node.location = {"line": 42, "col": 10}
    return node


def _always_block_and_token(src: str, token_kind: object) -> tuple[object, object]:
    """Parse `src` and return (first AlwaysBlock raw node, first raw token of `token_kind`)."""
    tree = parse_text(src)
    assert_no_parse_errors(src, tree)
    block: object = None
    token: object = None

    def walk(node: object) -> None:
        nonlocal block, token
        if block is None and getattr(node, "kind", None) == ALWAYS_BLOCK_KIND:
            block = node
        if token is None and isinstance(node, Token) and node.kind == token_kind:
            token = node
        if hasattr(node, "__iter__"):
            for child in node:
                walk(child)

    walk(tree.root)
    return block, token


def _system_name_vnode(name: str) -> BaseVNode:
    tree = parse_text(f"module top; initial {name}(); endmodule")

    def walk(node):
        if isinstance(node, SystemNameNode):
            return node
        if hasattr(node, "__iter__"):
            for child in node:
                found = walk(child)
                if found is not None:
                    return found
        return None

    raw_node = walk(tree.root)
    assert raw_node is not None
    return FakeVNode(raw_node)
