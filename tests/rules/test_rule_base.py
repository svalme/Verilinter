from typing import Any
import pytest
from unittest.mock import Mock

from src.pkg.rules.base_rule import Rule
from src.pkg.vnodes.base_vnode import BaseVNode


@pytest.fixture
def rule() -> Rule:
    """Fixture for a base Rule instance."""
    return Rule()


@pytest.fixture
def mock_vnode() -> Mock:
    """Fixture for a mock vnode."""
    mock = Mock(spec=BaseVNode)
    mock.location = {"line": 10, "col": 5}
    return mock


@pytest.fixture
def mock_ctx() -> Mock:
    """Fixture for a mock context."""
    return Mock()


class TestRule:
    """Test cases for the Rule base class."""

    def test_rule_has_code_attribute(self) -> None:
        """Test that Rule class has a code attribute."""
        assert hasattr(Rule, 'code')
        assert Rule.code == "UNSPEC"

    def test_rule_has_message_attribute(self) -> None:
        """Test that Rule class has a message attribute."""
        assert hasattr(Rule, 'message')
        assert Rule.message == "No message"

    def test_applies_returns_none(self, rule: Rule, mock_vnode: Mock, mock_ctx: Mock) -> None:
        """Test that applies() returns None by default."""
        result = rule.applies(mock_vnode, mock_ctx)
        assert result is None

    def test_report_generates_diagnostic(self, rule: Rule, mock_vnode: Mock) -> None:
        """Test that report() generates a proper diagnostic dictionary."""
        result = rule.report(mock_vnode)
        
        assert isinstance(result, dict)
        assert "line" in result
        assert "col" in result
        assert "message" in result
        
        assert result["line"] == 10
        assert result["col"] == 5
        assert result["message"] == "No message"

    def test_report_uses_location_data(self, rule: Rule, mock_vnode: Mock) -> None:
        """Test that report() correctly extracts location from vnode."""
        mock_vnode.location = {"line": 42, "col": 99}
        result = rule.report(mock_vnode)
        
        assert result["line"] == 42
        assert result["col"] == 99

    def test_report_uses_rule_message(self, rule: Rule, mock_vnode: Mock) -> None:
        """Test that report() uses the rule's message attribute."""
        rule.message = "Custom error message"
        result = rule.report(mock_vnode)
        
        assert result["message"] == "Custom error message"


class TestCustomRule:
    """Test cases for custom rule implementations."""

    @pytest.fixture
    def custom_rule(self) -> Rule:
        """Fixture for a custom rule implementation."""
        class CustomRule(Rule):
            code = "CUSTOM_RULE"
            message = "This is a custom rule"

            def applies(self, vnode: Any, ctx: Any) -> bool:
                return True

        return CustomRule()

    @pytest.fixture
    def mock_vnode(self) -> Mock:
        """Fixture for a mock vnode."""
        mock = Mock(spec=BaseVNode)
        mock.location = {"line": 1, "col": 1}
        return mock

    @pytest.fixture
    def mock_ctx(self) -> Mock:
        """Fixture for a mock context."""
        return Mock()

    def test_custom_rule_code(self, custom_rule: Rule) -> None:
        """Test that custom rules can set their own code."""
        assert custom_rule.code == "CUSTOM_RULE"

    def test_custom_rule_message(self, custom_rule: Rule) -> None:
        """Test that custom rules can set their own message."""
        assert custom_rule.message == "This is a custom rule"

    def test_custom_rule_applies_implementation(self, custom_rule: Rule, mock_vnode: Mock, mock_ctx: Mock) -> None:
        """Test that custom rules can implement applies()."""
        result = custom_rule.applies(mock_vnode, mock_ctx)
        assert result is True

    def test_custom_rule_report(self, custom_rule: Rule, mock_vnode: Mock) -> None:
        """Test that custom rules inherit report() functionality."""
        result = custom_rule.report(mock_vnode)
        
        assert result["message"] == "This is a custom rule"
        assert result["line"] == 1
        assert result["col"] == 1
