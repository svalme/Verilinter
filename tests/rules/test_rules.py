import pytest
from unittest.mock import Mock
import pyslang as sl

from src.pkg.rules.default_case import DefaultCaseRule
from src.pkg.rules.no_blocking_sequential_logic import NoBlockingAssignmentInSequentialRule
from src.pkg.rules.no_nonblocking_comb import NoNonBlockingAssignmentInCombRule
from src.pkg.ast.context import Context, ContextFlag
from src.pkg.vnodes.base_vnode import BaseVNode


@pytest.fixture
def mock_vnode() -> Mock:
    """Fixture for a mock vnode."""
    mock = Mock(spec=BaseVNode)
    mock.location = {"line": 42, "col": 10}
    return mock


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
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.EndCaseKeyword
        
        context = Context().with_flag(ContextFlag.CASE_GENERATE)
        
        assert rule.applies(mock_vnode, context) is True

    def test_applies_returns_false_without_endcase_keyword(self, rule: DefaultCaseRule) -> None:
        """Test that applies() returns False if vnode is not EndCaseKeyword."""
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.AlwaysKeyword
        
        context = Context().with_flag(ContextFlag.CASE_GENERATE)
        
        assert rule.applies(mock_vnode, context) is False

    def test_applies_returns_false_without_case_generate_flag(self, rule: DefaultCaseRule) -> None:
        """Test that applies() returns False without CASE_GENERATE flag."""
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.EndCaseKeyword
        
        context = Context()
        
        assert rule.applies(mock_vnode, context) is False

    def test_applies_returns_false_with_default_flag(self, rule: DefaultCaseRule) -> None:
        """Test that applies() returns False if DEFAULT flag is set."""
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.EndCaseKeyword
        
        context = Context().with_flag(ContextFlag.CASE_GENERATE).with_flag(ContextFlag.DEFAULT)
        
        assert rule.applies(mock_vnode, context) is False

    def test_report_returns_correct_format(self, rule: DefaultCaseRule, mock_vnode: Mock) -> None:
        """Test that report() returns the correct diagnostic format."""
        result = rule.report(mock_vnode)
        
        assert result["line"] == 42
        assert result["col"] == 10
        assert result["message"] == "Case statement missing default case"


class TestNoBlockingAssignmentInSequentialRule:
    """Test cases for the NoBlockingAssignmentInSequentialRule."""

    @pytest.fixture
    def rule(self) -> NoBlockingAssignmentInSequentialRule:
        """Fixture for NoBlockingAssignmentInSequentialRule instance."""
        return NoBlockingAssignmentInSequentialRule()

    def test_rule_has_correct_code(self, rule: NoBlockingAssignmentInSequentialRule) -> None:
        """Test that NoBlockingAssignmentInSequentialRule has the correct code."""
        assert rule.code == "NO_BLOCKING_SEQUENTIAL"

    def test_rule_has_correct_message(self, rule: NoBlockingAssignmentInSequentialRule) -> None:
        """Test that NoBlockingAssignmentInSequentialRule has the correct message."""
        assert rule.message == "Blocking assignment used in sequential logic"

    def test_applies_returns_true_for_equals_in_always(self, rule: NoBlockingAssignmentInSequentialRule) -> None:
        """Test that applies() returns True for '=' (Equals) inside always block."""
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.Equals
        
        context = Context().with_flag(ContextFlag.ALWAYS)
        
        assert rule.applies(mock_vnode, context) is True

    def test_applies_returns_false_without_equals_token(self, rule: NoBlockingAssignmentInSequentialRule) -> None:
        """Test that applies() returns False if vnode is not Equals token."""
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.LessThanEquals
        
        context = Context().with_flag(ContextFlag.ALWAYS)
        
        assert rule.applies(mock_vnode, context) is False

    def test_applies_returns_false_without_always_flag(self, rule: NoBlockingAssignmentInSequentialRule) -> None:
        """Test that applies() returns False without ALWAYS flag."""
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.Equals
        
        context = Context()
        
        assert rule.applies(mock_vnode, context) is False

    def test_applies_returns_false_in_combinational_logic(self, rule: NoBlockingAssignmentInSequentialRule) -> None:
        """Test that applies() returns False in always_comb."""
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.Equals
        
        context = Context().with_flag(ContextFlag.ALWAYS_COMB)
        
        assert rule.applies(mock_vnode, context) is False

    def test_report_returns_correct_format(self, rule: NoBlockingAssignmentInSequentialRule, mock_vnode: Mock) -> None:
        """Test that report() returns the correct diagnostic format."""
        mock_vnode.location = {"line": 15, "col": 8}
        result = rule.report(mock_vnode)
        
        assert result["line"] == 15
        assert result["col"] == 8
        assert result["message"] == "Blocking assignment used in sequential logic"


class TestNoNonBlockingAssignmentInCombRule:
    """Test cases for the NoNonBlockingAssignmentInCombRule."""

    @pytest.fixture
    def rule(self) -> NoNonBlockingAssignmentInCombRule:
        """Fixture for NoNonBlockingAssignmentInCombRule instance."""
        return NoNonBlockingAssignmentInCombRule()

    def test_rule_has_correct_code(self, rule: NoNonBlockingAssignmentInCombRule) -> None:
        """Test that NoNonBlockingAssignmentInCombRule has the correct code."""
        assert rule.code == "NO_NONBLOCKING_COMBINATIONAL"

    def test_rule_has_correct_message(self, rule: NoNonBlockingAssignmentInCombRule) -> None:
        """Test that NoNonBlockingAssignmentInCombRule has the correct message."""
        assert rule.message == "Non-blocking assignment used in combinational logic"

    def test_applies_returns_true_for_nonblocking_in_always_comb(self, rule: NoNonBlockingAssignmentInCombRule) -> None:
        """Test that applies() returns True for '<=' inside always_comb."""
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.LessThanEquals
        
        context = Context().with_flag(ContextFlag.ALWAYS_COMB)
        
        assert rule.applies(mock_vnode, context) is True

    def test_applies_returns_false_without_lessthanequals_token(self, rule: NoNonBlockingAssignmentInCombRule) -> None:
        """Test that applies() returns False if vnode is not LessThanEquals token."""
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.Equals
        
        context = Context().with_flag(ContextFlag.ALWAYS_COMB)
        
        assert rule.applies(mock_vnode, context) is False

    def test_applies_returns_false_without_always_comb_flag(self, rule: NoNonBlockingAssignmentInCombRule) -> None:
        """Test that applies() returns False without ALWAYS_COMB flag."""
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.LessThanEquals
        
        context = Context()
        
        assert rule.applies(mock_vnode, context) is False

    def test_applies_returns_false_in_sequential_logic(self, rule: NoNonBlockingAssignmentInCombRule) -> None:
        """Test that applies() returns False in always @(posedge)."""
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.LessThanEquals
        
        context = Context().with_flag(ContextFlag.ALWAYS)
        
        assert rule.applies(mock_vnode, context) is False

    def test_report_returns_correct_format(self, rule: NoNonBlockingAssignmentInCombRule, mock_vnode: Mock) -> None:
        """Test that report() returns the correct diagnostic format."""
        mock_vnode.location = {"line": 25, "col": 12}
        result = rule.report(mock_vnode)
        
        assert result["line"] == 25
        assert result["col"] == 12
        assert result["message"] == "Non-blocking assignment used in combinational logic"
