"""Node rule tests for `assertions_and_verification`: one test class per rule."""
import pytest
from src.pkg.parser.syntax_kinds import CLOCKING_DECLARATION_KIND, CHECKER_DECLARATION_KIND, ASSERT_PROPERTY_STATEMENT_KIND, CLASS_DECLARATION_KIND, COVERGROUP_DECLARATION_KIND, COVER_PROPERTY_STATEMENT_KIND, EXPECT_PROPERTY_STATEMENT_KIND, FOREVER_STATEMENT_KIND, IMMEDIATE_ASSERT_STATEMENT_KIND, IMMEDIATE_COVER_STATEMENT_KIND, PROGRAM_DECLARATION_KIND, PROPERTY_DECLARATION_KIND, RAND_SEQUENCE_STATEMENT_KIND, RESTRICT_PROPERTY_STATEMENT_KIND, SEQUENCE_DECLARATION_KIND
from src.pkg.rules.assertions_and_verification.no_checker_declaration import NoCheckerDeclarationRule
from src.pkg.rules.assertions_and_verification.no_immediate_assertion import NoImmediateAssertionRule
from src.pkg.rules.assertions_and_verification.no_concurrent_assertion import NoConcurrentAssertionRule
from src.pkg.rules.assertions_and_verification.no_covergroup_declaration import NoCovergroupDeclarationRule
from src.pkg.rules.assertions_and_verification.no_sequence_declaration import NoSequenceDeclarationRule
from src.pkg.rules.assertions_and_verification.no_property_declaration import NoPropertyDeclarationRule
from src.pkg.rules.assertions_and_verification.no_randsequence import NoRandsequenceRule
from src.pkg.rules.assertions_and_verification.no_expect_restrict_property import NoExpectRestrictPropertyRule
from src.pkg.rules.assertions_and_verification.no_assertion_control_task import NoAssertionControlTaskRule
from tests.support.fakes import fake_vnode
from src.pkg.walk.context import Context
from src.pkg.vnodes.base_vnode import BaseVNode
from tests.support.rule_node_helpers import _system_name_vnode, mock_vnode


class TestNoCheckerDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoCheckerDeclarationRule:
        return NoCheckerDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoCheckerDeclarationRule) -> None:
        assert rule.code == "NO_CHECKER_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoCheckerDeclarationRule) -> None:
        assert rule.message == "Use of checker declarations is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_checker_declaration_node(self, rule: NoCheckerDeclarationRule) -> None:
        mock_vnode = fake_vnode(CHECKER_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_clocking_declaration_node(self, rule: NoCheckerDeclarationRule) -> None:
        mock_vnode = fake_vnode(CLOCKING_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoCheckerDeclarationRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of checker declarations is discouraged in synthesizable RTL"


class TestNoImmediateAssertionRule:
    @pytest.fixture
    def rule(self) -> NoImmediateAssertionRule:
        return NoImmediateAssertionRule()

    def test_rule_has_correct_code(self, rule: NoImmediateAssertionRule) -> None:
        assert rule.code == "NO_IMMEDIATE_ASSERTION"

    def test_rule_has_correct_message(self, rule: NoImmediateAssertionRule) -> None:
        assert rule.message == "Use of immediate assertions (assert/assume/cover) is discouraged in synthesizable RTL; assertions belong in verification, not design"

    def test_applies_returns_true_for_immediate_assert_statement(self, rule: NoImmediateAssertionRule) -> None:
        mock_vnode = fake_vnode(IMMEDIATE_ASSERT_STATEMENT_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_immediate_cover_statement(self, rule: NoImmediateAssertionRule) -> None:
        mock_vnode = fake_vnode(IMMEDIATE_COVER_STATEMENT_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_concurrent_assertion(self, rule: NoImmediateAssertionRule) -> None:
        mock_vnode = fake_vnode(ASSERT_PROPERTY_STATEMENT_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoImmediateAssertionRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 3, "col": 9}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 9
        assert result["message"] == "Use of immediate assertions (assert/assume/cover) is discouraged in synthesizable RTL; assertions belong in verification, not design"


class TestNoConcurrentAssertionRule:
    @pytest.fixture
    def rule(self) -> NoConcurrentAssertionRule:
        return NoConcurrentAssertionRule()

    def test_rule_has_correct_code(self, rule: NoConcurrentAssertionRule) -> None:
        assert rule.code == "NO_CONCURRENT_ASSERTION"

    def test_rule_has_correct_message(self, rule: NoConcurrentAssertionRule) -> None:
        assert rule.message == "Use of concurrent assertions (assert/assume/cover property) is discouraged in synthesizable RTL; assertions belong in verification, not design"

    def test_applies_returns_true_for_assert_property_statement(self, rule: NoConcurrentAssertionRule) -> None:
        mock_vnode = fake_vnode(ASSERT_PROPERTY_STATEMENT_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_cover_property_statement(self, rule: NoConcurrentAssertionRule) -> None:
        mock_vnode = fake_vnode(COVER_PROPERTY_STATEMENT_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_immediate_assertion(self, rule: NoConcurrentAssertionRule) -> None:
        mock_vnode = fake_vnode(IMMEDIATE_ASSERT_STATEMENT_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoConcurrentAssertionRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 2, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 5
        assert result["message"] == "Use of concurrent assertions (assert/assume/cover property) is discouraged in synthesizable RTL; assertions belong in verification, not design"


class TestNoCovergroupDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoCovergroupDeclarationRule:
        return NoCovergroupDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoCovergroupDeclarationRule) -> None:
        assert rule.code == "NO_COVERGROUP_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoCovergroupDeclarationRule) -> None:
        assert rule.message == "Use of covergroup declarations is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_covergroup_declaration_node(self, rule: NoCovergroupDeclarationRule) -> None:
        mock_vnode = fake_vnode(COVERGROUP_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoCovergroupDeclarationRule) -> None:
        mock_vnode = fake_vnode(CLASS_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoCovergroupDeclarationRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of covergroup declarations is discouraged in synthesizable RTL"


class TestNoSequenceDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoSequenceDeclarationRule:
        return NoSequenceDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoSequenceDeclarationRule) -> None:
        assert rule.code == "NO_SEQUENCE_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoSequenceDeclarationRule) -> None:
        assert rule.message == "Use of sequence declarations is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_sequence_declaration_node(self, rule: NoSequenceDeclarationRule) -> None:
        mock_vnode = fake_vnode(SEQUENCE_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_property_declaration_node(self, rule: NoSequenceDeclarationRule) -> None:
        mock_vnode = fake_vnode(PROPERTY_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoSequenceDeclarationRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of sequence declarations is discouraged in synthesizable RTL"


class TestNoPropertyDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoPropertyDeclarationRule:
        return NoPropertyDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoPropertyDeclarationRule) -> None:
        assert rule.code == "NO_PROPERTY_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoPropertyDeclarationRule) -> None:
        assert rule.message == "Use of property declarations is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_property_declaration_node(self, rule: NoPropertyDeclarationRule) -> None:
        mock_vnode = fake_vnode(PROPERTY_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_sequence_declaration_node(self, rule: NoPropertyDeclarationRule) -> None:
        mock_vnode = fake_vnode(SEQUENCE_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_false_for_assert_property_statement(self, rule: NoPropertyDeclarationRule) -> None:
        mock_vnode = fake_vnode(ASSERT_PROPERTY_STATEMENT_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoPropertyDeclarationRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of property declarations is discouraged in synthesizable RTL"


class TestNoRandsequenceRule:
    @pytest.fixture
    def rule(self) -> NoRandsequenceRule:
        return NoRandsequenceRule()

    def test_rule_has_correct_code(self, rule: NoRandsequenceRule) -> None:
        assert rule.code == "NO_RANDSEQUENCE"

    def test_rule_has_correct_message(self, rule: NoRandsequenceRule) -> None:
        assert rule.message == "Use of randsequence blocks is discouraged in synthesizable RTL; randsequence is a verification-oriented control construct"

    def test_applies_returns_true_for_randsequence_statement_node(self, rule: NoRandsequenceRule) -> None:
        mock_vnode = fake_vnode(RAND_SEQUENCE_STATEMENT_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoRandsequenceRule) -> None:
        mock_vnode = fake_vnode(FOREVER_STATEMENT_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoRandsequenceRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of randsequence blocks is discouraged in synthesizable RTL; randsequence is a verification-oriented control construct"


class TestNoExpectRestrictPropertyRule:
    @pytest.fixture
    def rule(self) -> NoExpectRestrictPropertyRule:
        return NoExpectRestrictPropertyRule()

    def test_rule_has_correct_code(self, rule: NoExpectRestrictPropertyRule) -> None:
        assert rule.code == "NO_EXPECT_RESTRICT_PROPERTY"

    def test_rule_has_correct_message(self, rule: NoExpectRestrictPropertyRule) -> None:
        assert rule.message == "Use of expect/restrict property statements is discouraged in synthesizable RTL; assertions belong in verification, not design"

    def test_applies_returns_true_for_expect_property_statement(self, rule: NoExpectRestrictPropertyRule) -> None:
        mock_vnode = fake_vnode(EXPECT_PROPERTY_STATEMENT_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_restrict_property_statement(self, rule: NoExpectRestrictPropertyRule) -> None:
        mock_vnode = fake_vnode(RESTRICT_PROPERTY_STATEMENT_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_assert_property_statement(self, rule: NoExpectRestrictPropertyRule) -> None:
        mock_vnode = fake_vnode(ASSERT_PROPERTY_STATEMENT_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoExpectRestrictPropertyRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of expect/restrict property statements is discouraged in synthesizable RTL; assertions belong in verification, not design"


class TestNoAssertionControlTaskRule:
    @pytest.fixture
    def rule(self) -> NoAssertionControlTaskRule:
        return NoAssertionControlTaskRule()

    def test_rule_has_correct_code(self, rule: NoAssertionControlTaskRule) -> None:
        assert rule.code == "NO_ASSERTION_CONTROL_TASK"

    def test_rule_has_correct_message(self, rule: NoAssertionControlTaskRule) -> None:
        assert rule.message == "Use of $assertoff/$asserton/$assertkill-family assertion-control system tasks is discouraged in synthesizable RTL; these are simulation-only verification controls"

    def test_applies_returns_true_for_assertoff(self, rule: NoAssertionControlTaskRule) -> None:
        assert rule.applies(_system_name_vnode("$assertoff"), Context()) is True

    def test_applies_returns_true_for_assertkill(self, rule: NoAssertionControlTaskRule) -> None:
        assert rule.applies(_system_name_vnode("$assertkill"), Context()) is True

    def test_applies_returns_false_for_unrelated_system_task(self, rule: NoAssertionControlTaskRule) -> None:
        assert rule.applies(_system_name_vnode("$display"), Context()) is False

    def test_applies_returns_false_for_non_system_name_node(self, rule: NoAssertionControlTaskRule) -> None:
        mock_vnode = fake_vnode(PROGRAM_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoAssertionControlTaskRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 4, "col": 9}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 9
        assert result["message"] == "Use of $assertoff/$asserton/$assertkill-family assertion-control system tasks is discouraged in synthesizable RTL; these are simulation-only verification controls"
