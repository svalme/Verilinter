"""Node rule tests for `sequential_logic`: one test class per rule."""
import pytest
from src.pkg.parser.syntax_kinds import ALWAYS_FF_BLOCK_KIND, ALWAYS_LATCH_BLOCK_KIND, LESS_THAN_EQUALS_TOKEN_KIND, EQUALS_TOKEN_KIND
from src.pkg.rules.sequential_logic.no_always_ff import NoAlwaysFFRule
from src.pkg.rules.sequential_logic.no_blocking_sequential_logic import NoBlockingAssignmentInSequentialRule
from tests.support.fakes import FakeVNode, fake_vnode
from src.pkg.walk.context import Context, ContextFlag
from src.pkg.vnodes.base_vnode import BaseVNode
from tests.support.rule_node_helpers import _always_block_and_token, mock_vnode


def _always_block_and_blocking_token(src: str) -> tuple[object, object]:
    return _always_block_and_token(src, EQUALS_TOKEN_KIND)


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
        mock_vnode = fake_vnode(EQUALS_TOKEN_KIND)

        context = Context().with_flag(ContextFlag.ALWAYS)

        assert rule.applies(mock_vnode, context) is True

    def test_applies_returns_false_without_equals_token(self, rule: NoBlockingAssignmentInSequentialRule) -> None:
        """Test that applies() returns False if vnode is not Equals token."""
        mock_vnode = fake_vnode(LESS_THAN_EQUALS_TOKEN_KIND)

        context = Context().with_flag(ContextFlag.ALWAYS)

        assert rule.applies(mock_vnode, context) is False

    def test_applies_returns_false_without_always_flag(self, rule: NoBlockingAssignmentInSequentialRule) -> None:
        """Test that applies() returns False without ALWAYS flag."""
        mock_vnode = fake_vnode(EQUALS_TOKEN_KIND)

        context = Context()

        assert rule.applies(mock_vnode, context) is False

    def test_applies_returns_false_in_combinational_logic(self, rule: NoBlockingAssignmentInSequentialRule) -> None:
        """Test that applies() returns False in always_comb."""
        mock_vnode = fake_vnode(EQUALS_TOKEN_KIND)

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

        block_vnode = FakeVNode(block_raw)
        token_vnode_ = FakeVNode(token_raw)

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

        block_vnode = FakeVNode(block_raw)
        token_vnode_ = FakeVNode(token_raw)

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

        block_vnode = FakeVNode(block_raw)
        token_vnode_ = FakeVNode(token_raw)

        context = Context().with_flag(ContextFlag.ALWAYS).push(block_vnode)

        assert rule.applies(token_vnode_, context) is True

    def test_report_returns_correct_format(self, rule: NoBlockingAssignmentInSequentialRule, mock_vnode: BaseVNode) -> None:
        """Test that report() returns the correct diagnostic format."""
        mock_vnode.location = {"line": 15, "col": 8}
        result = rule.report(mock_vnode)

        assert result["line"] == 15
        assert result["col"] == 8
        assert result["message"] == "Blocking assignment used in sequential logic"


class TestNoAlwaysFFRule:
    @pytest.fixture
    def rule(self) -> NoAlwaysFFRule:
        return NoAlwaysFFRule()

    def test_rule_has_correct_code(self, rule: NoAlwaysFFRule) -> None:
        assert rule.code == "NO_ALWAYS_FF"

    def test_rule_has_correct_message(self, rule: NoAlwaysFFRule) -> None:
        assert rule.message == "Use of always_ff is discouraged in this RTL subset"

    def test_applies_returns_true_for_always_ff_block(self, rule: NoAlwaysFFRule) -> None:
        mock_vnode = fake_vnode(ALWAYS_FF_BLOCK_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_procedural_block(self, rule: NoAlwaysFFRule) -> None:
        mock_vnode = fake_vnode(ALWAYS_LATCH_BLOCK_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoAlwaysFFRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 10, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 10
        assert result["col"] == 3
        assert result["message"] == "Use of always_ff is discouraged in this RTL subset"
