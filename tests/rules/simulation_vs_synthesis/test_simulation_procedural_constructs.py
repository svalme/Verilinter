"""Node rule tests for `simulation_vs_synthesis`: procedural blocks, loops and simulation-only statements."""
import pytest
from src.pkg.parser.syntax_kinds import ALWAYS_BLOCK_KIND, FINAL_BLOCK_KIND, INITIAL_BLOCK_KIND, WHILE_TOKEN_KIND, WAIT_TOKEN_KIND, SEQUENTIAL_BLOCK_STATEMENT_KIND, RETURN_KEYWORD_TOKEN_KIND, REPEAT_TOKEN_KIND, PARALLEL_BLOCK_STATEMENT_KIND, MINUS_DOUBLE_ARROW_TOKEN_KIND, MINUS_ARROW_TOKEN_KIND, LOOP_GENERATE_KIND, GREATER_THAN_TOKEN_KIND, FOREVER_KEYWORD_TOKEN_KIND, FOREACH_KEYWORD_TOKEN_KIND, FOR_KEYWORD_TOKEN_KIND, DO_WHILE_STATEMENT_KIND, DO_KEYWORD_TOKEN_KIND, DISABLE_KEYWORD_TOKEN_KIND, DISABLE_IFF_KIND, ASSIGN_KEYWORD_TOKEN_KIND, CONTINUOUS_ASSIGN_KIND, DEASSIGN_KEYWORD_TOKEN_KIND, DELAY3_KIND, DELAY_CONTROL_KIND, FORCE_KEYWORD_TOKEN_KIND, INITIAL_KEYWORD_TOKEN_KIND, PARAMETER_KEYWORD_TOKEN_KIND, RELEASE_KEYWORD_TOKEN_KIND
from src.pkg.rules.simulation_vs_synthesis.procedural.no_disable_statement import NoDisableStatementRule
from src.pkg.rules.simulation_vs_synthesis.procedural.no_do_while_loop import NoDoWhileLoopRule
from src.pkg.rules.simulation_vs_synthesis.procedural.no_event_trigger import NoEventTriggerRule
from src.pkg.rules.simulation_vs_synthesis.procedural.no_for_loop import NoForLoopRule
from src.pkg.rules.simulation_vs_synthesis.procedural.no_foreach_loop import NoForeachLoopRule
from src.pkg.rules.simulation_vs_synthesis.procedural.no_fork_join import NoForkJoinRule
from src.pkg.rules.simulation_vs_synthesis.procedural.no_forever_loop import NoForeverLoopRule
from src.pkg.rules.simulation_vs_synthesis.procedural.no_assign_deassign import NoAssignDeassignRule
from src.pkg.rules.simulation_vs_synthesis.procedural.no_final_block import NoFinalBlockRule
from src.pkg.rules.simulation_vs_synthesis.procedural.no_force_release import NoForceReleaseRule
from src.pkg.rules.simulation_vs_synthesis.procedural.no_initial_block import NoInitialBlockRule
from src.pkg.rules.simulation_vs_synthesis.procedural.no_repeat_loop import NoRepeatLoopRule
from src.pkg.rules.simulation_vs_synthesis.procedural.no_while_loop import NoWhileLoopRule
from src.pkg.rules.simulation_vs_synthesis.procedural.no_wait_statement import NoWaitStatementRule
from src.pkg.rules.simulation_vs_synthesis.procedural.no_delay_control import NoDelayControlRule
from tests.support.fakes import fake_vnode
from tests.support.syntax_context_builders import continuous_assign_context, event_trigger_statement_context, token_vnode
from src.pkg.walk.context import Context
from src.pkg.vnodes.base_vnode import BaseVNode
from tests.support.rule_node_helpers import mock_vnode


class TestNoInitialBlockRule:
    """Test cases for the NoInitialBlockRule."""

    @pytest.fixture
    def rule(self) -> NoInitialBlockRule:
        return NoInitialBlockRule()

    def test_rule_has_correct_code(self, rule: NoInitialBlockRule) -> None:
        assert rule.code == "NO_INITIAL_BLOCK"

    def test_rule_has_correct_message(self, rule: NoInitialBlockRule) -> None:
        assert rule.message == "Use of initial blocks can be unsafe in synthesizable RTL"

    def test_applies_returns_true_for_initial_block(self, rule: NoInitialBlockRule) -> None:
        mock_vnode = fake_vnode(INITIAL_BLOCK_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_procedural_block(self, rule: NoInitialBlockRule) -> None:
        mock_vnode = fake_vnode(ALWAYS_BLOCK_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoInitialBlockRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 6, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 6
        assert result["col"] == 3
        assert result["message"] == "Use of initial blocks can be unsafe in synthesizable RTL"


class TestNoFinalBlockRule:
    @pytest.fixture
    def rule(self) -> NoFinalBlockRule:
        return NoFinalBlockRule()

    def test_rule_has_correct_code(self, rule: NoFinalBlockRule) -> None:
        assert rule.code == "NO_FINAL_BLOCK"

    def test_rule_has_correct_message(self, rule: NoFinalBlockRule) -> None:
        assert rule.message == "Use of final blocks is usually not appropriate in synthesizable RTL"

    def test_applies_returns_true_for_final_block(self, rule: NoFinalBlockRule) -> None:
        mock_vnode = fake_vnode(FINAL_BLOCK_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_procedural_block(self, rule: NoFinalBlockRule) -> None:
        mock_vnode = fake_vnode(ALWAYS_BLOCK_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoFinalBlockRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 11, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 11
        assert result["col"] == 3
        assert result["message"] == "Use of final blocks is usually not appropriate in synthesizable RTL"


class TestNoForeverLoopRule:
    @pytest.fixture
    def rule(self) -> NoForeverLoopRule:
        return NoForeverLoopRule()

    def test_rule_has_correct_code(self, rule: NoForeverLoopRule) -> None:
        assert rule.code == "NO_FOREVER_LOOP"

    def test_rule_has_correct_message(self, rule: NoForeverLoopRule) -> None:
        assert rule.message == "Use of forever loops is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_forever_keyword(self, rule: NoForeverLoopRule) -> None:
        mock_vnode = token_vnode(FOREVER_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_repeat_keyword(self, rule: NoForeverLoopRule) -> None:
        mock_vnode = token_vnode(REPEAT_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoForeverLoopRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 3, "col": 11}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 11
        assert result["message"] == "Use of forever loops is discouraged in synthesizable RTL"


class TestNoWaitStatementRule:
    @pytest.fixture
    def rule(self) -> NoWaitStatementRule:
        return NoWaitStatementRule()

    def test_rule_has_correct_code(self, rule: NoWaitStatementRule) -> None:
        assert rule.code == "NO_WAIT_STATEMENT"

    def test_rule_has_correct_message(self, rule: NoWaitStatementRule) -> None:
        assert rule.message == "Use of wait statements is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_wait_keyword(self, rule: NoWaitStatementRule) -> None:
        mock_vnode = token_vnode(WAIT_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_while_keyword(self, rule: NoWaitStatementRule) -> None:
        mock_vnode = token_vnode(WHILE_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoWaitStatementRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 3, "col": 11}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 11
        assert result["message"] == "Use of wait statements is discouraged in synthesizable RTL"


class TestNoRepeatLoopRule:
    @pytest.fixture
    def rule(self) -> NoRepeatLoopRule:
        return NoRepeatLoopRule()

    def test_rule_has_correct_code(self, rule: NoRepeatLoopRule) -> None:
        assert rule.code == "NO_REPEAT_LOOP"

    def test_rule_has_correct_message(self, rule: NoRepeatLoopRule) -> None:
        assert rule.message == "Use of repeat loops is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_repeat_keyword(self, rule: NoRepeatLoopRule) -> None:
        mock_vnode = token_vnode(REPEAT_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_while_keyword(self, rule: NoRepeatLoopRule) -> None:
        mock_vnode = token_vnode(WHILE_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoRepeatLoopRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 3, "col": 11}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 11
        assert result["message"] == "Use of repeat loops is discouraged in synthesizable RTL"


class TestNoWhileLoopRule:
    @pytest.fixture
    def rule(self) -> NoWhileLoopRule:
        return NoWhileLoopRule()

    def test_rule_has_correct_code(self, rule: NoWhileLoopRule) -> None:
        assert rule.code == "NO_WHILE_LOOP"

    def test_rule_has_correct_message(self, rule: NoWhileLoopRule) -> None:
        assert rule.message == "Use of while loops is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_while_keyword(self, rule: NoWhileLoopRule) -> None:
        mock_vnode = token_vnode(WHILE_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_wait_keyword(self, rule: NoWhileLoopRule) -> None:
        mock_vnode = token_vnode(WAIT_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_false_for_do_while_trailing_while(self, rule: NoWhileLoopRule) -> None:
        mock_vnode = token_vnode(WHILE_TOKEN_KIND)
        do_while_vnode = fake_vnode(DO_WHILE_STATEMENT_KIND)
        context = Context().push(do_while_vnode)

        assert rule.applies(mock_vnode, context) is False

    def test_report_returns_correct_format(self, rule: NoWhileLoopRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 3, "col": 11}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 11
        assert result["message"] == "Use of while loops is discouraged in synthesizable RTL"


class TestNoForeachLoopRule:
    @pytest.fixture
    def rule(self) -> NoForeachLoopRule:
        return NoForeachLoopRule()

    def test_rule_has_correct_code(self, rule: NoForeachLoopRule) -> None:
        assert rule.code == "NO_FOREACH_LOOP"

    def test_rule_has_correct_message(self, rule: NoForeachLoopRule) -> None:
        assert rule.message == "Use of foreach loops is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_foreach_keyword(self, rule: NoForeachLoopRule) -> None:
        mock_vnode = token_vnode(FOREACH_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_for_keyword(self, rule: NoForeachLoopRule) -> None:
        mock_vnode = token_vnode(FOR_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoForeachLoopRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 3, "col": 11}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 11
        assert result["message"] == "Use of foreach loops is discouraged in synthesizable RTL"


class TestNoDoWhileLoopRule:
    @pytest.fixture
    def rule(self) -> NoDoWhileLoopRule:
        return NoDoWhileLoopRule()

    def test_rule_has_correct_code(self, rule: NoDoWhileLoopRule) -> None:
        assert rule.code == "NO_DO_WHILE_LOOP"

    def test_rule_has_correct_message(self, rule: NoDoWhileLoopRule) -> None:
        assert rule.message == "Use of do-while loops is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_do_keyword(self, rule: NoDoWhileLoopRule) -> None:
        mock_vnode = token_vnode(DO_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_while_keyword(self, rule: NoDoWhileLoopRule) -> None:
        mock_vnode = token_vnode(WHILE_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoDoWhileLoopRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 3, "col": 11}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 11
        assert result["message"] == "Use of do-while loops is discouraged in synthesizable RTL"


class TestNoForLoopRule:
    @pytest.fixture
    def rule(self) -> NoForLoopRule:
        return NoForLoopRule()

    def test_rule_has_correct_code(self, rule: NoForLoopRule) -> None:
        assert rule.code == "NO_FOR_LOOP"

    def test_rule_has_correct_message(self, rule: NoForLoopRule) -> None:
        assert rule.message == "Use of for loops is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_for_keyword(self, rule: NoForLoopRule) -> None:
        mock_vnode = token_vnode(FOR_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_foreach_keyword(self, rule: NoForLoopRule) -> None:
        mock_vnode = token_vnode(FOREACH_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_false_for_generate_for_token(self, rule: NoForLoopRule) -> None:
        mock_vnode = token_vnode(FOR_KEYWORD_TOKEN_KIND)
        loop_generate_vnode = fake_vnode(LOOP_GENERATE_KIND)
        context = Context().push(loop_generate_vnode)

        assert rule.applies(mock_vnode, context) is False

    def test_report_returns_correct_format(self, rule: NoForLoopRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 3, "col": 11}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 11
        assert result["message"] == "Use of for loops is discouraged in synthesizable RTL"


class TestNoDisableStatementRule:
    @pytest.fixture
    def rule(self) -> NoDisableStatementRule:
        return NoDisableStatementRule()

    def test_rule_has_correct_code(self, rule: NoDisableStatementRule) -> None:
        assert rule.code == "NO_DISABLE_STATEMENT"

    def test_rule_has_correct_message(self, rule: NoDisableStatementRule) -> None:
        assert rule.message == "Use of disable statements is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_disable_keyword(self, rule: NoDisableStatementRule) -> None:
        mock_vnode = token_vnode(DISABLE_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_return_keyword(self, rule: NoDisableStatementRule) -> None:
        mock_vnode = token_vnode(RETURN_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_false_for_disable_keyword_inside_disable_iff(self, rule: NoDisableStatementRule) -> None:
        """`disable iff (...)` (a property's clock/reset qualifier) reuses the same
        DisableKeyword token as an ordinary `disable <label>;` statement, but is a
        different grammatical construct (DisableIffSyntax) and not a disable
        statement at all."""
        mock_vnode = token_vnode(DISABLE_KEYWORD_TOKEN_KIND)
        ancestor = fake_vnode(DISABLE_IFF_KIND)
        ctx = Context().push(ancestor)

        assert rule.applies(mock_vnode, ctx) is False

    def test_report_returns_correct_format(self, rule: NoDisableStatementRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 3, "col": 11}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 11
        assert result["message"] == "Use of disable statements is discouraged in synthesizable RTL"


class TestNoEventTriggerRule:
    @pytest.fixture
    def rule(self) -> NoEventTriggerRule:
        return NoEventTriggerRule()

    def test_rule_has_correct_code(self, rule: NoEventTriggerRule) -> None:
        assert rule.code == "NO_EVENT_TRIGGER"

    def test_rule_has_correct_message(self, rule: NoEventTriggerRule) -> None:
        assert rule.message == "Use of event trigger statements is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_blocking_event_trigger(self, rule: NoEventTriggerRule) -> None:
        mock_vnode = token_vnode(MINUS_ARROW_TOKEN_KIND)

        assert rule.applies(mock_vnode, event_trigger_statement_context()) is True

    def test_applies_returns_true_for_nonblocking_event_trigger(self, rule: NoEventTriggerRule) -> None:
        mock_vnode = token_vnode(MINUS_DOUBLE_ARROW_TOKEN_KIND)

        assert rule.applies(mock_vnode, event_trigger_statement_context(nonblocking=True)) is True

    def test_applies_returns_false_for_greater_than(self, rule: NoEventTriggerRule) -> None:
        mock_vnode = token_vnode(GREATER_THAN_TOKEN_KIND)

        assert rule.applies(mock_vnode, event_trigger_statement_context()) is False

    def test_applies_returns_false_for_minus_arrow_used_as_implication_operator(self, rule: NoEventTriggerRule) -> None:
        """`->` is also the logical-implication operator in ordinary expressions
        (`a -> b`), not just an event-trigger statement (`-> done;`). Outside a
        BlockingEventTriggerStatement/NonblockingEventTriggerStatement ancestor, it
        must not be flagged."""
        mock_vnode = token_vnode(MINUS_ARROW_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoEventTriggerRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 3, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 5
        assert result["message"] == "Use of event trigger statements is discouraged in synthesizable RTL"


class TestNoForkJoinRule:
    @pytest.fixture
    def rule(self) -> NoForkJoinRule:
        return NoForkJoinRule()

    def test_rule_has_correct_code(self, rule: NoForkJoinRule) -> None:
        assert rule.code == "NO_FORK_JOIN"

    def test_rule_has_correct_message(self, rule: NoForkJoinRule) -> None:
        assert rule.message == "Use of fork/join style parallel blocks is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_parallel_block(self, rule: NoForkJoinRule) -> None:
        mock_vnode = fake_vnode(PARALLEL_BLOCK_STATEMENT_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_sequential_block(self, rule: NoForkJoinRule) -> None:
        mock_vnode = fake_vnode(SEQUENTIAL_BLOCK_STATEMENT_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoForkJoinRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 3, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 3
        assert result["message"] == "Use of fork/join style parallel blocks is discouraged in synthesizable RTL"


class TestNoForceReleaseRule:
    @pytest.fixture
    def rule(self) -> NoForceReleaseRule:
        return NoForceReleaseRule()

    def test_rule_has_correct_code(self, rule: NoForceReleaseRule) -> None:
        assert rule.code == "NO_FORCE_RELEASE"

    def test_rule_has_correct_message(self, rule: NoForceReleaseRule) -> None:
        assert rule.message == "Use of force/release is discouraged in RTL; prefer explicit structural or procedural intent"

    def test_applies_returns_true_for_force_keyword(self, rule: NoForceReleaseRule) -> None:
        mock_vnode = fake_vnode(FORCE_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_release_keyword(self, rule: NoForceReleaseRule) -> None:
        mock_vnode = fake_vnode(RELEASE_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_token(self, rule: NoForceReleaseRule) -> None:
        mock_vnode = fake_vnode(INITIAL_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoForceReleaseRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 5, "col": 9}
        result = rule.report(mock_vnode)

        assert result["line"] == 5
        assert result["col"] == 9
        assert result["message"] == "Use of force/release is discouraged in RTL; prefer explicit structural or procedural intent"


class TestNoAssignDeassignRule:
    @pytest.fixture
    def rule(self) -> NoAssignDeassignRule:
        return NoAssignDeassignRule()

    def test_rule_has_correct_code(self, rule: NoAssignDeassignRule) -> None:
        assert rule.code == "NO_ASSIGN_DEASSIGN"

    def test_rule_has_correct_message(self, rule: NoAssignDeassignRule) -> None:
        assert rule.message == "Use of assign/deassign is discouraged in RTL; prefer explicit continuous or procedural intent"

    def test_applies_returns_true_for_assign_keyword(self, rule: NoAssignDeassignRule) -> None:
        mock_vnode = fake_vnode(ASSIGN_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_deassign_keyword(self, rule: NoAssignDeassignRule) -> None:
        mock_vnode = fake_vnode(DEASSIGN_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_token(self, rule: NoAssignDeassignRule) -> None:
        mock_vnode = fake_vnode(PARAMETER_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_false_for_assign_keyword_inside_continuous_assign(self, rule: NoAssignDeassignRule) -> None:
        mock_vnode = fake_vnode(ASSIGN_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, continuous_assign_context()) is False

    def test_report_returns_correct_format(self, rule: NoAssignDeassignRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 5, "col": 9}
        result = rule.report(mock_vnode)

        assert result["line"] == 5
        assert result["col"] == 9
        assert result["message"] == "Use of assign/deassign is discouraged in RTL; prefer explicit continuous or procedural intent"


class TestNoDelayControlRule:
    @pytest.fixture
    def rule(self) -> NoDelayControlRule:
        return NoDelayControlRule()

    def test_rule_has_correct_code(self, rule: NoDelayControlRule) -> None:
        assert rule.code == "NO_DELAY_CONTROL"

    def test_rule_has_correct_message(self, rule: NoDelayControlRule) -> None:
        assert rule.message == "Use of delay controls (#delay) is discouraged in synthesizable RTL; delays are simulation-only timing"

    def test_applies_returns_true_for_delay_control_node(self, rule: NoDelayControlRule) -> None:
        mock_vnode = fake_vnode(DELAY_CONTROL_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_delay3_node(self, rule: NoDelayControlRule) -> None:
        mock_vnode = fake_vnode(DELAY3_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoDelayControlRule) -> None:
        mock_vnode = fake_vnode(CONTINUOUS_ASSIGN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoDelayControlRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 2, "col": 12}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 12
        assert result["message"] == "Use of delay controls (#delay) is discouraged in synthesizable RTL; delays are simulation-only timing"
