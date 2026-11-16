"""Node rule tests for `combinational_logic`: one test class per rule."""
import pytest
from src.pkg.parser.parse import parse_text
from src.pkg.parser.types import ProceduralBlockNode
from src.pkg.parser.syntax_kinds import ALWAYS_BLOCK_KIND, LESS_THAN_EQUALS_TOKEN_KIND, EQUALS_TOKEN_KIND, AND_KEYWORD_TOKEN_KIND, BUFIF0_KEYWORD_TOKEN_KIND, CMOS_KEYWORD_TOKEN_KIND, INITIAL_KEYWORD_TOKEN_KIND, OR_KEYWORD_TOKEN_KIND, PULLUP_KEYWORD_TOKEN_KIND, RTRANIF0_KEYWORD_TOKEN_KIND, RTRAN_KEYWORD_TOKEN_KIND, TASK_DECLARATION_KIND, TRANIF1_KEYWORD_TOKEN_KIND, TRAN_KEYWORD_TOKEN_KIND, UDP_DECLARATION_KIND
from src.pkg.rules.combinational_logic.no_latch_in_always_comb import NoLatchInAlwaysCombRule
from src.pkg.rules.combinational_logic.no_nonblocking_comb import NoNonBlockingAssignmentInCombRule
from src.pkg.rules.combinational_logic.no_tranif_rtranif import NoTranifRtranifRule
from src.pkg.rules.combinational_logic.no_tran_rtran import NoTranRtranRule
from src.pkg.rules.combinational_logic.no_primitive_declaration import NoPrimitiveDeclarationRule
from src.pkg.rules.combinational_logic.no_gate_primitive import NoGatePrimitiveRule
from src.pkg.rules.combinational_logic.no_switch_primitive import NoSwitchPrimitiveRule
from tests.support.fakes import FakeVNode, fake_vnode
from tests.support.parse_diagnostics import assert_no_parse_errors
from tests.support.syntax_context_builders import primitive_instantiation_context
from src.pkg.walk.context import Context, ContextFlag
from src.pkg.vnodes.base_vnode import BaseVNode
from tests.support.rule_node_helpers import _always_block_and_token, mock_vnode


def _always_block_and_nonblocking_token(src: str) -> tuple[object, object]:
    return _always_block_and_token(src, LESS_THAN_EQUALS_TOKEN_KIND)


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
        mock_vnode = fake_vnode(LESS_THAN_EQUALS_TOKEN_KIND)

        context = Context().with_flag(ContextFlag.ALWAYS_COMB)

        assert rule.applies(mock_vnode, context) is True

    def test_applies_returns_false_without_lessthanequals_token(self, rule: NoNonBlockingAssignmentInCombRule) -> None:
        """Test that applies() returns False if vnode is not LessThanEquals token."""
        mock_vnode = fake_vnode(EQUALS_TOKEN_KIND)

        context = Context().with_flag(ContextFlag.ALWAYS_COMB)

        assert rule.applies(mock_vnode, context) is False

    def test_applies_returns_false_without_always_comb_flag(self, rule: NoNonBlockingAssignmentInCombRule) -> None:
        """Test that applies() returns False without ALWAYS_COMB flag."""
        mock_vnode = fake_vnode(LESS_THAN_EQUALS_TOKEN_KIND)

        context = Context()

        assert rule.applies(mock_vnode, context) is False

    def test_applies_returns_false_in_sequential_logic(self, rule: NoNonBlockingAssignmentInCombRule) -> None:
        """Test that applies() returns False in always @(posedge)."""
        mock_vnode = fake_vnode(LESS_THAN_EQUALS_TOKEN_KIND)

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

        block_vnode = FakeVNode(block_raw)
        token_vnode_ = FakeVNode(token_raw)

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

        block_vnode = FakeVNode(block_raw)
        token_vnode_ = FakeVNode(token_raw)

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

        block_vnode = FakeVNode(block_raw)
        token_vnode_ = FakeVNode(token_raw)

        context = Context().push(block_vnode)

        assert rule.applies(token_vnode_, context) is False

    def test_report_returns_correct_format(self, rule: NoNonBlockingAssignmentInCombRule, mock_vnode: BaseVNode) -> None:
        """Test that report() returns the correct diagnostic format."""
        mock_vnode.location = {"line": 25, "col": 12}
        result = rule.report(mock_vnode)

        assert result["line"] == 25
        assert result["col"] == 12
        assert result["message"] == "Non-blocking assignment used in combinational logic"


class TestNoLatchInAlwaysCombRule:
    @pytest.fixture
    def rule(self) -> NoLatchInAlwaysCombRule:
        return NoLatchInAlwaysCombRule()

    def test_rule_has_correct_code(self, rule: NoLatchInAlwaysCombRule) -> None:
        assert rule.code == "NO_LATCH_IN_ALWAYS_COMB"

    def test_rule_has_correct_message(self, rule: NoLatchInAlwaysCombRule) -> None:
        assert rule.message == "always_comb block contains a conditional-only assignment that can infer latch-like storage"

    def test_applies_returns_true_for_missing_default_assignment(self, rule: NoLatchInAlwaysCombRule) -> None:
        tree = parse_text(
            """
            module top(input logic a, b, output logic y);
                always_comb begin
                    if (a) y = b;
                end
            endmodule
            """
        )
        assert_no_parse_errors("test_applies_returns_true_for_missing_default_assignment", tree)

        def walk(node):
            if isinstance(node, ProceduralBlockNode):
                return node
            if hasattr(node, "__iter__"):
                for child in node:
                    found = walk(child)
                    if found is not None:
                        return found
            return None

        raw_node = walk(tree.root)
        assert raw_node is not None

        mock_vnode = FakeVNode(raw_node)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_with_prior_default_assignment(self, rule: NoLatchInAlwaysCombRule) -> None:
        tree = parse_text(
            """
            module top(input logic a, b, output logic y);
                always_comb begin
                    y = '0;
                    if (a) y = b;
                end
            endmodule
            """
        )
        assert_no_parse_errors("test_applies_returns_false_with_prior_default_assignment", tree)

        def walk(node):
            if isinstance(node, ProceduralBlockNode):
                return node
            if hasattr(node, "__iter__"):
                for child in node:
                    found = walk(child)
                    if found is not None:
                        return found
            return None

        raw_node = walk(tree.root)
        assert raw_node is not None

        mock_vnode = FakeVNode(raw_node)

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_false_with_explicit_else(self, rule: NoLatchInAlwaysCombRule) -> None:
        tree = parse_text(
            """
            module top(input logic a, b, c, output logic y);
                always_comb begin
                    if (a) y = b;
                    else y = c;
                end
            endmodule
            """
        )
        assert_no_parse_errors("test_applies_returns_false_with_explicit_else", tree)

        def walk(node):
            if isinstance(node, ProceduralBlockNode):
                return node
            if hasattr(node, "__iter__"):
                for child in node:
                    found = walk(child)
                    if found is not None:
                        return found
            return None

        raw_node = walk(tree.root)
        assert raw_node is not None

        mock_vnode = FakeVNode(raw_node)

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_false_for_non_always_comb_block(self, rule: NoLatchInAlwaysCombRule) -> None:
        mock_vnode = fake_vnode(ALWAYS_BLOCK_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoLatchInAlwaysCombRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 5, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 5
        assert result["col"] == 3
        assert result["message"] == "always_comb block contains a conditional-only assignment that can infer latch-like storage"


class TestNoTranRtranRule:
    @pytest.fixture
    def rule(self) -> NoTranRtranRule:
        return NoTranRtranRule()

    def test_rule_has_correct_code(self, rule: NoTranRtranRule) -> None:
        assert rule.code == "NO_TRAN_RTRAN"

    def test_rule_has_correct_message(self, rule: NoTranRtranRule) -> None:
        assert rule.message == "Use of tran/rtran is discouraged in RTL; prefer explicit connectivity modeling instead"

    def test_applies_returns_true_for_tran_keyword(self, rule: NoTranRtranRule) -> None:
        mock_vnode = fake_vnode(TRAN_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_rtran_keyword(self, rule: NoTranRtranRule) -> None:
        mock_vnode = fake_vnode(RTRAN_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_tranif_keyword(self, rule: NoTranRtranRule) -> None:
        mock_vnode = fake_vnode(TRANIF1_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoTranRtranRule, mock_vnode: BaseVNode) -> None:
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
        mock_vnode = fake_vnode(TRANIF1_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_rtranif0_keyword(self, rule: NoTranifRtranifRule) -> None:
        mock_vnode = fake_vnode(RTRANIF0_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_tran_keyword(self, rule: NoTranifRtranifRule) -> None:
        mock_vnode = fake_vnode(TRAN_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoTranifRtranifRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 10, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 10
        assert result["col"] == 5
        assert result["message"] == "Use of tranif/rtranif is discouraged in RTL; prefer explicit connectivity modeling instead"


class TestNoPrimitiveDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoPrimitiveDeclarationRule:
        return NoPrimitiveDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoPrimitiveDeclarationRule) -> None:
        assert rule.code == "NO_PRIMITIVE_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoPrimitiveDeclarationRule) -> None:
        assert rule.message == "Use of user-defined primitive (UDP) declarations is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_udp_declaration_node(self, rule: NoPrimitiveDeclarationRule) -> None:
        mock_vnode = fake_vnode(UDP_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoPrimitiveDeclarationRule) -> None:
        mock_vnode = fake_vnode(TASK_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoPrimitiveDeclarationRule, mock_vnode: BaseVNode) -> None:
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
        mock_vnode = fake_vnode(AND_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, primitive_instantiation_context()) is True

    def test_applies_returns_true_for_bufif0_keyword_inside_primitive_instantiation(self, rule: NoGatePrimitiveRule) -> None:
        mock_vnode = fake_vnode(BUFIF0_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, primitive_instantiation_context()) is True

    def test_applies_returns_false_for_other_token(self, rule: NoGatePrimitiveRule) -> None:
        mock_vnode = fake_vnode(INITIAL_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, primitive_instantiation_context()) is False

    def test_applies_returns_false_for_or_keyword_outside_primitive_instantiation(self, rule: NoGatePrimitiveRule) -> None:
        """`or` is also the separator in classic event/sensitivity lists
        (`@(posedge clk or negedge rst_n)`), which shares the same OR_KEYWORD_TOKEN_KIND
        as the `or` gate-primitive keyword but is not a gate instantiation at all."""
        mock_vnode = fake_vnode(OR_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_true_for_or_keyword_inside_primitive_instantiation(self, rule: NoGatePrimitiveRule) -> None:
        mock_vnode = fake_vnode(OR_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, primitive_instantiation_context()) is True

    def test_report_returns_correct_format(self, rule: NoGatePrimitiveRule, mock_vnode: BaseVNode) -> None:
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
        mock_vnode = fake_vnode(CMOS_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, primitive_instantiation_context()) is True

    def test_applies_returns_true_for_pullup_keyword_inside_primitive_instantiation(self, rule: NoSwitchPrimitiveRule) -> None:
        mock_vnode = fake_vnode(PULLUP_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, primitive_instantiation_context()) is True

    def test_applies_returns_false_for_other_token(self, rule: NoSwitchPrimitiveRule) -> None:
        mock_vnode = fake_vnode(INITIAL_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, primitive_instantiation_context()) is False

    def test_applies_returns_false_for_cmos_keyword_outside_primitive_instantiation(self, rule: NoSwitchPrimitiveRule) -> None:
        mock_vnode = fake_vnode(CMOS_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_applies_returns_false_for_gate_primitive_token(self, rule: NoSwitchPrimitiveRule) -> None:
        """A gate-level `and`/`or`/... keyword is `NO_GATE_PRIMITIVE`'s concern, not this rule's."""
        mock_vnode = fake_vnode(AND_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, primitive_instantiation_context()) is False

    def test_report_returns_correct_format(self, rule: NoSwitchPrimitiveRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 2, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 5
        assert result["message"] == "Use of switch-level primitives is discouraged in RTL; prefer behavioral or operator-level modeling"
