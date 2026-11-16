"""Node rule tests for `latches`: one test class per rule."""
import pytest
from src.pkg.parser.syntax_kinds import ALWAYS_COMB_BLOCK_KIND, ALWAYS_LATCH_BLOCK_KIND
from src.pkg.rules.latches.no_always_latch import NoAlwaysLatchRule
from tests.support.fakes import fake_vnode
from src.pkg.walk.context import Context
from src.pkg.vnodes.base_vnode import BaseVNode
from tests.support.rule_node_helpers import mock_vnode


class TestNoAlwaysLatchRule:
    @pytest.fixture
    def rule(self) -> NoAlwaysLatchRule:
        return NoAlwaysLatchRule()

    def test_rule_has_correct_code(self, rule: NoAlwaysLatchRule) -> None:
        assert rule.code == "NO_ALWAYS_LATCH"

    def test_rule_has_correct_message(self, rule: NoAlwaysLatchRule) -> None:
        assert rule.message == "Use of always_latch can hide unintended latch-oriented design choices"

    def test_applies_returns_true_for_always_latch_block(self, rule: NoAlwaysLatchRule) -> None:
        mock_vnode = fake_vnode(ALWAYS_LATCH_BLOCK_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_procedural_block(self, rule: NoAlwaysLatchRule) -> None:
        mock_vnode = fake_vnode(ALWAYS_COMB_BLOCK_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoAlwaysLatchRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 14, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 14
        assert result["col"] == 3
        assert result["message"] == "Use of always_latch can hide unintended latch-oriented design choices"
