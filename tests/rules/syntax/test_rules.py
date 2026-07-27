import pytest
from unittest.mock import Mock
import pyslang as sl
from pathlib import Path

from src.pkg.rules.syntax.default_case import DefaultCaseRule
from src.pkg.rules.syntax.no_always_ff import NoAlwaysFFRule
from src.pkg.rules.syntax.no_always_latch import NoAlwaysLatchRule
from src.pkg.rules.syntax.no_blocking_sequential_logic import NoBlockingAssignmentInSequentialRule
from src.pkg.rules.syntax.no_case_generate import NoCaseGenerateRule
from src.pkg.rules.syntax.no_case_inside import NoCaseInsideRule
from src.pkg.rules.syntax.no_disable_statement import NoDisableStatementRule
from src.pkg.rules.syntax.no_forever_loop import NoForeverLoopRule
from src.pkg.rules.syntax.no_inside_operator import NoInsideOperatorRule
from src.pkg.rules.syntax.no_assign_deassign import NoAssignDeassignRule
from src.pkg.rules.syntax.no_final_block import NoFinalBlockRule
from src.pkg.rules.syntax.no_full_parallel_case import NoFullParallelCaseRule
from src.pkg.rules.syntax.no_force_release import NoForceReleaseRule
from src.pkg.rules.syntax.no_initial_block import NoInitialBlockRule
from src.pkg.rules.syntax.no_defparam import NoDefparamRule
from src.pkg.rules.syntax.no_inout_internal import NoInternalInoutRule
from src.pkg.rules.syntax.no_latch_in_always_comb import NoLatchInAlwaysCombRule
from src.pkg.rules.syntax.no_nonblocking_comb import NoNonBlockingAssignmentInCombRule
from src.pkg.rules.syntax.no_supply0_supply1 import NoSupply0Supply1Rule
from src.pkg.rules.syntax.no_tranif_rtranif import NoTranifRtranifRule
from src.pkg.rules.syntax.no_tran_rtran import NoTranRtranRule
from src.pkg.rules.syntax.no_trireg import NoTriregRule
from src.pkg.rules.syntax.no_wait_statement import NoWaitStatementRule
from src.pkg.rules.syntax.no_priority_if import NoPriorityIfRule
from src.pkg.rules.syntax.no_unique0_case import NoUnique0CaseRule
from src.pkg.rules.syntax.no_unique_if import NoUniqueIfRule
from src.pkg.rules.syntax.no_unique_priority_case import NoUniquePriorityCaseRule
from src.pkg.rules.syntax.no_wand_wor import NoWandWorRule
from tests.support.syntax_context_builders import case_context, conditional_context, token_vnode
from src.pkg.walk.context import Context, ContextFlag
from src.pkg.vnodes.base_vnode import BaseVNode
from src.pkg.vnodes.token_vnode import TokenVNode

DATA = Path(__file__).parent.parent.parent / "data"


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
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.InitialBlock

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_procedural_block(self, rule: NoInitialBlockRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.AlwaysBlock

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoInitialBlockRule, mock_vnode: Mock) -> None:
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
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.FinalBlock

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_procedural_block(self, rule: NoFinalBlockRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.AlwaysBlock

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoFinalBlockRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 11, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 11
        assert result["col"] == 3
        assert result["message"] == "Use of final blocks is usually not appropriate in synthesizable RTL"


class TestNoAlwaysLatchRule:
    @pytest.fixture
    def rule(self) -> NoAlwaysLatchRule:
        return NoAlwaysLatchRule()

    def test_rule_has_correct_code(self, rule: NoAlwaysLatchRule) -> None:
        assert rule.code == "NO_ALWAYS_LATCH"

    def test_rule_has_correct_message(self, rule: NoAlwaysLatchRule) -> None:
        assert rule.message == "Use of always_latch can hide unintended latch-oriented design choices"

    def test_applies_returns_true_for_always_latch_block(self, rule: NoAlwaysLatchRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.AlwaysLatchBlock

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_procedural_block(self, rule: NoAlwaysLatchRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.AlwaysCombBlock

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoAlwaysLatchRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 14, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 14
        assert result["col"] == 3
        assert result["message"] == "Use of always_latch can hide unintended latch-oriented design choices"


class TestNoAlwaysFFRule:
    @pytest.fixture
    def rule(self) -> NoAlwaysFFRule:
        return NoAlwaysFFRule()

    def test_rule_has_correct_code(self, rule: NoAlwaysFFRule) -> None:
        assert rule.code == "NO_ALWAYS_FF"

    def test_rule_has_correct_message(self, rule: NoAlwaysFFRule) -> None:
        assert rule.message == "Use of always_ff is discouraged in this RTL subset"

    def test_applies_returns_true_for_always_ff_block(self, rule: NoAlwaysFFRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.AlwaysFFBlock

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_procedural_block(self, rule: NoAlwaysFFRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.AlwaysLatchBlock

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoAlwaysFFRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 10, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 10
        assert result["col"] == 3
        assert result["message"] == "Use of always_ff is discouraged in this RTL subset"


class TestNoCaseGenerateRule:
    @pytest.fixture
    def rule(self) -> NoCaseGenerateRule:
        return NoCaseGenerateRule()

    def test_rule_has_correct_code(self, rule: NoCaseGenerateRule) -> None:
        assert rule.code == "NO_CASE_GENERATE"

    def test_rule_has_correct_message(self, rule: NoCaseGenerateRule) -> None:
        assert rule.message == "Use of case generate can make structural intent harder to follow"

    def test_applies_returns_true_for_case_generate_node(self, rule: NoCaseGenerateRule) -> None:
        tree = sl.SyntaxTree.fromFile(str(DATA / "case_generate.v"))

        def walk(node):
            if isinstance(node, sl.CaseGenerateSyntax):
                return node
            if hasattr(node, "__iter__"):
                for child in node:
                    found = walk(child)
                    if found is not None:
                        return found
            return None

        raw_node = walk(tree.root)
        assert raw_node is not None

        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = raw_node

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_syntax_node(self, rule: NoCaseGenerateRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.AlwaysCombBlock

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoCaseGenerateRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 3, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 5
        assert result["message"] == "Use of case generate can make structural intent harder to follow"


class TestNoFullParallelCaseRule:
    @pytest.fixture
    def rule(self) -> NoFullParallelCaseRule:
        return NoFullParallelCaseRule()

    def test_rule_has_correct_code(self, rule: NoFullParallelCaseRule) -> None:
        assert rule.code == "NO_FULL_PARALLEL_CASE"

    def test_rule_has_correct_message(self, rule: NoFullParallelCaseRule) -> None:
        assert rule.message == "Use of full_case / parallel_case pragmas can hide real case coverage issues"

    def test_applies_returns_false_for_non_case_token(self, rule: NoFullParallelCaseRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.Identifier

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_true_for_case_with_preceding_pragma_comment(self, rule: NoFullParallelCaseRule) -> None:
        tree = sl.SyntaxTree.fromFile(str(DATA / "full_parallel_case.v"))

        def walk(node):
            if isinstance(node, sl.Token) and node.kind == sl.TokenKind.CaseKeyword:
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

    def test_report_returns_correct_format(self, rule: NoFullParallelCaseRule, mock_vnode: Mock) -> None:
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
        tree = sl.SyntaxTree.fromFile(str(DATA / "case_inside.v"))

        def walk(node):
            if isinstance(node, sl.Token) and node.kind == sl.TokenKind.InsideKeyword:
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

    def test_applies_returns_false_for_inside_operator(self, rule: NoCaseInsideRule) -> None:
        tree = sl.SyntaxTree.fromText(
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

        def walk(node):
            if isinstance(node, sl.Token) and node.kind == sl.TokenKind.InsideKeyword:
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

        assert rule.applies(vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoCaseInsideRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 4, "col": 10}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 10
        assert result["message"] == "Use of case inside is discouraged in this RTL subset"


class TestNoForeverLoopRule:
    @pytest.fixture
    def rule(self) -> NoForeverLoopRule:
        return NoForeverLoopRule()

    def test_rule_has_correct_code(self, rule: NoForeverLoopRule) -> None:
        assert rule.code == "NO_FOREVER_LOOP"

    def test_rule_has_correct_message(self, rule: NoForeverLoopRule) -> None:
        assert rule.message == "Use of forever loops is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_forever_keyword(self, rule: NoForeverLoopRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.ForeverKeyword)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_repeat_keyword(self, rule: NoForeverLoopRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.RepeatKeyword)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoForeverLoopRule, mock_vnode: Mock) -> None:
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
        mock_vnode = token_vnode(sl.TokenKind.WaitKeyword)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_while_keyword(self, rule: NoWaitStatementRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.WhileKeyword)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoWaitStatementRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 3, "col": 11}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 11
        assert result["message"] == "Use of wait statements is discouraged in synthesizable RTL"


class TestNoDisableStatementRule:
    @pytest.fixture
    def rule(self) -> NoDisableStatementRule:
        return NoDisableStatementRule()

    def test_rule_has_correct_code(self, rule: NoDisableStatementRule) -> None:
        assert rule.code == "NO_DISABLE_STATEMENT"

    def test_rule_has_correct_message(self, rule: NoDisableStatementRule) -> None:
        assert rule.message == "Use of disable statements is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_disable_keyword(self, rule: NoDisableStatementRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.DisableKeyword)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_return_keyword(self, rule: NoDisableStatementRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.ReturnKeyword)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoDisableStatementRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 3, "col": 11}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 11
        assert result["message"] == "Use of disable statements is discouraged in synthesizable RTL"


class TestNoInsideOperatorRule:
    @pytest.fixture
    def rule(self) -> NoInsideOperatorRule:
        return NoInsideOperatorRule()

    def test_rule_has_correct_code(self, rule: NoInsideOperatorRule) -> None:
        assert rule.code == "NO_INSIDE_OPERATOR"

    def test_rule_has_correct_message(self, rule: NoInsideOperatorRule) -> None:
        assert rule.message == "Use of the inside operator is discouraged in this RTL subset"

    def test_applies_returns_true_for_inside_operator(self, rule: NoInsideOperatorRule) -> None:
        tree = sl.SyntaxTree.fromFile(str(DATA / "inside_operator.v"))

        def walk(node):
            if isinstance(node, sl.Token) and node.kind == sl.TokenKind.InsideKeyword:
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
        tree = sl.SyntaxTree.fromFile(str(DATA / "case_inside.v"))

        def walk(node):
            if isinstance(node, sl.Token) and node.kind == sl.TokenKind.InsideKeyword:
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

        assert rule.applies(vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoInsideOperatorRule, mock_vnode: Mock) -> None:
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
        mock_vnode = token_vnode(sl.TokenKind.UniqueKeyword)
        context = case_context(unique_or_priority="unique")

        assert rule.applies(mock_vnode, context) is True

    def test_applies_returns_true_for_priority_keyword(self, rule: NoUniquePriorityCaseRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.PriorityKeyword)
        context = case_context(unique_or_priority="priority")

        assert rule.applies(mock_vnode, context) is True

    def test_applies_returns_false_for_plain_case_keyword(self, rule: NoUniquePriorityCaseRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.CaseKeyword)

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_false_for_unique_if(self, rule: NoUniquePriorityCaseRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.UniqueKeyword)
        context = conditional_context(unique_or_priority="unique")

        assert rule.applies(mock_vnode, context) is False

    def test_report_returns_correct_format(self, rule: NoUniquePriorityCaseRule, mock_vnode: Mock) -> None:
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
        mock_vnode = token_vnode(getattr(sl.TokenKind, "Unique0Keyword", None))
        context = case_context(unique_or_priority="unique0")

        assert rule.applies(mock_vnode, context) is True

    def test_applies_returns_false_for_unique_keyword(self, rule: NoUnique0CaseRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.UniqueKeyword)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoUnique0CaseRule, mock_vnode: Mock) -> None:
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
        mock_vnode = token_vnode(sl.TokenKind.UniqueKeyword)
        context = conditional_context(unique_or_priority="unique")

        assert rule.applies(mock_vnode, context) is True

    def test_applies_returns_false_for_unique_case(self, rule: NoUniqueIfRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.UniqueKeyword)
        context = case_context(unique_or_priority="unique")

        assert rule.applies(mock_vnode, context) is False

    def test_report_returns_correct_format(self, rule: NoUniqueIfRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 5, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 5
        assert result["col"] == 5
        assert result["message"] == "Use of unique if can overstate branch exclusivity assumptions"


class TestNoPriorityIfRule:
    @pytest.fixture
    def rule(self) -> NoPriorityIfRule:
        return NoPriorityIfRule()

    def test_rule_has_correct_code(self, rule: NoPriorityIfRule) -> None:
        assert rule.code == "NO_PRIORITY_IF"

    def test_rule_has_correct_message(self, rule: NoPriorityIfRule) -> None:
        assert rule.message == "Use of priority if can overstate branch ordering assumptions"

    def test_applies_returns_true_for_priority_if(self, rule: NoPriorityIfRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.PriorityKeyword)
        context = conditional_context(unique_or_priority="priority")

        assert rule.applies(mock_vnode, context) is True

    def test_applies_returns_false_for_priority_case(self, rule: NoPriorityIfRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.PriorityKeyword)
        context = case_context(unique_or_priority="priority")

        assert rule.applies(mock_vnode, context) is False

    def test_report_returns_correct_format(self, rule: NoPriorityIfRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 6, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 6
        assert result["col"] == 5
        assert result["message"] == "Use of priority if can overstate branch ordering assumptions"


class TestNoInternalInoutRule:
    @pytest.fixture
    def rule(self) -> NoInternalInoutRule:
        return NoInternalInoutRule()

    def test_rule_has_correct_code(self, rule: NoInternalInoutRule) -> None:
        assert rule.code == "NO_INOUT_INTERNAL"

    def test_rule_has_correct_message(self, rule: NoInternalInoutRule) -> None:
        assert rule.message == "Internal inout declarations are not allowed"

    def test_applies_returns_true_for_internal_inout_port_declaration(self, rule: NoInternalInoutRule) -> None:
        tree = sl.SyntaxTree.fromFile(str(DATA / "internal_inout.v"))

        def walk(node):
            if isinstance(node, sl.PortDeclarationSyntax):
                return node
            if hasattr(node, "__iter__"):
                for child in node:
                    found = walk(child)
                    if found is not None:
                        return found
            return None

        raw_node = walk(tree.root)
        assert raw_node is not None

        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = raw_node

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_ansi_inout_module_port(self, rule: NoInternalInoutRule) -> None:
        tree = sl.SyntaxTree.fromText("module top(inout wire io); endmodule")

        def walk(node):
            if isinstance(node, sl.ImplicitAnsiPortSyntax):
                return node
            if hasattr(node, "__iter__"):
                for child in node:
                    found = walk(child)
                    if found is not None:
                        return found
            return None

        raw_node = walk(tree.root)
        assert raw_node is not None

        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = raw_node

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoInternalInoutRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 3, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 3
        assert result["message"] == "Internal inout declarations are not allowed"


class TestNoLatchInAlwaysCombRule:
    @pytest.fixture
    def rule(self) -> NoLatchInAlwaysCombRule:
        return NoLatchInAlwaysCombRule()

    def test_rule_has_correct_code(self, rule: NoLatchInAlwaysCombRule) -> None:
        assert rule.code == "NO_LATCH_IN_ALWAYS_COMB"

    def test_rule_has_correct_message(self, rule: NoLatchInAlwaysCombRule) -> None:
        assert rule.message == "always_comb block contains a conditional-only assignment that can infer latch-like storage"

    def test_applies_returns_true_for_missing_default_assignment(self, rule: NoLatchInAlwaysCombRule) -> None:
        tree = sl.SyntaxTree.fromText(
            """
            module top(input logic a, b, output logic y);
                always_comb begin
                    if (a) y = b;
                end
            endmodule
            """
        )

        def walk(node):
            if isinstance(node, sl.ProceduralBlockSyntax):
                return node
            if hasattr(node, "__iter__"):
                for child in node:
                    found = walk(child)
                    if found is not None:
                        return found
            return None

        raw_node = walk(tree.root)
        assert raw_node is not None

        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = raw_node

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_with_prior_default_assignment(self, rule: NoLatchInAlwaysCombRule) -> None:
        tree = sl.SyntaxTree.fromText(
            """
            module top(input logic a, b, output logic y);
                always_comb begin
                    y = '0;
                    if (a) y = b;
                end
            endmodule
            """
        )

        def walk(node):
            if isinstance(node, sl.ProceduralBlockSyntax):
                return node
            if hasattr(node, "__iter__"):
                for child in node:
                    found = walk(child)
                    if found is not None:
                        return found
            return None

        raw_node = walk(tree.root)
        assert raw_node is not None

        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = raw_node

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_false_with_explicit_else(self, rule: NoLatchInAlwaysCombRule) -> None:
        tree = sl.SyntaxTree.fromText(
            """
            module top(input logic a, b, c, output logic y);
                always_comb begin
                    if (a) y = b;
                    else y = c;
                end
            endmodule
            """
        )

        def walk(node):
            if isinstance(node, sl.ProceduralBlockSyntax):
                return node
            if hasattr(node, "__iter__"):
                for child in node:
                    found = walk(child)
                    if found is not None:
                        return found
            return None

        raw_node = walk(tree.root)
        assert raw_node is not None

        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = raw_node

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_false_for_non_always_comb_block(self, rule: NoLatchInAlwaysCombRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.AlwaysBlock

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoLatchInAlwaysCombRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 5, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 5
        assert result["col"] == 3
        assert result["message"] == "always_comb block contains a conditional-only assignment that can infer latch-like storage"


class TestNoDefparamRule:
    @pytest.fixture
    def rule(self) -> NoDefparamRule:
        return NoDefparamRule()

    def test_rule_has_correct_code(self, rule: NoDefparamRule) -> None:
        assert rule.code == "NO_DEFPARAM"

    def test_rule_has_correct_message(self, rule: NoDefparamRule) -> None:
        assert rule.message == "Use of defparam is discouraged; prefer explicit parameter overrides at instantiation"

    def test_applies_returns_true_for_defparam_token(self, rule: NoDefparamRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.DefParamKeyword

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_token(self, rule: NoDefparamRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.ParameterKeyword

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoDefparamRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 6, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 6
        assert result["col"] == 5
        assert result["message"] == "Use of defparam is discouraged; prefer explicit parameter overrides at instantiation"


class TestNoForceReleaseRule:
    @pytest.fixture
    def rule(self) -> NoForceReleaseRule:
        return NoForceReleaseRule()

    def test_rule_has_correct_code(self, rule: NoForceReleaseRule) -> None:
        assert rule.code == "NO_FORCE_RELEASE"

    def test_rule_has_correct_message(self, rule: NoForceReleaseRule) -> None:
        assert rule.message == "Use of force/release is discouraged in RTL; prefer explicit structural or procedural intent"

    def test_applies_returns_true_for_force_keyword(self, rule: NoForceReleaseRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.ForceKeyword

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_release_keyword(self, rule: NoForceReleaseRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.ReleaseKeyword

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_token(self, rule: NoForceReleaseRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.InitialKeyword

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoForceReleaseRule, mock_vnode: Mock) -> None:
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
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.AssignKeyword

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_deassign_keyword(self, rule: NoAssignDeassignRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.DeassignKeyword

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_token(self, rule: NoAssignDeassignRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.ParameterKeyword

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoAssignDeassignRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 5, "col": 9}
        result = rule.report(mock_vnode)

        assert result["line"] == 5
        assert result["col"] == 9
        assert result["message"] == "Use of assign/deassign is discouraged in RTL; prefer explicit continuous or procedural intent"


class TestNoWandWorRule:
    @pytest.fixture
    def rule(self) -> NoWandWorRule:
        return NoWandWorRule()

    def test_rule_has_correct_code(self, rule: NoWandWorRule) -> None:
        assert rule.code == "NO_WAND_WOR"

    def test_rule_has_correct_message(self, rule: NoWandWorRule) -> None:
        assert rule.message == "Use of wand/wor is discouraged in RTL; prefer explicit logic composition instead"

    def test_applies_returns_true_for_wand_keyword(self, rule: NoWandWorRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.WAndKeyword

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_wor_keyword(self, rule: NoWandWorRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.WOrKeyword

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_token(self, rule: NoWandWorRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.LogicKeyword

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoWandWorRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 4, "col": 12}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 12
        assert result["message"] == "Use of wand/wor is discouraged in RTL; prefer explicit logic composition instead"


class TestNoTriregRule:
    @pytest.fixture
    def rule(self) -> NoTriregRule:
        return NoTriregRule()

    def test_rule_has_correct_code(self, rule: NoTriregRule) -> None:
        assert rule.code == "NO_TRIREG"

    def test_rule_has_correct_message(self, rule: NoTriregRule) -> None:
        assert rule.message == "Use of trireg is discouraged in RTL; prefer explicit storage and connectivity modeling instead"

    def test_applies_returns_true_for_trireg_keyword(self, rule: NoTriregRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.TriRegKeyword

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_token(self, rule: NoTriregRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.WireKeyword

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoTriregRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 5
        assert result["message"] == "Use of trireg is discouraged in RTL; prefer explicit storage and connectivity modeling instead"


class TestNoSupply0Supply1Rule:
    @pytest.fixture
    def rule(self) -> NoSupply0Supply1Rule:
        return NoSupply0Supply1Rule()

    def test_rule_has_correct_code(self, rule: NoSupply0Supply1Rule) -> None:
        assert rule.code == "NO_SUPPLY0_SUPPLY1"

    def test_rule_has_correct_message(self, rule: NoSupply0Supply1Rule) -> None:
        assert rule.message == "Use of supply0/supply1 is discouraged in RTL; prefer explicit constant-driving intent instead"

    def test_applies_returns_true_for_supply0_keyword(self, rule: NoSupply0Supply1Rule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.Supply0Keyword

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_supply1_keyword(self, rule: NoSupply0Supply1Rule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.Supply1Keyword

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_token(self, rule: NoSupply0Supply1Rule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.WireKeyword

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoSupply0Supply1Rule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 12}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 12
        assert result["message"] == "Use of supply0/supply1 is discouraged in RTL; prefer explicit constant-driving intent instead"


class TestNoTranRtranRule:
    @pytest.fixture
    def rule(self) -> NoTranRtranRule:
        return NoTranRtranRule()

    def test_rule_has_correct_code(self, rule: NoTranRtranRule) -> None:
        assert rule.code == "NO_TRAN_RTRAN"

    def test_rule_has_correct_message(self, rule: NoTranRtranRule) -> None:
        assert rule.message == "Use of tran/rtran is discouraged in RTL; prefer explicit connectivity modeling instead"

    def test_applies_returns_true_for_tran_keyword(self, rule: NoTranRtranRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.TranKeyword

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_rtran_keyword(self, rule: NoTranRtranRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.RtranKeyword

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_tranif_keyword(self, rule: NoTranRtranRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.TranIf1Keyword

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoTranRtranRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 6, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 6
        assert result["col"] == 5
        assert result["message"] == "Use of tran/rtran is discouraged in RTL; prefer explicit connectivity modeling instead"


class TestNoTranifRtranifRule:
    @pytest.fixture
    def rule(self) -> NoTranifRtranifRule:
        return NoTranifRtranifRule()

    def test_rule_has_correct_code(self, rule: NoTranifRtranifRule) -> None:
        assert rule.code == "NO_TRANIF_RTRANIF"

    def test_rule_has_correct_message(self, rule: NoTranifRtranifRule) -> None:
        assert rule.message == "Use of tranif/rtranif is discouraged in RTL; prefer explicit connectivity modeling instead"

    def test_applies_returns_true_for_tranif1_keyword(self, rule: NoTranifRtranifRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.TranIf1Keyword

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_rtranif0_keyword(self, rule: NoTranifRtranifRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.RtranIf0Keyword

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_tran_keyword(self, rule: NoTranifRtranifRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.TranKeyword

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoTranifRtranifRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 10, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 10
        assert result["col"] == 5
        assert result["message"] == "Use of tranif/rtranif is discouraged in RTL; prefer explicit connectivity modeling instead"
