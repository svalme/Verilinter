import pytest
from unittest.mock import Mock
import pyslang as sl
from pathlib import Path

from src.pkg.rules.syntax.default_case import DefaultCaseRule
from src.pkg.rules.syntax.no_always_latch import NoAlwaysLatchRule
from src.pkg.rules.syntax.no_blocking_sequential_logic import NoBlockingAssignmentInSequentialRule
from src.pkg.rules.syntax.no_case_generate import NoCaseGenerateRule
from src.pkg.rules.syntax.no_final_block import NoFinalBlockRule
from src.pkg.rules.syntax.no_full_parallel_case import NoFullParallelCaseRule
from src.pkg.rules.syntax.no_initial_block import NoInitialBlockRule
from src.pkg.rules.syntax.no_inout_internal import NoInternalInoutRule
from src.pkg.rules.syntax.no_nonblocking_comb import NoNonBlockingAssignmentInCombRule
from src.pkg.rules.syntax.no_unique_priority_case import NoUniquePriorityCaseRule
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


class TestNoUniquePriorityCaseRule:
    @pytest.fixture
    def rule(self) -> NoUniquePriorityCaseRule:
        return NoUniquePriorityCaseRule()

    def test_rule_has_correct_code(self, rule: NoUniquePriorityCaseRule) -> None:
        assert rule.code == "NO_UNIQUE_PRIORITY_CASE"

    def test_rule_has_correct_message(self, rule: NoUniquePriorityCaseRule) -> None:
        assert rule.message == "Use of unique/priority case can overstate case completeness or exclusivity"

    def test_applies_returns_true_for_unique_keyword(self, rule: NoUniquePriorityCaseRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.UniqueKeyword

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_priority_keyword(self, rule: NoUniquePriorityCaseRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.PriorityKeyword

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_plain_case_keyword(self, rule: NoUniquePriorityCaseRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.CaseKeyword

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoUniquePriorityCaseRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 4, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 5
        assert result["message"] == "Use of unique/priority case can overstate case completeness or exclusivity"


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
