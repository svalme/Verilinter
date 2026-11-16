"""Node rule tests for `connectivity_and_hierarchy`: one test class per rule."""
import pytest
from src.pkg.parser.parse import parse_file, parse_text
from src.pkg.parser.types import ImplicitAnsiPortNode, PortDeclarationNode
from src.pkg.parser.syntax_kinds import BIND_DIRECTIVE_KIND, NET_ALIAS_KIND
from src.pkg.rules.connectivity_and_hierarchy.drivers.no_inout_internal import NoInternalInoutRule
from src.pkg.rules.connectivity_and_hierarchy.no_alias_statement import NoAliasStatementRule
from src.pkg.rules.connectivity_and_hierarchy.no_bind_directive import NoBindDirectiveRule
from tests.support.fakes import FakeVNode, fake_vnode
from tests.support.parse_diagnostics import assert_no_parse_errors
from src.pkg.walk.context import Context
from src.pkg.vnodes.base_vnode import BaseVNode
from tests.support.rule_node_helpers import DATA, mock_vnode


class TestNoInternalInoutRule:
    @pytest.fixture
    def rule(self) -> NoInternalInoutRule:
        return NoInternalInoutRule()

    def test_rule_has_correct_code(self, rule: NoInternalInoutRule) -> None:
        assert rule.code == "NO_INOUT_INTERNAL"

    def test_rule_has_correct_message(self, rule: NoInternalInoutRule) -> None:
        assert rule.message == "Internal inout declarations are not allowed"

    def test_applies_returns_true_for_internal_inout_port_declaration(self, rule: NoInternalInoutRule) -> None:
        tree = parse_file(str(DATA / "internal_inout.v"))

        def walk(node):
            if isinstance(node, PortDeclarationNode):
                return node
            if hasattr(node, "__iter__"):
                for child in node:
                    found = walk(child)
                    if found is not None:
                        return found
            return None

        raw_node = walk(tree.root)
        assert raw_node is not None

        mock_vnode = FakeVNode(raw_node)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_ansi_inout_module_port(self, rule: NoInternalInoutRule) -> None:
        tree = parse_text("module top(inout wire io); endmodule")
        assert_no_parse_errors("test_applies_returns_false_for_ansi_inout_module_port", tree)

        def walk(node):
            if isinstance(node, ImplicitAnsiPortNode):
                return node
            if hasattr(node, "__iter__"):
                for child in node:
                    found = walk(child)
                    if found is not None:
                        return found
            return None

        raw_node = walk(tree.root)
        assert raw_node is not None

        mock_vnode = FakeVNode(raw_node)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoInternalInoutRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 3, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 3
        assert result["message"] == "Internal inout declarations are not allowed"


class TestNoAliasStatementRule:
    @pytest.fixture
    def rule(self) -> NoAliasStatementRule:
        return NoAliasStatementRule()

    def test_rule_has_correct_code(self, rule: NoAliasStatementRule) -> None:
        assert rule.code == "NO_ALIAS_STATEMENT"

    def test_rule_has_correct_message(self, rule: NoAliasStatementRule) -> None:
        assert rule.message == "Use of alias statements is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_net_alias_node(self, rule: NoAliasStatementRule) -> None:
        mock_vnode = fake_vnode(NET_ALIAS_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoAliasStatementRule) -> None:
        mock_vnode = fake_vnode(BIND_DIRECTIVE_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoAliasStatementRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 3, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 5
        assert result["message"] == "Use of alias statements is discouraged in synthesizable RTL"


class TestNoBindDirectiveRule:
    @pytest.fixture
    def rule(self) -> NoBindDirectiveRule:
        return NoBindDirectiveRule()

    def test_rule_has_correct_code(self, rule: NoBindDirectiveRule) -> None:
        assert rule.code == "NO_BIND_DIRECTIVE"

    def test_rule_has_correct_message(self, rule: NoBindDirectiveRule) -> None:
        assert rule.message == "Use of bind directives is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_bind_directive_node(self, rule: NoBindDirectiveRule) -> None:
        mock_vnode = fake_vnode(BIND_DIRECTIVE_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoBindDirectiveRule) -> None:
        mock_vnode = fake_vnode(NET_ALIAS_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoBindDirectiveRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 5, "col": 1}
        result = rule.report(mock_vnode)

        assert result["line"] == 5
        assert result["col"] == 1
        assert result["message"] == "Use of bind directives is discouraged in synthesizable RTL"
