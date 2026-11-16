"""Node rule tests for `arrays_and_indexing`: one test class per rule."""
import pytest
from src.pkg.parser.parse import parse_text
from src.pkg.parser.syntax_kinds import QUEUE_DIMENSION_SPECIFIER_KIND, RANGE_DIMENSION_SPECIFIER_KIND, VARIABLE_DIMENSION_KIND, WILDCARD_DIMENSION_SPECIFIER_KIND
from src.pkg.rules.arrays_and_indexing.no_queue import NoQueueRule
from src.pkg.rules.arrays_and_indexing.no_dynamic_array import NoDynamicArrayRule
from src.pkg.rules.arrays_and_indexing.no_associative_array import NoAssociativeArrayRule
from tests.support.fakes import FakeVNode, fake_vnode
from tests.support.parse_diagnostics import assert_no_parse_errors
from src.pkg.walk.context import Context
from src.pkg.vnodes.base_vnode import BaseVNode
from tests.support.rule_node_helpers import mock_vnode


def _find_first_node_of_kind(src: str, kind: object) -> object:
    tree = parse_text(src)
    assert_no_parse_errors(src, tree)
    found: object = None

    def walk(node: object) -> None:
        nonlocal found
        if found is None and getattr(node, "kind", None) == kind:
            found = node
        if hasattr(node, "__iter__"):
            for child in node:
                walk(child)

    walk(tree.root)
    return found


class TestNoQueueRule:
    @pytest.fixture
    def rule(self) -> NoQueueRule:
        return NoQueueRule()

    def test_rule_has_correct_code(self, rule: NoQueueRule) -> None:
        assert rule.code == "NO_QUEUE"

    def test_rule_has_correct_message(self, rule: NoQueueRule) -> None:
        assert rule.message == "Use of queue declarations (arr[$]) is discouraged in synthesizable RTL; queues are a dynamic, software-oriented SystemVerilog construct"

    def test_applies_returns_true_for_queue_dimension_node(self, rule: NoQueueRule) -> None:
        mock_vnode = fake_vnode(QUEUE_DIMENSION_SPECIFIER_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoQueueRule) -> None:
        mock_vnode = fake_vnode(WILDCARD_DIMENSION_SPECIFIER_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoQueueRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of queue declarations (arr[$]) is discouraged in synthesizable RTL; queues are a dynamic, software-oriented SystemVerilog construct"


class TestNoDynamicArrayRule:
    @pytest.fixture
    def rule(self) -> NoDynamicArrayRule:
        return NoDynamicArrayRule()

    def test_rule_has_correct_code(self, rule: NoDynamicArrayRule) -> None:
        assert rule.code == "NO_DYNAMIC_ARRAY"

    def test_rule_has_correct_message(self, rule: NoDynamicArrayRule) -> None:
        assert rule.message == "Use of dynamic array declarations (arr[]) is discouraged in synthesizable RTL; dynamic arrays are a software-oriented SystemVerilog construct"

    def test_applies_returns_true_for_bare_brackets(self, rule: NoDynamicArrayRule) -> None:
        raw_node = _find_first_node_of_kind("module top; int arr[]; endmodule", VARIABLE_DIMENSION_KIND)
        assert raw_node is not None

        mock_vnode = FakeVNode(raw_node)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_fixed_size_dimension(self, rule: NoDynamicArrayRule) -> None:
        """`arr[4]` has a real `specifier` (a BitSelect around the size literal), so
        it must not be mistaken for a dynamic array's bare `[]`."""
        raw_node = _find_first_node_of_kind("module top; int arr[4]; endmodule", VARIABLE_DIMENSION_KIND)
        assert raw_node is not None

        mock_vnode = FakeVNode(raw_node)

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_false_for_queue_dimension(self, rule: NoDynamicArrayRule) -> None:
        raw_node = _find_first_node_of_kind("module top; int arr[$]; endmodule", VARIABLE_DIMENSION_KIND)
        assert raw_node is not None

        mock_vnode = FakeVNode(raw_node)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoDynamicArrayRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of dynamic array declarations (arr[]) is discouraged in synthesizable RTL; dynamic arrays are a software-oriented SystemVerilog construct"


class TestNoAssociativeArrayRule:
    @pytest.fixture
    def rule(self) -> NoAssociativeArrayRule:
        return NoAssociativeArrayRule()

    def test_rule_has_correct_code(self, rule: NoAssociativeArrayRule) -> None:
        assert rule.code == "NO_ASSOCIATIVE_ARRAY"

    def test_rule_has_correct_message(self, rule: NoAssociativeArrayRule) -> None:
        assert rule.message == "Use of associative array declarations (arr[*], arr[string], arr[int], etc.) is discouraged in synthesizable RTL; associative arrays are a software-oriented SystemVerilog construct"

    def test_applies_returns_true_for_wildcard_index(self, rule: NoAssociativeArrayRule) -> None:
        mock_vnode = fake_vnode(WILDCARD_DIMENSION_SPECIFIER_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_string_index(self, rule: NoAssociativeArrayRule) -> None:
        raw_node = _find_first_node_of_kind("module top; int aa[string]; endmodule", RANGE_DIMENSION_SPECIFIER_KIND)
        assert raw_node is not None

        mock_vnode = FakeVNode(raw_node)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_int_index(self, rule: NoAssociativeArrayRule) -> None:
        raw_node = _find_first_node_of_kind("module top; int aa[int]; endmodule", RANGE_DIMENSION_SPECIFIER_KIND)
        assert raw_node is not None

        mock_vnode = FakeVNode(raw_node)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_identifier_index(self, rule: NoAssociativeArrayRule) -> None:
        """`arr[WIDTH]` is an ordinary parameter-sized fixed array -- syntactically
        indistinguishable from a user-defined-type associative-array index without
        symbol resolution, so it must not be guessed at."""
        raw_node = _find_first_node_of_kind(
            "module top; parameter WIDTH = 4; int arr[WIDTH]; endmodule", RANGE_DIMENSION_SPECIFIER_KIND
        )
        assert raw_node is not None

        mock_vnode = FakeVNode(raw_node)

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_false_for_fixed_range(self, rule: NoAssociativeArrayRule) -> None:
        raw_node = _find_first_node_of_kind("module top; int arr[3:0]; endmodule", RANGE_DIMENSION_SPECIFIER_KIND)
        assert raw_node is not None

        mock_vnode = FakeVNode(raw_node)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoAssociativeArrayRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of associative array declarations (arr[*], arr[string], arr[int], etc.) is discouraged in synthesizable RTL; associative arrays are a software-oriented SystemVerilog construct"
