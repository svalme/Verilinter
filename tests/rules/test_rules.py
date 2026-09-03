import pytest
from unittest.mock import Mock
import pyslang as sl
from pathlib import Path

from src.pkg.rules.conditional_and_case_statements.default_case import DefaultCaseRule
from src.pkg.rules.sequential_logic.no_always_ff import NoAlwaysFFRule
from src.pkg.rules.latches.no_always_latch import NoAlwaysLatchRule
from src.pkg.rules.sequential_logic.no_blocking_sequential_logic import NoBlockingAssignmentInSequentialRule
from src.pkg.rules.parameters_and_generate_logic.no_case_generate import NoCaseGenerateRule
from src.pkg.rules.conditional_and_case_statements.no_case_inside import NoCaseInsideRule
from src.pkg.rules.assertions_and_verification.no_checker_declaration import NoCheckerDeclarationRule
from src.pkg.rules.simulation_vs_synthesis.no_clocking_declaration import NoClockingDeclarationRule
from src.pkg.rules.simulation_vs_synthesis.no_disable_statement import NoDisableStatementRule
from src.pkg.rules.simulation_vs_synthesis.no_do_while_loop import NoDoWhileLoopRule
from src.pkg.rules.simulation_vs_synthesis.no_event_trigger import NoEventTriggerRule
from src.pkg.rules.simulation_vs_synthesis.no_for_loop import NoForLoopRule
from src.pkg.rules.simulation_vs_synthesis.no_foreach_loop import NoForeachLoopRule
from src.pkg.rules.parameters_and_generate_logic.no_generate_for import NoGenerateForRule
from src.pkg.rules.parameters_and_generate_logic.no_if_generate import NoIfGenerateRule
from src.pkg.rules.simulation_vs_synthesis.no_interface_declaration import NoInterfaceDeclarationRule
from src.pkg.rules.simulation_vs_synthesis.no_modport_declaration import NoModportDeclarationRule
from src.pkg.rules.simulation_vs_synthesis.no_package_declaration import NoPackageDeclarationRule
from src.pkg.rules.simulation_vs_synthesis.no_program_declaration import NoProgramDeclarationRule
from src.pkg.rules.simulation_vs_synthesis.no_task_declaration import NoTaskDeclarationRule
from src.pkg.rules.simulation_vs_synthesis.no_fork_join import NoForkJoinRule
from src.pkg.rules.simulation_vs_synthesis.no_forever_loop import NoForeverLoopRule
from src.pkg.rules.conditional_and_case_statements.no_inside_operator import NoInsideOperatorRule
from src.pkg.rules.simulation_vs_synthesis.no_assign_deassign import NoAssignDeassignRule
from src.pkg.rules.simulation_vs_synthesis.no_final_block import NoFinalBlockRule
from src.pkg.rules.conditional_and_case_statements.no_full_parallel_case import NoFullParallelCaseRule
from src.pkg.rules.simulation_vs_synthesis.no_force_release import NoForceReleaseRule
from src.pkg.rules.simulation_vs_synthesis.no_initial_block import NoInitialBlockRule
from src.pkg.rules.parameters_and_generate_logic.no_defparam import NoDefparamRule
from src.pkg.rules.connectivity_and_hierarchy.no_inout_internal import NoInternalInoutRule
from src.pkg.rules.combinational_logic.no_latch_in_always_comb import NoLatchInAlwaysCombRule
from src.pkg.rules.combinational_logic.no_nonblocking_comb import NoNonBlockingAssignmentInCombRule
from src.pkg.rules.declarations_and_types.no_supply0_supply1 import NoSupply0Supply1Rule
from src.pkg.rules.combinational_logic.no_tranif_rtranif import NoTranifRtranifRule
from src.pkg.rules.combinational_logic.no_tran_rtran import NoTranRtranRule
from src.pkg.rules.declarations_and_types.no_trireg import NoTriregRule
from src.pkg.rules.simulation_vs_synthesis.no_repeat_loop import NoRepeatLoopRule
from src.pkg.rules.simulation_vs_synthesis.no_while_loop import NoWhileLoopRule
from src.pkg.rules.simulation_vs_synthesis.no_wait_statement import NoWaitStatementRule
from src.pkg.rules.conditional_and_case_statements.no_priority_if import NoPriorityIfRule
from src.pkg.rules.conditional_and_case_statements.no_unique0_case import NoUnique0CaseRule
from src.pkg.rules.conditional_and_case_statements.no_unique_if import NoUniqueIfRule
from src.pkg.rules.conditional_and_case_statements.no_unique_priority_case import NoUniquePriorityCaseRule
from src.pkg.rules.declarations_and_types.no_wand_wor import NoWandWorRule
from src.pkg.rules.simulation_vs_synthesis.no_specify_block import NoSpecifyBlockRule
from src.pkg.rules.combinational_logic.no_primitive_declaration import NoPrimitiveDeclarationRule
from src.pkg.rules.combinational_logic.no_gate_primitive import NoGatePrimitiveRule
from src.pkg.rules.connectivity_and_hierarchy.no_alias_statement import NoAliasStatementRule
from src.pkg.rules.connectivity_and_hierarchy.no_bind_directive import NoBindDirectiveRule
from src.pkg.rules.simulation_vs_synthesis.no_delay_control import NoDelayControlRule
from src.pkg.rules.assertions_and_verification.no_immediate_assertion import NoImmediateAssertionRule
from src.pkg.rules.assertions_and_verification.no_concurrent_assertion import NoConcurrentAssertionRule
from src.pkg.rules.simulation_vs_synthesis.no_display_system_task import NoDisplaySystemTaskRule
from src.pkg.rules.simulation_vs_synthesis.no_simulation_control_task import NoSimulationControlTaskRule
from src.pkg.rules.simulation_vs_synthesis.no_class_declaration import NoClassDeclarationRule
from src.pkg.rules.assertions_and_verification.no_covergroup_declaration import NoCovergroupDeclarationRule
from src.pkg.rules.assertions_and_verification.no_sequence_declaration import NoSequenceDeclarationRule
from src.pkg.rules.assertions_and_verification.no_property_declaration import NoPropertyDeclarationRule
from src.pkg.rules.simulation_vs_synthesis.no_function_declaration import NoFunctionDeclarationRule
from src.pkg.rules.declarations_and_types.no_uwire import NoUwireRule
from src.pkg.rules.simulation_vs_synthesis.no_let_declaration import NoLetDeclarationRule
from src.pkg.rules.simulation_vs_synthesis.no_config_declaration import NoConfigDeclarationRule
from src.pkg.rules.assertions_and_verification.no_randsequence import NoRandsequenceRule
from src.pkg.rules.assertions_and_verification.no_expect_restrict_property import NoExpectRestrictPropertyRule
from src.pkg.rules.simulation_vs_synthesis.no_virtual_interface import NoVirtualInterfaceRule
from src.pkg.rules.simulation_vs_synthesis.no_dpi_import_export import NoDpiImportExportRule
from src.pkg.rules.declarations_and_types.no_real_type import NoRealTypeRule
from src.pkg.rules.declarations_and_types.no_string_type import NoStringTypeRule
from src.pkg.rules.declarations_and_types.no_chandle_type import NoChandleTypeRule
from src.pkg.rules.simulation_vs_synthesis.no_random_system_function import NoRandomSystemFunctionRule
from src.pkg.rules.simulation_vs_synthesis.no_time_system_function import NoTimeSystemFunctionRule
from src.pkg.rules.simulation_vs_synthesis.no_vcd_dump_task import NoVcdDumpTaskRule
from src.pkg.rules.simulation_vs_synthesis.no_file_io_system_task import NoFileIoSystemTaskRule
from src.pkg.rules.simulation_vs_synthesis.no_plusargs_system_function import NoPlusargsSystemFunctionRule
from src.pkg.rules.assertions_and_verification.no_assertion_control_task import NoAssertionControlTaskRule
from src.pkg.rules.arrays_and_indexing.no_queue import NoQueueRule
from src.pkg.rules.arrays_and_indexing.no_dynamic_array import NoDynamicArrayRule
from src.pkg.rules.arrays_and_indexing.no_associative_array import NoAssociativeArrayRule
from src.pkg.rules.conditional_and_case_statements.no_unique0_if import NoUnique0IfRule
from src.pkg.rules.combinational_logic.no_switch_primitive import NoSwitchPrimitiveRule
from tests.support.syntax_context_builders import (
    case_context,
    conditional_context,
    continuous_assign_context,
    event_trigger_statement_context,
    primitive_instantiation_context,
    token_vnode,
)
from src.pkg.walk.context import Context, ContextFlag
from src.pkg.vnodes.base_vnode import BaseVNode
from src.pkg.vnodes.token_vnode import TokenVNode

DATA = Path(__file__).parent.parent / "data"


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

    def test_applies_returns_false_for_wildcard_always_star(self, rule: NoBlockingAssignmentInSequentialRule) -> None:
        """Regression test: `always @(*)` is classic Verilog's combinational spelling,
        where `=` is the *correct* assignment style -- ContextFlag.ALWAYS alone does
        not distinguish this from a genuinely edge-triggered plain `always` block, so
        it must not be flagged as a sequential-logic blocking assignment."""
        block_raw, token_raw = _always_block_and_blocking_token(
            """
            module top(input logic a, input logic b, output logic y);
                always @(*) begin
                    y = a & b;
                end
            endmodule
            """
        )
        assert block_raw is not None and token_raw is not None

        block_vnode = Mock(spec=BaseVNode)
        block_vnode.raw = block_raw
        token_vnode_ = Mock(spec=BaseVNode)
        token_vnode_.raw = token_raw

        context = Context().with_flag(ContextFlag.ALWAYS).push(block_vnode)

        assert rule.applies(token_vnode_, context) is False

    def test_applies_returns_false_for_explicit_nonedge_sensitivity_list(
        self, rule: NoBlockingAssignmentInSequentialRule
    ) -> None:
        """Same combinational-style exclusion as the wildcard case, but with an
        explicit non-edge sensitivity list (`always @(a or b)`)."""
        block_raw, token_raw = _always_block_and_blocking_token(
            """
            module top(input logic a, input logic b, output logic y);
                always @(a or b) begin
                    y = a & b;
                end
            endmodule
            """
        )
        assert block_raw is not None and token_raw is not None

        block_vnode = Mock(spec=BaseVNode)
        block_vnode.raw = block_raw
        token_vnode_ = Mock(spec=BaseVNode)
        token_vnode_.raw = token_raw

        context = Context().with_flag(ContextFlag.ALWAYS).push(block_vnode)

        assert rule.applies(token_vnode_, context) is False

    def test_applies_returns_true_for_edge_sensitive_always_block(self, rule: NoBlockingAssignmentInSequentialRule) -> None:
        """An edge-triggered plain `always @(posedge clk)` is real sequential logic
        and must still be flagged when it uses a blocking assignment."""
        block_raw, token_raw = _always_block_and_blocking_token(
            """
            module top(input logic clk, input logic d, output logic q);
                always @(posedge clk) begin
                    q = d;
                end
            endmodule
            """
        )
        assert block_raw is not None and token_raw is not None

        block_vnode = Mock(spec=BaseVNode)
        block_vnode.raw = block_raw
        token_vnode_ = Mock(spec=BaseVNode)
        token_vnode_.raw = token_raw

        context = Context().with_flag(ContextFlag.ALWAYS).push(block_vnode)

        assert rule.applies(token_vnode_, context) is True

    def test_report_returns_correct_format(self, rule: NoBlockingAssignmentInSequentialRule, mock_vnode: Mock) -> None:
        """Test that report() returns the correct diagnostic format."""
        mock_vnode.location = {"line": 15, "col": 8}
        result = rule.report(mock_vnode)

        assert result["line"] == 15
        assert result["col"] == 8
        assert result["message"] == "Blocking assignment used in sequential logic"


def _always_block_and_token(src: str, token_kind: object) -> tuple[object, object]:
    """Parse `src` and return (first AlwaysBlock raw node, first raw token of `token_kind`)."""
    tree = sl.SyntaxTree.fromText(src)
    block: object = None
    token: object = None

    def walk(node: object) -> None:
        nonlocal block, token
        if block is None and getattr(node, "kind", None) == sl.SyntaxKind.AlwaysBlock:
            block = node
        if token is None and isinstance(node, sl.Token) and node.kind == token_kind:
            token = node
        if hasattr(node, "__iter__"):
            for child in node:
                walk(child)

    walk(tree.root)
    return block, token


def _always_block_and_nonblocking_token(src: str) -> tuple[object, object]:
    return _always_block_and_token(src, sl.TokenKind.LessThanEquals)


def _always_block_and_blocking_token(src: str) -> tuple[object, object]:
    return _always_block_and_token(src, sl.TokenKind.Equals)


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

    def test_applies_returns_true_for_wildcard_always_star(self, rule: NoNonBlockingAssignmentInCombRule) -> None:
        """Plain `always @(*)` is classic Verilog's combinational spelling and has no
        ALWAYS_COMB flag of its own -- this is the gap the widened check closes."""
        block_raw, token_raw = _always_block_and_nonblocking_token(
            """
            module top(input logic a, input logic b, output logic y);
                always @(*) begin
                    y <= a & b;
                end
            endmodule
            """
        )
        assert block_raw is not None and token_raw is not None

        block_vnode = Mock(spec=BaseVNode)
        block_vnode.raw = block_raw
        token_vnode_ = Mock(spec=BaseVNode)
        token_vnode_.raw = token_raw

        context = Context().push(block_vnode)

        assert rule.applies(token_vnode_, context) is True

    def test_applies_returns_true_for_explicit_nonedge_sensitivity_list(
        self, rule: NoNonBlockingAssignmentInCombRule
    ) -> None:
        """`always @(a or b)` (no posedge/negedge) is the same combinational-style
        block as `always @(*)`, just with an explicit list instead of a wildcard."""
        block_raw, token_raw = _always_block_and_nonblocking_token(
            """
            module top(input logic a, input logic b, output logic y);
                always @(a or b) begin
                    y <= a & b;
                end
            endmodule
            """
        )
        assert block_raw is not None and token_raw is not None

        block_vnode = Mock(spec=BaseVNode)
        block_vnode.raw = block_raw
        token_vnode_ = Mock(spec=BaseVNode)
        token_vnode_.raw = token_raw

        context = Context().push(block_vnode)

        assert rule.applies(token_vnode_, context) is True

    def test_applies_returns_false_for_edge_sensitive_always_block(self, rule: NoNonBlockingAssignmentInCombRule) -> None:
        """An edge-triggered plain `always @(posedge clk)` is real sequential logic
        and must stay unaffected by the combinational-style widening."""
        block_raw, token_raw = _always_block_and_nonblocking_token(
            """
            module top(input logic clk, input logic d, output logic q);
                always @(posedge clk) begin
                    q <= d;
                end
            endmodule
            """
        )
        assert block_raw is not None and token_raw is not None

        block_vnode = Mock(spec=BaseVNode)
        block_vnode.raw = block_raw
        token_vnode_ = Mock(spec=BaseVNode)
        token_vnode_.raw = token_raw

        context = Context().push(block_vnode)

        assert rule.applies(token_vnode_, context) is False

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


class TestNoRepeatLoopRule:
    @pytest.fixture
    def rule(self) -> NoRepeatLoopRule:
        return NoRepeatLoopRule()

    def test_rule_has_correct_code(self, rule: NoRepeatLoopRule) -> None:
        assert rule.code == "NO_REPEAT_LOOP"

    def test_rule_has_correct_message(self, rule: NoRepeatLoopRule) -> None:
        assert rule.message == "Use of repeat loops is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_repeat_keyword(self, rule: NoRepeatLoopRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.RepeatKeyword)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_while_keyword(self, rule: NoRepeatLoopRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.WhileKeyword)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoRepeatLoopRule, mock_vnode: Mock) -> None:
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
        mock_vnode = token_vnode(sl.TokenKind.WhileKeyword)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_wait_keyword(self, rule: NoWhileLoopRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.WaitKeyword)

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_false_for_do_while_trailing_while(self, rule: NoWhileLoopRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.WhileKeyword)
        do_while_vnode = Mock(spec=BaseVNode)
        do_while_vnode.raw = Mock()
        do_while_vnode.raw.kind = sl.SyntaxKind.DoWhileStatement
        context = Context().push(do_while_vnode)

        assert rule.applies(mock_vnode, context) is False

    def test_report_returns_correct_format(self, rule: NoWhileLoopRule, mock_vnode: Mock) -> None:
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
        mock_vnode = token_vnode(sl.TokenKind.ForeachKeyword)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_for_keyword(self, rule: NoForeachLoopRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.ForKeyword)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoForeachLoopRule, mock_vnode: Mock) -> None:
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
        mock_vnode = token_vnode(sl.TokenKind.DoKeyword)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_while_keyword(self, rule: NoDoWhileLoopRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.WhileKeyword)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoDoWhileLoopRule, mock_vnode: Mock) -> None:
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
        mock_vnode = token_vnode(sl.TokenKind.ForKeyword)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_foreach_keyword(self, rule: NoForLoopRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.ForeachKeyword)

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_false_for_generate_for_token(self, rule: NoForLoopRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.ForKeyword)
        loop_generate_vnode = Mock(spec=BaseVNode)
        loop_generate_vnode.raw = Mock()
        loop_generate_vnode.raw.kind = sl.SyntaxKind.LoopGenerate
        context = Context().push(loop_generate_vnode)

        assert rule.applies(mock_vnode, context) is False

    def test_report_returns_correct_format(self, rule: NoForLoopRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 3, "col": 11}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 11
        assert result["message"] == "Use of for loops is discouraged in synthesizable RTL"


class TestNoGenerateForRule:
    @pytest.fixture
    def rule(self) -> NoGenerateForRule:
        return NoGenerateForRule()

    def test_rule_has_correct_code(self, rule: NoGenerateForRule) -> None:
        assert rule.code == "NO_GENERATE_FOR"

    def test_rule_has_correct_message(self, rule: NoGenerateForRule) -> None:
        assert rule.message == "Use of generate-for loops can make structural intent harder to follow"

    def test_applies_returns_true_for_loop_generate_node(self, rule: NoGenerateForRule) -> None:
        tree = sl.SyntaxTree.fromFile(str(DATA / "generate_for.v"))

        def walk(node):
            if isinstance(node, sl.LoopGenerateSyntax):
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

    def test_applies_returns_false_for_procedural_for_statement(self, rule: NoGenerateForRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ForLoopStatement

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoGenerateForRule, mock_vnode: Mock) -> None:
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
        tree = sl.SyntaxTree.fromFile(str(DATA / "if_generate.v"))

        def walk(node):
            if isinstance(node, sl.IfGenerateSyntax):
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

    def test_applies_returns_false_for_procedural_if_statement(self, rule: NoIfGenerateRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ConditionalStatement

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoIfGenerateRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 4, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 5
        assert result["message"] == "Use of if-generate can make structural intent harder to follow"


class TestNoTaskDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoTaskDeclarationRule:
        return NoTaskDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoTaskDeclarationRule) -> None:
        assert rule.code == "NO_TASK_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoTaskDeclarationRule) -> None:
        assert rule.message == "Use of task declarations is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_task_declaration_node(self, rule: NoTaskDeclarationRule) -> None:
        tree = sl.SyntaxTree.fromFile(str(DATA / "task_declaration.v"))

        def walk(node):
            if getattr(node, "kind", None) == sl.SyntaxKind.TaskDeclaration:
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

    def test_applies_returns_false_for_function_declaration_node(self, rule: NoTaskDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.FunctionDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoTaskDeclarationRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 3, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 3
        assert result["message"] == "Use of task declarations is discouraged in synthesizable RTL"


class TestNoProgramDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoProgramDeclarationRule:
        return NoProgramDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoProgramDeclarationRule) -> None:
        assert rule.code == "NO_PROGRAM_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoProgramDeclarationRule) -> None:
        assert rule.message == "Use of program declarations is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_program_declaration_node(self, rule: NoProgramDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ProgramDeclaration

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_module_declaration_node(self, rule: NoProgramDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ModuleDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoProgramDeclarationRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 1, "col": 1}
        result = rule.report(mock_vnode)

        assert result["line"] == 1
        assert result["col"] == 1
        assert result["message"] == "Use of program declarations is discouraged in synthesizable RTL"


class TestNoClockingDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoClockingDeclarationRule:
        return NoClockingDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoClockingDeclarationRule) -> None:
        assert rule.code == "NO_CLOCKING_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoClockingDeclarationRule) -> None:
        assert rule.message == "Use of clocking declarations is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_clocking_declaration_node(self, rule: NoClockingDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ClockingDeclaration

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_program_declaration_node(self, rule: NoClockingDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ProgramDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoClockingDeclarationRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of clocking declarations is discouraged in synthesizable RTL"


class TestNoCheckerDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoCheckerDeclarationRule:
        return NoCheckerDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoCheckerDeclarationRule) -> None:
        assert rule.code == "NO_CHECKER_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoCheckerDeclarationRule) -> None:
        assert rule.message == "Use of checker declarations is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_checker_declaration_node(self, rule: NoCheckerDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.CheckerDeclaration

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_clocking_declaration_node(self, rule: NoCheckerDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ClockingDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoCheckerDeclarationRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of checker declarations is discouraged in synthesizable RTL"


class TestNoInterfaceDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoInterfaceDeclarationRule:
        return NoInterfaceDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoInterfaceDeclarationRule) -> None:
        assert rule.code == "NO_INTERFACE_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoInterfaceDeclarationRule) -> None:
        assert rule.message == "Use of interface declarations is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_interface_declaration_node(self, rule: NoInterfaceDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.InterfaceDeclaration

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_program_declaration_node(self, rule: NoInterfaceDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ProgramDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoInterfaceDeclarationRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 1, "col": 1}
        result = rule.report(mock_vnode)

        assert result["line"] == 1
        assert result["col"] == 1
        assert result["message"] == "Use of interface declarations is discouraged in synthesizable RTL"


class TestNoModportDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoModportDeclarationRule:
        return NoModportDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoModportDeclarationRule) -> None:
        assert rule.code == "NO_MODPORT_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoModportDeclarationRule) -> None:
        assert rule.message == "Use of modport declarations is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_modport_declaration_node(self, rule: NoModportDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ModportDeclaration

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_interface_declaration_node(self, rule: NoModportDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.InterfaceDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoModportDeclarationRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 1, "col": 1}
        result = rule.report(mock_vnode)

        assert result["line"] == 1
        assert result["col"] == 1
        assert result["message"] == "Use of modport declarations is discouraged in synthesizable RTL"


class TestNoPackageDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoPackageDeclarationRule:
        return NoPackageDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoPackageDeclarationRule) -> None:
        assert rule.code == "NO_PACKAGE_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoPackageDeclarationRule) -> None:
        assert rule.message == "Use of package declarations is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_package_declaration_node(self, rule: NoPackageDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.PackageDeclaration

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_program_declaration_node(self, rule: NoPackageDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ProgramDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoPackageDeclarationRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 1, "col": 1}
        result = rule.report(mock_vnode)

        assert result["line"] == 1
        assert result["col"] == 1
        assert result["message"] == "Use of package declarations is discouraged in synthesizable RTL"


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

    def test_applies_returns_false_for_disable_keyword_inside_disable_iff(self, rule: NoDisableStatementRule) -> None:
        """`disable iff (...)` (a property's clock/reset qualifier) reuses the same
        DisableKeyword token as an ordinary `disable <label>;` statement, but is a
        different grammatical construct (DisableIffSyntax) and not a disable
        statement at all."""
        mock_vnode = token_vnode(sl.TokenKind.DisableKeyword)
        ancestor = Mock(spec=BaseVNode)
        ancestor.raw = Mock()
        ancestor.raw.kind = sl.SyntaxKind.DisableIff
        ctx = Context().push(ancestor)

        assert rule.applies(mock_vnode, ctx) is False

    def test_report_returns_correct_format(self, rule: NoDisableStatementRule, mock_vnode: Mock) -> None:
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
        mock_vnode = token_vnode(sl.TokenKind.MinusArrow)

        assert rule.applies(mock_vnode, event_trigger_statement_context()) is True

    def test_applies_returns_true_for_nonblocking_event_trigger(self, rule: NoEventTriggerRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.MinusDoubleArrow)

        assert rule.applies(mock_vnode, event_trigger_statement_context(nonblocking=True)) is True

    def test_applies_returns_false_for_greater_than(self, rule: NoEventTriggerRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.GreaterThan)

        assert rule.applies(mock_vnode, event_trigger_statement_context()) is False

    def test_applies_returns_false_for_minus_arrow_used_as_implication_operator(self, rule: NoEventTriggerRule) -> None:
        """`->` is also the logical-implication operator in ordinary expressions
        (`a -> b`), not just an event-trigger statement (`-> done;`). Outside a
        BlockingEventTriggerStatement/NonblockingEventTriggerStatement ancestor, it
        must not be flagged."""
        mock_vnode = token_vnode(sl.TokenKind.MinusArrow)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoEventTriggerRule, mock_vnode: Mock) -> None:
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
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ParallelBlockStatement

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_sequential_block(self, rule: NoForkJoinRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.SequentialBlockStatement

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoForkJoinRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 3, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 3
        assert result["message"] == "Use of fork/join style parallel blocks is discouraged in synthesizable RTL"


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


class TestNoUnique0IfRule:
    @pytest.fixture
    def rule(self) -> NoUnique0IfRule:
        return NoUnique0IfRule()

    def test_rule_has_correct_code(self, rule: NoUnique0IfRule) -> None:
        assert rule.code == "NO_UNIQUE0_IF"

    def test_rule_has_correct_message(self, rule: NoUnique0IfRule) -> None:
        assert rule.message == "Use of unique0 if can overstate branch exclusivity assumptions"

    def test_applies_returns_true_for_unique0_if(self, rule: NoUnique0IfRule) -> None:
        mock_vnode = token_vnode(getattr(sl.TokenKind, "Unique0Keyword", None))
        context = conditional_context(unique_or_priority="unique0")

        assert rule.applies(mock_vnode, context) is True

    def test_applies_returns_false_for_unique0_case(self, rule: NoUnique0IfRule) -> None:
        mock_vnode = token_vnode(getattr(sl.TokenKind, "Unique0Keyword", None))
        context = case_context(unique_or_priority="unique0")

        assert rule.applies(mock_vnode, context) is False

    def test_applies_returns_false_for_unique_if(self, rule: NoUnique0IfRule) -> None:
        mock_vnode = token_vnode(sl.TokenKind.UniqueKeyword)
        context = conditional_context(unique_or_priority="unique")

        assert rule.applies(mock_vnode, context) is False

    def test_report_returns_correct_format(self, rule: NoUnique0IfRule, mock_vnode: Mock) -> None:
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

    def test_applies_returns_false_for_assign_keyword_inside_continuous_assign(self, rule: NoAssignDeassignRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.AssignKeyword

        assert rule.applies(mock_vnode, continuous_assign_context()) is False

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


class TestNoSpecifyBlockRule:
    @pytest.fixture
    def rule(self) -> NoSpecifyBlockRule:
        return NoSpecifyBlockRule()

    def test_rule_has_correct_code(self, rule: NoSpecifyBlockRule) -> None:
        assert rule.code == "NO_SPECIFY_BLOCK"

    def test_rule_has_correct_message(self, rule: NoSpecifyBlockRule) -> None:
        assert rule.message == "Use of specify blocks is discouraged in synthesizable RTL; pin-to-pin timing modeling is not synthesizable"

    def test_applies_returns_true_for_specify_block_node(self, rule: NoSpecifyBlockRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.SpecifyBlock

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoSpecifyBlockRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ProgramDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoSpecifyBlockRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 4, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 5
        assert result["message"] == "Use of specify blocks is discouraged in synthesizable RTL; pin-to-pin timing modeling is not synthesizable"


class TestNoPrimitiveDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoPrimitiveDeclarationRule:
        return NoPrimitiveDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoPrimitiveDeclarationRule) -> None:
        assert rule.code == "NO_PRIMITIVE_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoPrimitiveDeclarationRule) -> None:
        assert rule.message == "Use of user-defined primitive (UDP) declarations is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_udp_declaration_node(self, rule: NoPrimitiveDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.UdpDeclaration

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoPrimitiveDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.TaskDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoPrimitiveDeclarationRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 1, "col": 1}
        result = rule.report(mock_vnode)

        assert result["line"] == 1
        assert result["col"] == 1
        assert result["message"] == "Use of user-defined primitive (UDP) declarations is discouraged in synthesizable RTL"


class TestNoGatePrimitiveRule:
    @pytest.fixture
    def rule(self) -> NoGatePrimitiveRule:
        return NoGatePrimitiveRule()

    def test_rule_has_correct_code(self, rule: NoGatePrimitiveRule) -> None:
        assert rule.code == "NO_GATE_PRIMITIVE"

    def test_rule_has_correct_message(self, rule: NoGatePrimitiveRule) -> None:
        assert rule.message == "Use of gate-level primitives is discouraged in RTL; prefer behavioral or operator-level modeling"

    def test_applies_returns_true_for_and_keyword_inside_primitive_instantiation(self, rule: NoGatePrimitiveRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.AndKeyword

        assert rule.applies(mock_vnode, primitive_instantiation_context()) is True

    def test_applies_returns_true_for_bufif0_keyword_inside_primitive_instantiation(self, rule: NoGatePrimitiveRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.BufIf0Keyword

        assert rule.applies(mock_vnode, primitive_instantiation_context()) is True

    def test_applies_returns_false_for_other_token(self, rule: NoGatePrimitiveRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.InitialKeyword

        assert rule.applies(mock_vnode, primitive_instantiation_context()) is False

    def test_applies_returns_false_for_or_keyword_outside_primitive_instantiation(self, rule: NoGatePrimitiveRule) -> None:
        """`or` is also the separator in classic event/sensitivity lists
        (`@(posedge clk or negedge rst_n)`), which shares the same TokenKind.OrKeyword
        as the `or` gate-primitive keyword but is not a gate instantiation at all."""
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.OrKeyword

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_true_for_or_keyword_inside_primitive_instantiation(self, rule: NoGatePrimitiveRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.OrKeyword

        assert rule.applies(mock_vnode, primitive_instantiation_context()) is True

    def test_report_returns_correct_format(self, rule: NoGatePrimitiveRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 5
        assert result["message"] == "Use of gate-level primitives is discouraged in RTL; prefer behavioral or operator-level modeling"


class TestNoSwitchPrimitiveRule:
    @pytest.fixture
    def rule(self) -> NoSwitchPrimitiveRule:
        return NoSwitchPrimitiveRule()

    def test_rule_has_correct_code(self, rule: NoSwitchPrimitiveRule) -> None:
        assert rule.code == "NO_SWITCH_PRIMITIVE"

    def test_rule_has_correct_message(self, rule: NoSwitchPrimitiveRule) -> None:
        assert rule.message == "Use of switch-level primitives is discouraged in RTL; prefer behavioral or operator-level modeling"

    def test_applies_returns_true_for_cmos_keyword_inside_primitive_instantiation(self, rule: NoSwitchPrimitiveRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.CmosKeyword

        assert rule.applies(mock_vnode, primitive_instantiation_context()) is True

    def test_applies_returns_true_for_pullup_keyword_inside_primitive_instantiation(self, rule: NoSwitchPrimitiveRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.PullUpKeyword

        assert rule.applies(mock_vnode, primitive_instantiation_context()) is True

    def test_applies_returns_false_for_other_token(self, rule: NoSwitchPrimitiveRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.InitialKeyword

        assert rule.applies(mock_vnode, primitive_instantiation_context()) is False

    def test_applies_returns_false_for_cmos_keyword_outside_primitive_instantiation(self, rule: NoSwitchPrimitiveRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.CmosKeyword

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_false_for_gate_primitive_token(self, rule: NoSwitchPrimitiveRule) -> None:
        """A gate-level `and`/`or`/... keyword is `NO_GATE_PRIMITIVE`'s concern, not this rule's."""
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.AndKeyword

        assert rule.applies(mock_vnode, primitive_instantiation_context()) is False

    def test_report_returns_correct_format(self, rule: NoSwitchPrimitiveRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 5
        assert result["message"] == "Use of switch-level primitives is discouraged in RTL; prefer behavioral or operator-level modeling"


class TestNoAliasStatementRule:
    @pytest.fixture
    def rule(self) -> NoAliasStatementRule:
        return NoAliasStatementRule()

    def test_rule_has_correct_code(self, rule: NoAliasStatementRule) -> None:
        assert rule.code == "NO_ALIAS_STATEMENT"

    def test_rule_has_correct_message(self, rule: NoAliasStatementRule) -> None:
        assert rule.message == "Use of alias statements is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_net_alias_node(self, rule: NoAliasStatementRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.NetAlias

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoAliasStatementRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.BindDirective

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoAliasStatementRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 3, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 3
        assert result["col"] == 5
        assert result["message"] == "Use of alias statements is discouraged in synthesizable RTL"


class TestNoBindDirectiveRule:
    @pytest.fixture
    def rule(self) -> NoBindDirectiveRule:
        return NoBindDirectiveRule()

    def test_rule_has_correct_code(self, rule: NoBindDirectiveRule) -> None:
        assert rule.code == "NO_BIND_DIRECTIVE"

    def test_rule_has_correct_message(self, rule: NoBindDirectiveRule) -> None:
        assert rule.message == "Use of bind directives is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_bind_directive_node(self, rule: NoBindDirectiveRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.BindDirective

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoBindDirectiveRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.NetAlias

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoBindDirectiveRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 5, "col": 1}
        result = rule.report(mock_vnode)

        assert result["line"] == 5
        assert result["col"] == 1
        assert result["message"] == "Use of bind directives is discouraged in synthesizable RTL"


class TestNoDelayControlRule:
    @pytest.fixture
    def rule(self) -> NoDelayControlRule:
        return NoDelayControlRule()

    def test_rule_has_correct_code(self, rule: NoDelayControlRule) -> None:
        assert rule.code == "NO_DELAY_CONTROL"

    def test_rule_has_correct_message(self, rule: NoDelayControlRule) -> None:
        assert rule.message == "Use of delay controls (#delay) is discouraged in synthesizable RTL; delays are simulation-only timing"

    def test_applies_returns_true_for_delay_control_node(self, rule: NoDelayControlRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.DelayControl

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_delay3_node(self, rule: NoDelayControlRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.Delay3

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoDelayControlRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ContinuousAssign

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoDelayControlRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 12}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 12
        assert result["message"] == "Use of delay controls (#delay) is discouraged in synthesizable RTL; delays are simulation-only timing"


class TestNoImmediateAssertionRule:
    @pytest.fixture
    def rule(self) -> NoImmediateAssertionRule:
        return NoImmediateAssertionRule()

    def test_rule_has_correct_code(self, rule: NoImmediateAssertionRule) -> None:
        assert rule.code == "NO_IMMEDIATE_ASSERTION"

    def test_rule_has_correct_message(self, rule: NoImmediateAssertionRule) -> None:
        assert rule.message == "Use of immediate assertions (assert/assume/cover) is discouraged in synthesizable RTL; assertions belong in verification, not design"

    def test_applies_returns_true_for_immediate_assert_statement(self, rule: NoImmediateAssertionRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ImmediateAssertStatement

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_immediate_cover_statement(self, rule: NoImmediateAssertionRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ImmediateCoverStatement

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_concurrent_assertion(self, rule: NoImmediateAssertionRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.AssertPropertyStatement

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoImmediateAssertionRule, mock_vnode: Mock) -> None:
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
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.AssertPropertyStatement

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_cover_property_statement(self, rule: NoConcurrentAssertionRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.CoverPropertyStatement

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_immediate_assertion(self, rule: NoConcurrentAssertionRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ImmediateAssertStatement

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoConcurrentAssertionRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 5
        assert result["message"] == "Use of concurrent assertions (assert/assume/cover property) is discouraged in synthesizable RTL; assertions belong in verification, not design"


def _system_name_vnode(name: str) -> Mock:
    mock_vnode = Mock(spec=BaseVNode)
    mock_vnode.raw = Mock(spec=sl.SystemNameSyntax)
    mock_vnode.raw.systemIdentifier = Mock()
    mock_vnode.raw.systemIdentifier.valueText = name
    return mock_vnode


class TestNoDisplaySystemTaskRule:
    @pytest.fixture
    def rule(self) -> NoDisplaySystemTaskRule:
        return NoDisplaySystemTaskRule()

    def test_rule_has_correct_code(self, rule: NoDisplaySystemTaskRule) -> None:
        assert rule.code == "NO_DISPLAY_SYSTEM_TASK"

    def test_rule_has_correct_message(self, rule: NoDisplaySystemTaskRule) -> None:
        assert rule.message == "Use of $display/$write/$monitor/$strobe-family system tasks is discouraged in synthesizable RTL; these are simulation-only debug output"

    def test_applies_returns_true_for_display(self, rule: NoDisplaySystemTaskRule) -> None:
        assert rule.applies(_system_name_vnode("$display"), Context()) is True

    def test_applies_returns_true_for_monitorh(self, rule: NoDisplaySystemTaskRule) -> None:
        assert rule.applies(_system_name_vnode("$monitorh"), Context()) is True

    def test_applies_returns_false_for_unrelated_system_task(self, rule: NoDisplaySystemTaskRule) -> None:
        assert rule.applies(_system_name_vnode("$finish"), Context()) is False

    def test_applies_returns_false_for_non_system_name_node(self, rule: NoDisplaySystemTaskRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ProgramDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoDisplaySystemTaskRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 4, "col": 9}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 9
        assert result["message"] == "Use of $display/$write/$monitor/$strobe-family system tasks is discouraged in synthesizable RTL; these are simulation-only debug output"


class TestNoSimulationControlTaskRule:
    @pytest.fixture
    def rule(self) -> NoSimulationControlTaskRule:
        return NoSimulationControlTaskRule()

    def test_rule_has_correct_code(self, rule: NoSimulationControlTaskRule) -> None:
        assert rule.code == "NO_SIMULATION_CONTROL_TASK"

    def test_rule_has_correct_message(self, rule: NoSimulationControlTaskRule) -> None:
        assert rule.message == "Use of $stop/$finish is discouraged in synthesizable RTL; these are simulation-only control tasks"

    def test_applies_returns_true_for_stop(self, rule: NoSimulationControlTaskRule) -> None:
        assert rule.applies(_system_name_vnode("$stop"), Context()) is True

    def test_applies_returns_true_for_finish(self, rule: NoSimulationControlTaskRule) -> None:
        assert rule.applies(_system_name_vnode("$finish"), Context()) is True

    def test_applies_returns_false_for_unrelated_system_task(self, rule: NoSimulationControlTaskRule) -> None:
        assert rule.applies(_system_name_vnode("$display"), Context()) is False

    def test_applies_returns_false_for_non_system_name_node(self, rule: NoSimulationControlTaskRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ProgramDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoSimulationControlTaskRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 7, "col": 9}
        result = rule.report(mock_vnode)

        assert result["line"] == 7
        assert result["col"] == 9
        assert result["message"] == "Use of $stop/$finish is discouraged in synthesizable RTL; these are simulation-only control tasks"


class TestNoClassDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoClassDeclarationRule:
        return NoClassDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoClassDeclarationRule) -> None:
        assert rule.code == "NO_CLASS_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoClassDeclarationRule) -> None:
        assert rule.message == "Use of class declarations is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_class_declaration_node(self, rule: NoClassDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ClassDeclaration

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoClassDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.InterfaceDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoClassDeclarationRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 1, "col": 1}
        result = rule.report(mock_vnode)

        assert result["line"] == 1
        assert result["col"] == 1
        assert result["message"] == "Use of class declarations is discouraged in synthesizable RTL"


class TestNoCovergroupDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoCovergroupDeclarationRule:
        return NoCovergroupDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoCovergroupDeclarationRule) -> None:
        assert rule.code == "NO_COVERGROUP_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoCovergroupDeclarationRule) -> None:
        assert rule.message == "Use of covergroup declarations is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_covergroup_declaration_node(self, rule: NoCovergroupDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.CovergroupDeclaration

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoCovergroupDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ClassDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoCovergroupDeclarationRule, mock_vnode: Mock) -> None:
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
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.SequenceDeclaration

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_property_declaration_node(self, rule: NoSequenceDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.PropertyDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoSequenceDeclarationRule, mock_vnode: Mock) -> None:
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
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.PropertyDeclaration

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_sequence_declaration_node(self, rule: NoPropertyDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.SequenceDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_false_for_assert_property_statement(self, rule: NoPropertyDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.AssertPropertyStatement

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoPropertyDeclarationRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of property declarations is discouraged in synthesizable RTL"


class TestNoFunctionDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoFunctionDeclarationRule:
        return NoFunctionDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoFunctionDeclarationRule) -> None:
        assert rule.code == "NO_FUNCTION_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoFunctionDeclarationRule) -> None:
        assert rule.message == "Use of function declarations is discouraged in this restricted RTL subset"

    def test_applies_returns_true_for_function_declaration_node(self, rule: NoFunctionDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.FunctionDeclaration

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_task_declaration_node(self, rule: NoFunctionDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.TaskDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoFunctionDeclarationRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of function declarations is discouraged in this restricted RTL subset"


class TestNoUwireRule:
    @pytest.fixture
    def rule(self) -> NoUwireRule:
        return NoUwireRule()

    def test_rule_has_correct_code(self, rule: NoUwireRule) -> None:
        assert rule.code == "NO_UWIRE"

    def test_rule_has_correct_message(self, rule: NoUwireRule) -> None:
        assert rule.message == "Use of uwire is discouraged in RTL; prefer explicit wire/tri declarations"

    def test_applies_returns_true_for_uwire_keyword(self, rule: NoUwireRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.UWireKeyword

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_wand_keyword(self, rule: NoUwireRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.TokenKind.WAndKeyword

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoUwireRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of uwire is discouraged in RTL; prefer explicit wire/tri declarations"


class TestNoLetDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoLetDeclarationRule:
        return NoLetDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoLetDeclarationRule) -> None:
        assert rule.code == "NO_LET_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoLetDeclarationRule) -> None:
        assert rule.message == "Use of let declarations is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_let_declaration_node(self, rule: NoLetDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.LetDeclaration

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoLetDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.FunctionDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoLetDeclarationRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of let declarations is discouraged in synthesizable RTL"


class TestNoConfigDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoConfigDeclarationRule:
        return NoConfigDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoConfigDeclarationRule) -> None:
        assert rule.code == "NO_CONFIG_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoConfigDeclarationRule) -> None:
        assert rule.message == "Use of config declarations is discouraged in synthesizable RTL; library/config binding is a compilation-flow concern, not design intent"

    def test_applies_returns_true_for_config_declaration_node(self, rule: NoConfigDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ConfigDeclaration

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoConfigDeclarationRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.PackageDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoConfigDeclarationRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of config declarations is discouraged in synthesizable RTL; library/config binding is a compilation-flow concern, not design intent"


class TestNoRandsequenceRule:
    @pytest.fixture
    def rule(self) -> NoRandsequenceRule:
        return NoRandsequenceRule()

    def test_rule_has_correct_code(self, rule: NoRandsequenceRule) -> None:
        assert rule.code == "NO_RANDSEQUENCE"

    def test_rule_has_correct_message(self, rule: NoRandsequenceRule) -> None:
        assert rule.message == "Use of randsequence blocks is discouraged in synthesizable RTL; randsequence is a verification-oriented control construct"

    def test_applies_returns_true_for_randsequence_statement_node(self, rule: NoRandsequenceRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.RandSequenceStatement

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoRandsequenceRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ForeverStatement

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoRandsequenceRule, mock_vnode: Mock) -> None:
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
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ExpectPropertyStatement

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_restrict_property_statement(self, rule: NoExpectRestrictPropertyRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.RestrictPropertyStatement

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_assert_property_statement(self, rule: NoExpectRestrictPropertyRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.AssertPropertyStatement

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoExpectRestrictPropertyRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of expect/restrict property statements is discouraged in synthesizable RTL; assertions belong in verification, not design"


class TestNoVirtualInterfaceRule:
    @pytest.fixture
    def rule(self) -> NoVirtualInterfaceRule:
        return NoVirtualInterfaceRule()

    def test_rule_has_correct_code(self, rule: NoVirtualInterfaceRule) -> None:
        assert rule.code == "NO_VIRTUAL_INTERFACE"

    def test_rule_has_correct_message(self, rule: NoVirtualInterfaceRule) -> None:
        assert rule.message == "Use of virtual interface declarations is discouraged in synthesizable RTL; virtual interfaces are a testbench-only construct"

    def test_applies_returns_true_for_virtual_interface_type_node(self, rule: NoVirtualInterfaceRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.VirtualInterfaceType

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_interface_declaration_node(self, rule: NoVirtualInterfaceRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.InterfaceDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoVirtualInterfaceRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of virtual interface declarations is discouraged in synthesizable RTL; virtual interfaces are a testbench-only construct"


class TestNoDpiImportExportRule:
    @pytest.fixture
    def rule(self) -> NoDpiImportExportRule:
        return NoDpiImportExportRule()

    def test_rule_has_correct_code(self, rule: NoDpiImportExportRule) -> None:
        assert rule.code == "NO_DPI_IMPORT_EXPORT"

    def test_rule_has_correct_message(self, rule: NoDpiImportExportRule) -> None:
        assert rule.message == "Use of DPI import/export declarations is discouraged in synthesizable RTL; DPI is a simulation/foreign-code bridge"

    def test_applies_returns_true_for_dpi_import_node(self, rule: NoDpiImportExportRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.DPIImport

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_dpi_export_node(self, rule: NoDpiImportExportRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.DPIExport

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoDpiImportExportRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.FunctionDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoDpiImportExportRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of DPI import/export declarations is discouraged in synthesizable RTL; DPI is a simulation/foreign-code bridge"


class TestNoRealTypeRule:
    @pytest.fixture
    def rule(self) -> NoRealTypeRule:
        return NoRealTypeRule()

    def test_rule_has_correct_code(self, rule: NoRealTypeRule) -> None:
        assert rule.code == "NO_REAL_TYPE"

    def test_rule_has_correct_message(self, rule: NoRealTypeRule) -> None:
        assert rule.message == "Use of real/shortreal/realtime types is discouraged in synthesizable RTL; floating-point types are not synthesizable"

    def test_applies_returns_true_for_real_type_node(self, rule: NoRealTypeRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.RealType

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_shortreal_type_node(self, rule: NoRealTypeRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ShortRealType

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_realtime_type_node(self, rule: NoRealTypeRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.RealTimeType

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_string_type_node(self, rule: NoRealTypeRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.StringType

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoRealTypeRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of real/shortreal/realtime types is discouraged in synthesizable RTL; floating-point types are not synthesizable"


class TestNoStringTypeRule:
    @pytest.fixture
    def rule(self) -> NoStringTypeRule:
        return NoStringTypeRule()

    def test_rule_has_correct_code(self, rule: NoStringTypeRule) -> None:
        assert rule.code == "NO_STRING_TYPE"

    def test_rule_has_correct_message(self, rule: NoStringTypeRule) -> None:
        assert rule.message == "Use of string type is discouraged in synthesizable RTL; string is a simulation-only data type"

    def test_applies_returns_true_for_string_type_node(self, rule: NoStringTypeRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.StringType

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_real_type_node(self, rule: NoStringTypeRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.RealType

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoStringTypeRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of string type is discouraged in synthesizable RTL; string is a simulation-only data type"


class TestNoChandleTypeRule:
    @pytest.fixture
    def rule(self) -> NoChandleTypeRule:
        return NoChandleTypeRule()

    def test_rule_has_correct_code(self, rule: NoChandleTypeRule) -> None:
        assert rule.code == "NO_CHANDLE_TYPE"

    def test_rule_has_correct_message(self, rule: NoChandleTypeRule) -> None:
        assert rule.message == "Use of chandle type is discouraged in synthesizable RTL; chandle is a DPI-only handle type"

    def test_applies_returns_true_for_chandle_type_node(self, rule: NoChandleTypeRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.CHandleType

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_string_type_node(self, rule: NoChandleTypeRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.StringType

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoChandleTypeRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of chandle type is discouraged in synthesizable RTL; chandle is a DPI-only handle type"


class TestNoRandomSystemFunctionRule:
    @pytest.fixture
    def rule(self) -> NoRandomSystemFunctionRule:
        return NoRandomSystemFunctionRule()

    def test_rule_has_correct_code(self, rule: NoRandomSystemFunctionRule) -> None:
        assert rule.code == "NO_RANDOM_SYSTEM_FUNCTION"

    def test_rule_has_correct_message(self, rule: NoRandomSystemFunctionRule) -> None:
        assert rule.message == "Use of $random/$urandom/$urandom_range is discouraged in synthesizable RTL; these are simulation-only randomization functions"

    def test_applies_returns_true_for_random(self, rule: NoRandomSystemFunctionRule) -> None:
        assert rule.applies(_system_name_vnode("$random"), Context()) is True

    def test_applies_returns_true_for_urandom_range(self, rule: NoRandomSystemFunctionRule) -> None:
        assert rule.applies(_system_name_vnode("$urandom_range"), Context()) is True

    def test_applies_returns_false_for_unrelated_system_task(self, rule: NoRandomSystemFunctionRule) -> None:
        assert rule.applies(_system_name_vnode("$time"), Context()) is False

    def test_applies_returns_false_for_non_system_name_node(self, rule: NoRandomSystemFunctionRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ProgramDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoRandomSystemFunctionRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 4, "col": 9}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 9
        assert result["message"] == "Use of $random/$urandom/$urandom_range is discouraged in synthesizable RTL; these are simulation-only randomization functions"


class TestNoTimeSystemFunctionRule:
    @pytest.fixture
    def rule(self) -> NoTimeSystemFunctionRule:
        return NoTimeSystemFunctionRule()

    def test_rule_has_correct_code(self, rule: NoTimeSystemFunctionRule) -> None:
        assert rule.code == "NO_TIME_SYSTEM_FUNCTION"

    def test_rule_has_correct_message(self, rule: NoTimeSystemFunctionRule) -> None:
        assert rule.message == "Use of $time/$realtime/$stime is discouraged in synthesizable RTL; these are simulation-only timing functions"

    def test_applies_returns_true_for_time(self, rule: NoTimeSystemFunctionRule) -> None:
        assert rule.applies(_system_name_vnode("$time"), Context()) is True

    def test_applies_returns_true_for_stime(self, rule: NoTimeSystemFunctionRule) -> None:
        assert rule.applies(_system_name_vnode("$stime"), Context()) is True

    def test_applies_returns_false_for_unrelated_system_task(self, rule: NoTimeSystemFunctionRule) -> None:
        assert rule.applies(_system_name_vnode("$random"), Context()) is False

    def test_applies_returns_false_for_non_system_name_node(self, rule: NoTimeSystemFunctionRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ProgramDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoTimeSystemFunctionRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 4, "col": 9}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 9
        assert result["message"] == "Use of $time/$realtime/$stime is discouraged in synthesizable RTL; these are simulation-only timing functions"


class TestNoVcdDumpTaskRule:
    @pytest.fixture
    def rule(self) -> NoVcdDumpTaskRule:
        return NoVcdDumpTaskRule()

    def test_rule_has_correct_code(self, rule: NoVcdDumpTaskRule) -> None:
        assert rule.code == "NO_VCD_DUMP_TASK"

    def test_rule_has_correct_message(self, rule: NoVcdDumpTaskRule) -> None:
        assert rule.message == "Use of $dumpfile/$dumpvars-family VCD dump system tasks is discouraged in synthesizable RTL; these are simulation-only waveform tracing tasks"

    def test_applies_returns_true_for_dumpfile(self, rule: NoVcdDumpTaskRule) -> None:
        assert rule.applies(_system_name_vnode("$dumpfile"), Context()) is True

    def test_applies_returns_true_for_dumpvars(self, rule: NoVcdDumpTaskRule) -> None:
        assert rule.applies(_system_name_vnode("$dumpvars"), Context()) is True

    def test_applies_returns_false_for_unrelated_system_task(self, rule: NoVcdDumpTaskRule) -> None:
        assert rule.applies(_system_name_vnode("$display"), Context()) is False

    def test_applies_returns_false_for_non_system_name_node(self, rule: NoVcdDumpTaskRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ProgramDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoVcdDumpTaskRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 4, "col": 9}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 9
        assert result["message"] == "Use of $dumpfile/$dumpvars-family VCD dump system tasks is discouraged in synthesizable RTL; these are simulation-only waveform tracing tasks"


class TestNoFileIoSystemTaskRule:
    @pytest.fixture
    def rule(self) -> NoFileIoSystemTaskRule:
        return NoFileIoSystemTaskRule()

    def test_rule_has_correct_code(self, rule: NoFileIoSystemTaskRule) -> None:
        assert rule.code == "NO_FILE_IO_SYSTEM_TASK"

    def test_rule_has_correct_message(self, rule: NoFileIoSystemTaskRule) -> None:
        assert rule.message == "Use of file I/O system tasks ($fopen/$fclose/$fdisplay/$fwrite/$fscanf/etc.) is discouraged in synthesizable RTL; these are simulation-only file operations"

    def test_applies_returns_true_for_fopen(self, rule: NoFileIoSystemTaskRule) -> None:
        assert rule.applies(_system_name_vnode("$fopen"), Context()) is True

    def test_applies_returns_true_for_fdisplay(self, rule: NoFileIoSystemTaskRule) -> None:
        assert rule.applies(_system_name_vnode("$fdisplay"), Context()) is True

    def test_applies_returns_false_for_plain_display(self, rule: NoFileIoSystemTaskRule) -> None:
        """`$display` (no `f`) is the console-output family, a separate rule's concern."""
        assert rule.applies(_system_name_vnode("$display"), Context()) is False

    def test_applies_returns_false_for_non_system_name_node(self, rule: NoFileIoSystemTaskRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ProgramDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoFileIoSystemTaskRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 4, "col": 9}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 9
        assert result["message"] == "Use of file I/O system tasks ($fopen/$fclose/$fdisplay/$fwrite/$fscanf/etc.) is discouraged in synthesizable RTL; these are simulation-only file operations"


class TestNoPlusargsSystemFunctionRule:
    @pytest.fixture
    def rule(self) -> NoPlusargsSystemFunctionRule:
        return NoPlusargsSystemFunctionRule()

    def test_rule_has_correct_code(self, rule: NoPlusargsSystemFunctionRule) -> None:
        assert rule.code == "NO_PLUSARGS_SYSTEM_FUNCTION"

    def test_rule_has_correct_message(self, rule: NoPlusargsSystemFunctionRule) -> None:
        assert rule.message == "Use of $test$plusargs/$value$plusargs is discouraged in synthesizable RTL; these are simulation-only command-line-argument functions"

    def test_applies_returns_true_for_test_plusargs(self, rule: NoPlusargsSystemFunctionRule) -> None:
        assert rule.applies(_system_name_vnode("$test$plusargs"), Context()) is True

    def test_applies_returns_true_for_value_plusargs(self, rule: NoPlusargsSystemFunctionRule) -> None:
        assert rule.applies(_system_name_vnode("$value$plusargs"), Context()) is True

    def test_applies_returns_false_for_unrelated_system_task(self, rule: NoPlusargsSystemFunctionRule) -> None:
        assert rule.applies(_system_name_vnode("$random"), Context()) is False

    def test_applies_returns_false_for_non_system_name_node(self, rule: NoPlusargsSystemFunctionRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ProgramDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoPlusargsSystemFunctionRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 4, "col": 9}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 9
        assert result["message"] == "Use of $test$plusargs/$value$plusargs is discouraged in synthesizable RTL; these are simulation-only command-line-argument functions"


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
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.ProgramDeclaration

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoAssertionControlTaskRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 4, "col": 9}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 9
        assert result["message"] == "Use of $assertoff/$asserton/$assertkill-family assertion-control system tasks is discouraged in synthesizable RTL; these are simulation-only verification controls"


def _find_first_node_of_kind(src: str, kind: object) -> object:
    tree = sl.SyntaxTree.fromText(src)
    found: object = None

    def walk(node: object) -> None:
        nonlocal found
        if found is None and getattr(node, "kind", None) == kind:
            found = node
        if hasattr(node, "__iter__"):
            for child in node:
                walk(child)

    walk(tree.root)
    return found


class TestNoQueueRule:
    @pytest.fixture
    def rule(self) -> NoQueueRule:
        return NoQueueRule()

    def test_rule_has_correct_code(self, rule: NoQueueRule) -> None:
        assert rule.code == "NO_QUEUE"

    def test_rule_has_correct_message(self, rule: NoQueueRule) -> None:
        assert rule.message == "Use of queue declarations (arr[$]) is discouraged in synthesizable RTL; queues are a dynamic, software-oriented SystemVerilog construct"

    def test_applies_returns_true_for_queue_dimension_node(self, rule: NoQueueRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.QueueDimensionSpecifier

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoQueueRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.WildcardDimensionSpecifier

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoQueueRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of queue declarations (arr[$]) is discouraged in synthesizable RTL; queues are a dynamic, software-oriented SystemVerilog construct"


class TestNoDynamicArrayRule:
    @pytest.fixture
    def rule(self) -> NoDynamicArrayRule:
        return NoDynamicArrayRule()

    def test_rule_has_correct_code(self, rule: NoDynamicArrayRule) -> None:
        assert rule.code == "NO_DYNAMIC_ARRAY"

    def test_rule_has_correct_message(self, rule: NoDynamicArrayRule) -> None:
        assert rule.message == "Use of dynamic array declarations (arr[]) is discouraged in synthesizable RTL; dynamic arrays are a software-oriented SystemVerilog construct"

    def test_applies_returns_true_for_bare_brackets(self, rule: NoDynamicArrayRule) -> None:
        raw_node = _find_first_node_of_kind("module top; int arr[]; endmodule", sl.SyntaxKind.VariableDimension)
        assert raw_node is not None

        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = raw_node

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_fixed_size_dimension(self, rule: NoDynamicArrayRule) -> None:
        """`arr[4]` has a real `specifier` (a BitSelect around the size literal), so
        it must not be mistaken for a dynamic array's bare `[]`."""
        raw_node = _find_first_node_of_kind("module top; int arr[4]; endmodule", sl.SyntaxKind.VariableDimension)
        assert raw_node is not None

        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = raw_node

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_false_for_queue_dimension(self, rule: NoDynamicArrayRule) -> None:
        raw_node = _find_first_node_of_kind("module top; int arr[$]; endmodule", sl.SyntaxKind.VariableDimension)
        assert raw_node is not None

        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = raw_node

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoDynamicArrayRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of dynamic array declarations (arr[]) is discouraged in synthesizable RTL; dynamic arrays are a software-oriented SystemVerilog construct"


class TestNoAssociativeArrayRule:
    @pytest.fixture
    def rule(self) -> NoAssociativeArrayRule:
        return NoAssociativeArrayRule()

    def test_rule_has_correct_code(self, rule: NoAssociativeArrayRule) -> None:
        assert rule.code == "NO_ASSOCIATIVE_ARRAY"

    def test_rule_has_correct_message(self, rule: NoAssociativeArrayRule) -> None:
        assert rule.message == "Use of associative array declarations (arr[*], arr[string], arr[int], etc.) is discouraged in synthesizable RTL; associative arrays are a software-oriented SystemVerilog construct"

    def test_applies_returns_true_for_wildcard_index(self, rule: NoAssociativeArrayRule) -> None:
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = Mock()
        mock_vnode.raw.kind = sl.SyntaxKind.WildcardDimensionSpecifier

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_string_index(self, rule: NoAssociativeArrayRule) -> None:
        raw_node = _find_first_node_of_kind("module top; int aa[string]; endmodule", sl.SyntaxKind.RangeDimensionSpecifier)
        assert raw_node is not None

        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = raw_node

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_int_index(self, rule: NoAssociativeArrayRule) -> None:
        raw_node = _find_first_node_of_kind("module top; int aa[int]; endmodule", sl.SyntaxKind.RangeDimensionSpecifier)
        assert raw_node is not None

        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = raw_node

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_identifier_index(self, rule: NoAssociativeArrayRule) -> None:
        """`arr[WIDTH]` is an ordinary parameter-sized fixed array -- syntactically
        indistinguishable from a user-defined-type associative-array index without
        symbol resolution, so it must not be guessed at."""
        raw_node = _find_first_node_of_kind(
            "module top; parameter WIDTH = 4; int arr[WIDTH]; endmodule", sl.SyntaxKind.RangeDimensionSpecifier
        )
        assert raw_node is not None

        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = raw_node

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_false_for_fixed_range(self, rule: NoAssociativeArrayRule) -> None:
        raw_node = _find_first_node_of_kind("module top; int arr[3:0]; endmodule", sl.SyntaxKind.RangeDimensionSpecifier)
        assert raw_node is not None

        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = raw_node

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoAssociativeArrayRule, mock_vnode: Mock) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of associative array declarations (arr[*], arr[string], arr[int], etc.) is discouraged in synthesizable RTL; associative arrays are a software-oriented SystemVerilog construct"
