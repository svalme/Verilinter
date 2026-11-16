"""Node rule tests for `conditional_and_case_statements`: one test class per rule."""
import pytest
from src.pkg.parser.parse import parse_file, parse_text
from src.pkg.parser.types import Token
from src.pkg.parser.syntax_kinds import UNIQUE0_TOKEN_KIND, UNIQUE_KEYWORD_TOKEN_KIND, PRIORITY_KEYWORD_TOKEN_KIND, INSIDE_KEYWORD_TOKEN_KIND, IDENTIFIER_TOKEN_KIND, ENDCASE_KEYWORD_TOKEN_KIND, CASE_KEYWORD_TOKEN_KIND, ALWAYS_TOKEN_KIND
from src.pkg.rules.conditional_and_case_statements.default_case import DefaultCaseRule
from src.pkg.rules.conditional_and_case_statements.no_case_inside import NoCaseInsideRule
from src.pkg.rules.conditional_and_case_statements.no_inside_operator import NoInsideOperatorRule
from src.pkg.rules.conditional_and_case_statements.no_full_parallel_case import NoFullParallelCaseRule
from src.pkg.rules.conditional_and_case_statements.no_priority_if import NoPriorityIfRule
from src.pkg.rules.conditional_and_case_statements.no_unique0_case import NoUnique0CaseRule
from src.pkg.rules.conditional_and_case_statements.no_unique_if import NoUniqueIfRule
from src.pkg.rules.conditional_and_case_statements.no_unique_priority_case import NoUniquePriorityCaseRule
from src.pkg.rules.conditional_and_case_statements.no_unique0_if import NoUnique0IfRule
from tests.support.fakes import fake_vnode
from tests.support.parse_diagnostics import assert_no_parse_errors
from tests.support.syntax_context_builders import case_context, case_inside_context, conditional_context, token_vnode
from src.pkg.walk.context import Context, ContextFlag
from src.pkg.vnodes.base_vnode import BaseVNode
from src.pkg.vnodes.token_vnode import TokenVNode
from tests.support.rule_node_helpers import DATA, mock_vnode


class TestDefaultCaseRule:
    """Test cases for the DefaultCaseRule."""

    @pytest.fixture
    def rule(self) -> DefaultCaseRule:
        """Fixture for DefaultCaseRule instance."""
        return DefaultCaseRule()

    def test_rule_has_correct_code(self, rule: DefaultCaseRule) -> None:
        """Test that DefaultCaseRule has the correct code."""
        assert rule.code == "DEFAULT_CASE"

    def test_rule_has_correct_message(self, rule: DefaultCaseRule) -> None:
        """Test that DefaultCaseRule has the correct message."""
        assert rule.message == "Case statement missing default case"

    def test_applies_returns_true_for_endcase_without_default(self, rule: DefaultCaseRule) -> None:
        """Test that applies() returns True for EndCaseKeyword without DEFAULT flag."""
        mock_vnode = fake_vnode(ENDCASE_KEYWORD_TOKEN_KIND)

        context = Context().with_flag(ContextFlag.CASE_GENERATE)

        assert rule.applies(mock_vnode, context) is True

    def test_applies_returns_false_without_endcase_keyword(self, rule: DefaultCaseRule) -> None:
        """Test that applies() returns False if vnode is not EndCaseKeyword."""
        mock_vnode = fake_vnode(ALWAYS_TOKEN_KIND)

        context = Context().with_flag(ContextFlag.CASE_GENERATE)

        assert rule.applies(mock_vnode, context) is False

    def test_applies_returns_false_without_case_generate_flag(self, rule: DefaultCaseRule) -> None:
        """Test that applies() returns False without CASE_GENERATE flag."""
        mock_vnode = fake_vnode(ENDCASE_KEYWORD_TOKEN_KIND)

        context = Context()

        assert rule.applies(mock_vnode, context) is False

    def test_applies_returns_false_with_default_flag(self, rule: DefaultCaseRule) -> None:
        """Test that applies() returns False if DEFAULT flag is set."""
        mock_vnode = fake_vnode(ENDCASE_KEYWORD_TOKEN_KIND)

        context = Context().with_flag(ContextFlag.CASE_GENERATE).with_flag(ContextFlag.DEFAULT)

        assert rule.applies(mock_vnode, context) is False

    def test_report_returns_correct_format(self, rule: DefaultCaseRule, mock_vnode: BaseVNode) -> None:
        """Test that report() returns the correct diagnostic format."""
        result = rule.report(mock_vnode)

        assert result["line"] == 42
        assert result["col"] == 10
        assert result["message"] == "Case statement missing default case"


class TestNoFullParallelCaseRule:
    @pytest.fixture
    def rule(self) -> NoFullParallelCaseRule:
        return NoFullParallelCaseRule()

    def test_rule_has_correct_code(self, rule: NoFullParallelCaseRule) -> None:
        assert rule.code == "NO_FULL_PARALLEL_CASE"

    def test_rule_has_correct_message(self, rule: NoFullParallelCaseRule) -> None:
        assert rule.message == "Use of full_case / parallel_case pragmas can hide real case coverage issues"

    def test_applies_returns_false_for_non_case_token(self, rule: NoFullParallelCaseRule) -> None:
        mock_vnode = fake_vnode(IDENTIFIER_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_true_for_case_with_preceding_pragma_comment(self, rule: NoFullParallelCaseRule) -> None:
        tree = parse_file(str(DATA / "full_parallel_case.v"))

        def walk(node):
            if isinstance(node, Token) and node.kind == CASE_KEYWORD_TOKEN_KIND:
                return node
            if hasattr(node, "__iter__"):
                for child in node:
                    found = walk(child)
                    if found is not None:
                        return found
            return None

        raw_token = walk(tree.root)
        assert raw_token is not None
        vnode = TokenVNode(raw_token, tree)

        assert rule.applies(vnode, Context()) is True

    def test_report_returns_correct_format(self, rule: NoFullParallelCaseRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 9, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 9
        assert result["col"] == 5
        assert result["message"] == "Use of full_case / parallel_case pragmas can hide real case coverage issues"


class TestNoCaseInsideRule:
    @pytest.fixture
    def rule(self) -> NoCaseInsideRule:
        return NoCaseInsideRule()

    def test_rule_has_correct_code(self, rule: NoCaseInsideRule) -> None:
        assert rule.code == "NO_CASE_INSIDE"

    def test_rule_has_correct_message(self, rule: NoCaseInsideRule) -> None:
        assert rule.message == "Use of case inside is discouraged in this RTL subset"

    def test_applies_returns_true_for_case_inside_keyword(self, rule: NoCaseInsideRule) -> None:
        """`case (expr) inside ... endcase` exposes `inside` as the case
        statement's own `matchesOrInside` token (IEEE 1800-2017 SS12.5.4)."""
        mock_vnode = token_vnode(INSIDE_KEYWORD_TOKEN_KIND)
        ctx = case_inside_context(mock_vnode.raw)

        assert rule.applies(mock_vnode, ctx) is True

    def test_applies_returns_false_for_inside_operator(self, rule: NoCaseInsideRule) -> None:
        tree = parse_text(
            """
            module top(input logic [1:0] sel, output logic y);
                always_comb begin
                    case (sel)
                        2'b00: y = (sel inside {2'b00, 2'b01}) ? 1'b1 : 1'b0;
                        default: y = 1'b0;
                    endcase
                end
            endmodule
            """
        )
        assert_no_parse_errors("test_applies_returns_false_for_inside_operator", tree)

        def walk(node):
            if isinstance(node, Token) and node.kind == INSIDE_KEYWORD_TOKEN_KIND:
                return node
            if hasattr(node, "__iter__"):
                for child in node:
                    found = walk(child)
                    if found is not None:
                        return found
            return None

        raw_token = walk(tree.root)
        assert raw_token is not None
        vnode = TokenVNode(raw_token, tree)

        # An ordinary `inside` operator nested in a case item's expression is a
        # different token from the enclosing case statement's own
        # `matchesOrInside` field, even though a CaseStatement ancestor exists.
        ctx = case_inside_context(fake_vnode(None))

        assert rule.applies(vnode, ctx) is False

    def test_report_returns_correct_format(self, rule: NoCaseInsideRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 4, "col": 10}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 10
        assert result["message"] == "Use of case inside is discouraged in this RTL subset"


class TestNoInsideOperatorRule:
    @pytest.fixture
    def rule(self) -> NoInsideOperatorRule:
        return NoInsideOperatorRule()

    def test_rule_has_correct_code(self, rule: NoInsideOperatorRule) -> None:
        assert rule.code == "NO_INSIDE_OPERATOR"

    def test_rule_has_correct_message(self, rule: NoInsideOperatorRule) -> None:
        assert rule.message == "Use of the inside operator is discouraged in this RTL subset"

    def test_applies_returns_true_for_inside_operator(self, rule: NoInsideOperatorRule) -> None:
        tree = parse_file(str(DATA / "inside_operator.v"))

        def walk(node):
            if isinstance(node, Token) and node.kind == INSIDE_KEYWORD_TOKEN_KIND:
                return node
            if hasattr(node, "__iter__"):
                for child in node:
                    found = walk(child)
                    if found is not None:
                        return found
            return None

        raw_token = walk(tree.root)
        assert raw_token is not None
        vnode = TokenVNode(raw_token, tree)

        assert rule.applies(vnode, Context()) is True

    def test_applies_returns_false_for_case_inside_keyword(self, rule: NoInsideOperatorRule) -> None:
        """`case (expr) inside ... endcase` exposes `inside` as the case
        statement's own `matchesOrInside` token, not an ordinary operator use."""
        mock_vnode = token_vnode(INSIDE_KEYWORD_TOKEN_KIND)
        ctx = case_inside_context(mock_vnode.raw)

        assert rule.applies(mock_vnode, ctx) is False

    def test_report_returns_correct_format(self, rule: NoInsideOperatorRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 4, "col": 20}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 20
        assert result["message"] == "Use of the inside operator is discouraged in this RTL subset"


class TestNoUniquePriorityCaseRule:
    @pytest.fixture
    def rule(self) -> NoUniquePriorityCaseRule:
        return NoUniquePriorityCaseRule()

    def test_rule_has_correct_code(self, rule: NoUniquePriorityCaseRule) -> None:
        assert rule.code == "NO_UNIQUE_PRIORITY_CASE"

    def test_rule_has_correct_message(self, rule: NoUniquePriorityCaseRule) -> None:
        assert rule.message == "Use of unique/priority case can overstate case completeness or exclusivity"

    def test_applies_returns_true_for_unique_keyword(self, rule: NoUniquePriorityCaseRule) -> None:
        mock_vnode = token_vnode(UNIQUE_KEYWORD_TOKEN_KIND)
        context = case_context(unique_or_priority="unique")

        assert rule.applies(mock_vnode, context) is True

    def test_applies_returns_true_for_priority_keyword(self, rule: NoUniquePriorityCaseRule) -> None:
        mock_vnode = token_vnode(PRIORITY_KEYWORD_TOKEN_KIND)
        context = case_context(unique_or_priority="priority")

        assert rule.applies(mock_vnode, context) is True

    def test_applies_returns_false_for_plain_case_keyword(self, rule: NoUniquePriorityCaseRule) -> None:
        mock_vnode = token_vnode(CASE_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_false_for_unique_if(self, rule: NoUniquePriorityCaseRule) -> None:
        mock_vnode = token_vnode(UNIQUE_KEYWORD_TOKEN_KIND)
        context = conditional_context(unique_or_priority="unique")

        assert rule.applies(mock_vnode, context) is False

    def test_report_returns_correct_format(self, rule: NoUniquePriorityCaseRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 4, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 5
        assert result["message"] == "Use of unique/priority case can overstate case completeness or exclusivity"


class TestNoUnique0CaseRule:
    @pytest.fixture
    def rule(self) -> NoUnique0CaseRule:
        return NoUnique0CaseRule()

    def test_rule_has_correct_code(self, rule: NoUnique0CaseRule) -> None:
        assert rule.code == "NO_UNIQUE0_CASE"

    def test_rule_has_correct_message(self, rule: NoUnique0CaseRule) -> None:
        assert rule.message == "Use of unique0 case can overstate case coverage assumptions"

    def test_applies_returns_true_for_unique0_keyword(self, rule: NoUnique0CaseRule) -> None:
        mock_vnode = token_vnode(UNIQUE0_TOKEN_KIND)
        context = case_context(unique_or_priority="unique0")

        assert rule.applies(mock_vnode, context) is True

    def test_applies_returns_false_for_unique_keyword(self, rule: NoUnique0CaseRule) -> None:
        mock_vnode = token_vnode(UNIQUE_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoUnique0CaseRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 4, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 5
        assert result["message"] == "Use of unique0 case can overstate case coverage assumptions"


class TestNoUniqueIfRule:
    @pytest.fixture
    def rule(self) -> NoUniqueIfRule:
        return NoUniqueIfRule()

    def test_rule_has_correct_code(self, rule: NoUniqueIfRule) -> None:
        assert rule.code == "NO_UNIQUE_IF"

    def test_rule_has_correct_message(self, rule: NoUniqueIfRule) -> None:
        assert rule.message == "Use of unique if can overstate branch exclusivity assumptions"

    def test_applies_returns_true_for_unique_if(self, rule: NoUniqueIfRule) -> None:
        mock_vnode = token_vnode(UNIQUE_KEYWORD_TOKEN_KIND)
        context = conditional_context(unique_or_priority="unique")

        assert rule.applies(mock_vnode, context) is True

    def test_applies_returns_false_for_unique_case(self, rule: NoUniqueIfRule) -> None:
        mock_vnode = token_vnode(UNIQUE_KEYWORD_TOKEN_KIND)
        context = case_context(unique_or_priority="unique")

        assert rule.applies(mock_vnode, context) is False

    def test_report_returns_correct_format(self, rule: NoUniqueIfRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 5, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 5
        assert result["col"] == 5
        assert result["message"] == "Use of unique if can overstate branch exclusivity assumptions"


class TestNoUnique0IfRule:
    @pytest.fixture
    def rule(self) -> NoUnique0IfRule:
        return NoUnique0IfRule()

    def test_rule_has_correct_code(self, rule: NoUnique0IfRule) -> None:
        assert rule.code == "NO_UNIQUE0_IF"

    def test_rule_has_correct_message(self, rule: NoUnique0IfRule) -> None:
        assert rule.message == "Use of unique0 if can overstate branch exclusivity assumptions"

    def test_applies_returns_true_for_unique0_if(self, rule: NoUnique0IfRule) -> None:
        mock_vnode = token_vnode(UNIQUE0_TOKEN_KIND)
        context = conditional_context(unique_or_priority="unique0")

        assert rule.applies(mock_vnode, context) is True

    def test_applies_returns_false_for_unique0_case(self, rule: NoUnique0IfRule) -> None:
        mock_vnode = token_vnode(UNIQUE0_TOKEN_KIND)
        context = case_context(unique_or_priority="unique0")

        assert rule.applies(mock_vnode, context) is False

    def test_applies_returns_false_for_unique_if(self, rule: NoUnique0IfRule) -> None:
        mock_vnode = token_vnode(UNIQUE_KEYWORD_TOKEN_KIND)
        context = conditional_context(unique_or_priority="unique")

        assert rule.applies(mock_vnode, context) is False

    def test_report_returns_correct_format(self, rule: NoUnique0IfRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 5, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 5
        assert result["col"] == 5
        assert result["message"] == "Use of unique0 if can overstate branch exclusivity assumptions"


class TestNoPriorityIfRule:
    @pytest.fixture
    def rule(self) -> NoPriorityIfRule:
        return NoPriorityIfRule()

    def test_rule_has_correct_code(self, rule: NoPriorityIfRule) -> None:
        assert rule.code == "NO_PRIORITY_IF"

    def test_rule_has_correct_message(self, rule: NoPriorityIfRule) -> None:
        assert rule.message == "Use of priority if can overstate branch ordering assumptions"

    def test_applies_returns_true_for_priority_if(self, rule: NoPriorityIfRule) -> None:
        mock_vnode = token_vnode(PRIORITY_KEYWORD_TOKEN_KIND)
        context = conditional_context(unique_or_priority="priority")

        assert rule.applies(mock_vnode, context) is True

    def test_applies_returns_false_for_priority_case(self, rule: NoPriorityIfRule) -> None:
        mock_vnode = token_vnode(PRIORITY_KEYWORD_TOKEN_KIND)
        context = case_context(unique_or_priority="priority")

        assert rule.applies(mock_vnode, context) is False

    def test_report_returns_correct_format(self, rule: NoPriorityIfRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 6, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 6
        assert result["col"] == 5
        assert result["message"] == "Use of priority if can overstate branch ordering assumptions"
