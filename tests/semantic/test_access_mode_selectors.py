from __future__ import annotations

import pytest

from src.pkg.parser.parse import parse_text
from src.pkg.parser.types import SyntaxNode
from src.pkg.parser._syntax_queries.access import _identifier_access_modes_over_ancestors


def _get_access_modes(code: str, target_name: str) -> tuple[bool, bool]:
    tree = parse_text(f"module t; initial begin {code} end endmodule")

    def _traverse(node: object):
        yield node
        if isinstance(node, SyntaxNode):
            for child in node:
                if isinstance(child, SyntaxNode):
                    yield from _traverse(child)

    target = None
    for n in _traverse(tree.root):
        if getattr(getattr(n, "identifier", None), "valueText", None) == target_name or getattr(getattr(n, "name", None), "valueText", None) == target_name:
            # Skip the module header / declaration identifiers
            if "Declaration" not in str(getattr(getattr(n, "parent", None), "kind", "")):
                target = n
                break

    assert target is not None, f"Could not find target identifier '{target_name}' in code: {code}"

    ancestors: list[object] = []
    curr = target
    while curr is not None:
        ancestors.append(curr)
        curr = getattr(curr, "parent", None)

    return _identifier_access_modes_over_ancestors(list(reversed(ancestors)), target)


class TestAccessModeSelectors:
    def test_simple_assignment(self) -> None:
        read, write = _get_access_modes("a = b;", "a")
        assert not read and write

        read, write = _get_access_modes("a = b;", "b")
        assert read and not write

    def test_nonblocking_assignment(self) -> None:
        read, write = _get_access_modes("a <= b;", "a")
        assert not read and write

        read, write = _get_access_modes("a <= b;", "b")
        assert read and not write

    def test_element_select_on_lhs(self) -> None:
        read, write = _get_access_modes("mem[idx] <= data;", "mem")
        assert not read and write

        read, write = _get_access_modes("mem[idx] <= data;", "idx")
        assert read and not write

        read, write = _get_access_modes("mem[idx] <= data;", "data")
        assert read and not write

    def test_parenthesized_element_select_on_lhs(self) -> None:
        read, write = _get_access_modes("(mem)[idx] <= data;", "mem")
        assert not read and write

        read, write = _get_access_modes("(mem)[idx] <= data;", "idx")
        assert read and not write

    def test_multidimensional_select_on_lhs(self) -> None:
        read, write = _get_access_modes("matrix[row][col] <= val;", "matrix")
        assert not read and write

        read, write = _get_access_modes("matrix[row][col] <= val;", "row")
        assert read and not write

        read, write = _get_access_modes("matrix[row][col] <= val;", "col")
        assert read and not write

        read, write = _get_access_modes("matrix[row][col] <= val;", "val")
        assert read and not write

    def test_range_select_on_lhs(self) -> None:
        read, write = _get_access_modes("bus[msb:lsb] <= in_val;", "bus")
        assert not read and write

        read, write = _get_access_modes("bus[msb:lsb] <= in_val;", "msb")
        assert read and not write

        read, write = _get_access_modes("bus[msb:lsb] <= in_val;", "lsb")
        assert read and not write

    def test_indexed_part_select_on_lhs(self) -> None:
        read, write = _get_access_modes("bus[base+:4] <= in_val;", "bus")
        assert not read and write

        read, write = _get_access_modes("bus[base+:4] <= in_val;", "base")
        assert read and not write

    def test_member_and_scoped_select_on_lhs(self) -> None:
        read, write = _get_access_modes("arr[i].b[j] <= 1;", "arr")
        assert not read and write

        read, write = _get_access_modes("arr[i].b[j] <= 1;", "i")
        assert read and not write

        read, write = _get_access_modes("arr[i].b[j] <= 1;", "b")
        assert not read and write

        read, write = _get_access_modes("arr[i].b[j] <= 1;", "j")
        assert read and not write

    def test_concatenation_lhs(self) -> None:
        read, write = _get_access_modes("{a[i], b} <= 2'b0;", "a")
        assert not read and write

        read, write = _get_access_modes("{a[i], b} <= 2'b0;", "i")
        assert read and not write

        read, write = _get_access_modes("{a[i], b} <= 2'b0;", "b")
        assert not read and write

    def test_complex_expression_in_select(self) -> None:
        read, write = _get_access_modes("mem[base + offset * 4] <= val;", "mem")
        assert not read and write

        read, write = _get_access_modes("mem[base + offset * 4] <= val;", "base")
        assert read and not write

        read, write = _get_access_modes("mem[base + offset * 4] <= val;", "offset")
        assert read and not write

    def test_read_modify_write_assignment(self) -> None:
        read, write = _get_access_modes("mem[idx] += 1;", "mem")
        assert read and write

        read, write = _get_access_modes("mem[idx] += 1;", "idx")
        assert read and not write
