import pytest
from unittest.mock import Mock

from src.pkg.rules.rule_runner import RuleRunner
from src.pkg.rules.base_rule import Rule
from src.pkg.vnode.base_vnode import BaseVNode


@pytest.fixture
def runner() -> RuleRunner:
    """Fixture for a fresh RuleRunner instance."""
    return RuleRunner()


@pytest.fixture
def mock_vnode() -> Mock:
    """Fixture for a mock vnode."""
    mock = Mock(spec=BaseVNode)
    mock.location = {"line": 1, "col": 1}
    return mock


@pytest.fixture
def mock_ctx() -> Mock:
    """Fixture for a mock context."""
    return Mock()


class TestRuleRunner:
    """Test cases for the RuleRunner class."""

    def test_rule_runner_initializes_empty(self, runner: RuleRunner) -> None:
        """Test that RuleRunner starts with no rules."""
        assert len(runner._rules) == 0

    def test_register_adds_rule(self, runner: RuleRunner) -> None:
        """Test that register() adds a rule instance to the runner."""
        class TestRule(Rule):
            pass

        runner.register(TestRule)
        
        assert len(runner._rules) == 1
        assert isinstance(runner._rules[0], TestRule)

    def test_register_returns_class(self, runner: RuleRunner) -> None:
        """Test that register() returns the class for use as a decorator."""
        class TestRule(Rule):
            code = "TEST"

        result = runner.register(TestRule)
        
        assert result == TestRule

    def test_register_instantiates_rule(self, runner: RuleRunner) -> None:
        """Test that register() instantiates the rule class."""
        class TestRule(Rule):
            pass

        runner.register(TestRule)
        
        registered = runner._rules[0]
        assert isinstance(registered, TestRule)

    def test_run_with_empty_rules(self, runner: RuleRunner) -> None:
        """Test that run() returns empty list when no rules are registered."""
        walk_results: list[tuple[any, any]] = []
        diagnostics = runner.run(walk_results)
        
        assert diagnostics == []

    def test_run_applies_rules_to_walk_results(self, runner: RuleRunner, mock_vnode: Mock, mock_ctx: Mock) -> None:
        """Test that run() applies registered rules to walk results."""
        class AlwaysApplyRule(Rule):
            code = "ALWAYS_APPLY"
            message = "This always applies"

            def applies(self, vnode: any, ctx: any) -> bool:
                return True

        runner.register(AlwaysApplyRule)
        
        walk_results: list[tuple[Mock, Mock]] = [(mock_vnode, mock_ctx)]
        diagnostics = runner.run(walk_results)

        assert len(diagnostics) == 1
        assert diagnostics[0]["message"] == "This always applies"

    def test_run_skips_non_applicable_rules(self, runner: RuleRunner, mock_vnode: Mock, mock_ctx: Mock) -> None:
        """Test that run() skips rules that don't apply."""
        class NeverApplyRule(Rule):
            code = "NEVER_APPLY"
            message = "This never applies"

            def applies(self, vnode: any, ctx: any) -> bool:
                return False

        runner.register(NeverApplyRule)
        
        walk_results: list[tuple[Mock, Mock]] = [(mock_vnode, mock_ctx)]
        diagnostics = runner.run(walk_results)

        assert diagnostics == []

    def test_run_with_multiple_rules(self, runner: RuleRunner, mock_vnode: Mock, mock_ctx: Mock) -> None:
        """Test that run() applies multiple rules correctly."""
        class Rule1(Rule):
            code = "RULE_1"
            message = "Rule 1"

            def applies(self, vnode: any, ctx: any) -> bool:
                return True

        class Rule2(Rule):
            code = "RULE_2"
            message = "Rule 2"

            def applies(self, vnode: any, ctx: any) -> bool:
                return True

        runner.register(Rule1)
        runner.register(Rule2)

        walk_results: list[tuple[Mock, Mock]] = [(mock_vnode, mock_ctx)]
        diagnostics = runner.run(walk_results)

        assert len(diagnostics) == 2
        messages = [d["message"] for d in diagnostics]
        assert "Rule 1" in messages
        assert "Rule 2" in messages

    def test_run_with_multiple_walk_results(self, runner: RuleRunner, mock_ctx: Mock) -> None:
        """Test that run() processes multiple walk results."""
        class TestRule(Rule):
            code = "TEST"
            message = "Test message"

            def applies(self, vnode: any, ctx: any) -> bool:
                return True

        runner.register(TestRule)

        # Create multiple mock walk results
        mock_vnode1 = Mock(spec=BaseVNode)
        mock_vnode1.location = {"line": 1, "col": 1}
        mock_vnode2 = Mock(spec=BaseVNode)
        mock_vnode2.location = {"line": 2, "col": 2}
        
        walk_results: list[tuple[Mock, Mock]] = [
            (mock_vnode1, mock_ctx),
            (mock_vnode2, mock_ctx),
        ]
        diagnostics = runner.run(walk_results)

        assert len(diagnostics) == 2
        assert diagnostics[0]["line"] == 1
        assert diagnostics[1]["line"] == 2

    def test_run_collects_all_violations(self, runner: RuleRunner, mock_ctx: Mock) -> None:
        """Test that run() collects all violations across rules and vnodes."""
        class Rule1(Rule):
            code = "RULE_1"
            message = "Violation 1"

            def applies(self, vnode: any, ctx: any) -> bool:
                return True

        class Rule2(Rule):
            code = "RULE_2"
            message = "Violation 2"

            def applies(self, vnode: any, ctx: any) -> bool:
                return True

        runner.register(Rule1)
        runner.register(Rule2)

        mock_vnode1 = Mock(spec=BaseVNode)
        mock_vnode1.location = {"line": 1, "col": 1}
        mock_vnode2 = Mock(spec=BaseVNode)
        mock_vnode2.location = {"line": 2, "col": 2}
        
        walk_results: list[tuple[Mock, Mock]] = [
            (mock_vnode1, mock_ctx),
            (mock_vnode2, mock_ctx),
        ]
        diagnostics = runner.run(walk_results)

        # 2 vnodes × 2 rules = 4 diagnostics
        assert len(diagnostics) == 4
