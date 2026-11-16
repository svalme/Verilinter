"""Node rule tests for `parameters_and_generate_logic`: one test class per rule."""
import pytest
from src.pkg.parser.parse import parse_file
from src.pkg.parser.types import CaseGenerateNode, IfGenerateNode, LoopGenerateNode
from src.pkg.parser.syntax_kinds import ALWAYS_COMB_BLOCK_KIND, FOR_LOOP_STATEMENT_KIND, CONDITIONAL_STATEMENT_KIND, DEFPARAM_KEYWORD_TOKEN_KIND, PARAMETER_KEYWORD_TOKEN_KIND
from src.pkg.rules.parameters_and_generate_logic.no_case_generate import NoCaseGenerateRule
from src.pkg.rules.parameters_and_generate_logic.no_generate_for import NoGenerateForRule
from src.pkg.rules.parameters_and_generate_logic.no_if_generate import NoIfGenerateRule
from src.pkg.rules.parameters_and_generate_logic.no_defparam import NoDefparamRule
from tests.support.fakes import FakeVNode, fake_vnode
from src.pkg.walk.context import Context
from src.pkg.vnodes.base_vnode import BaseVNode
from tests.support.rule_node_helpers import DATA, mock_vnode


class TestNoCaseGenerateRule:
    @pytest.fixture
    def rule(self) -> NoCaseGenerateRule:
        return NoCaseGenerateRule()

    def test_rule_has_correct_code(self, rule: NoCaseGenerateRule) -> None:
        assert rule.code == "NO_CASE_GENERATE"

    def test_rule_has_correct_message(self, rule: NoCaseGenerateRule) -> None:
        assert rule.message == "Use of case generate can make structural intent harder to follow"

    def test_applies_returns_true_for_case_generate_node(self, rule: NoCaseGenerateRule) -> None:
        tree = parse_file(str(DATA / "case_generate.v"))

        def walk(node):
            if isinstance(node, CaseGenerateNode):
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

    def test_applies_returns_false_for_other_syntax_node(self, rule: NoCaseGenerateRule) -> None:
        mock_vnode = fake_vnode(ALWAYS_COMB_BLOCK_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoCaseGenerateRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 3, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 5
        assert result["message"] == "Use of case generate can make structural intent harder to follow"


class TestNoGenerateForRule:
    @pytest.fixture
    def rule(self) -> NoGenerateForRule:
        return NoGenerateForRule()

    def test_rule_has_correct_code(self, rule: NoGenerateForRule) -> None:
        assert rule.code == "NO_GENERATE_FOR"

    def test_rule_has_correct_message(self, rule: NoGenerateForRule) -> None:
        assert rule.message == "Use of generate-for loops can make structural intent harder to follow"

    def test_applies_returns_true_for_loop_generate_node(self, rule: NoGenerateForRule) -> None:
        tree = parse_file(str(DATA / "generate_for.v"))

        def walk(node):
            if isinstance(node, LoopGenerateNode):
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

    def test_applies_returns_false_for_procedural_for_statement(self, rule: NoGenerateForRule) -> None:
        mock_vnode = fake_vnode(FOR_LOOP_STATEMENT_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoGenerateForRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 4, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 5
        assert result["message"] == "Use of generate-for loops can make structural intent harder to follow"


class TestNoIfGenerateRule:
    @pytest.fixture
    def rule(self) -> NoIfGenerateRule:
        return NoIfGenerateRule()

    def test_rule_has_correct_code(self, rule: NoIfGenerateRule) -> None:
        assert rule.code == "NO_IF_GENERATE"

    def test_rule_has_correct_message(self, rule: NoIfGenerateRule) -> None:
        assert rule.message == "Use of if-generate can make structural intent harder to follow"

    def test_applies_returns_true_for_if_generate_node(self, rule: NoIfGenerateRule) -> None:
        tree = parse_file(str(DATA / "if_generate.v"))

        def walk(node):
            if isinstance(node, IfGenerateNode):
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

    def test_applies_returns_false_for_procedural_if_statement(self, rule: NoIfGenerateRule) -> None:
        mock_vnode = fake_vnode(CONDITIONAL_STATEMENT_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoIfGenerateRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 4, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 5
        assert result["message"] == "Use of if-generate can make structural intent harder to follow"


class TestNoDefparamRule:
    @pytest.fixture
    def rule(self) -> NoDefparamRule:
        return NoDefparamRule()

    def test_rule_has_correct_code(self, rule: NoDefparamRule) -> None:
        assert rule.code == "NO_DEFPARAM"

    def test_rule_has_correct_message(self, rule: NoDefparamRule) -> None:
        assert rule.message == "Use of defparam is discouraged; prefer explicit parameter overrides at instantiation"

    def test_applies_returns_true_for_defparam_token(self, rule: NoDefparamRule) -> None:
        mock_vnode = fake_vnode(DEFPARAM_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_token(self, rule: NoDefparamRule) -> None:
        mock_vnode = fake_vnode(PARAMETER_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoDefparamRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 6, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 6
        assert result["col"] == 5
        assert result["message"] == "Use of defparam is discouraged; prefer explicit parameter overrides at instantiation"
