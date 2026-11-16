"""Node rule tests for `declarations_and_types`: one test class per rule."""
import pytest
from src.pkg.parser.syntax_kinds import CHANDLE_TYPE_KIND, LOGIC_KEYWORD_TOKEN_KIND, REAL_TIME_TYPE_KIND, REAL_TYPE_KIND, SHORT_REAL_TYPE_KIND, STRING_TYPE_KIND, SUPPLY0_KEYWORD_TOKEN_KIND, SUPPLY1_KEYWORD_TOKEN_KIND, TRIREG_KEYWORD_TOKEN_KIND, UWIRE_KEYWORD_TOKEN_KIND, WAND_KEYWORD_TOKEN_KIND, WIRE_KEYWORD_TOKEN_KIND, WOR_KEYWORD_TOKEN_KIND
from src.pkg.rules.declarations_and_types.no_supply0_supply1 import NoSupply0Supply1Rule
from src.pkg.rules.declarations_and_types.no_trireg import NoTriregRule
from src.pkg.rules.declarations_and_types.no_wand_wor import NoWandWorRule
from src.pkg.rules.declarations_and_types.no_uwire import NoUwireRule
from src.pkg.rules.declarations_and_types.no_real_type import NoRealTypeRule
from src.pkg.rules.declarations_and_types.no_string_type import NoStringTypeRule
from src.pkg.rules.declarations_and_types.no_chandle_type import NoChandleTypeRule
from tests.support.fakes import fake_vnode
from src.pkg.walk.context import Context
from src.pkg.vnodes.base_vnode import BaseVNode
from tests.support.rule_node_helpers import mock_vnode


class TestNoWandWorRule:
    @pytest.fixture
    def rule(self) -> NoWandWorRule:
        return NoWandWorRule()

    def test_rule_has_correct_code(self, rule: NoWandWorRule) -> None:
        assert rule.code == "NO_WAND_WOR"

    def test_rule_has_correct_message(self, rule: NoWandWorRule) -> None:
        assert rule.message == "Use of wand/wor is discouraged in RTL; prefer explicit logic composition instead"

    def test_applies_returns_true_for_wand_keyword(self, rule: NoWandWorRule) -> None:
        mock_vnode = fake_vnode(WAND_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_wor_keyword(self, rule: NoWandWorRule) -> None:
        mock_vnode = fake_vnode(WOR_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_token(self, rule: NoWandWorRule) -> None:
        mock_vnode = fake_vnode(LOGIC_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoWandWorRule, mock_vnode: BaseVNode) -> None:
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
        mock_vnode = fake_vnode(TRIREG_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_token(self, rule: NoTriregRule) -> None:
        mock_vnode = fake_vnode(WIRE_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoTriregRule, mock_vnode: BaseVNode) -> None:
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
        mock_vnode = fake_vnode(SUPPLY0_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_supply1_keyword(self, rule: NoSupply0Supply1Rule) -> None:
        mock_vnode = fake_vnode(SUPPLY1_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_token(self, rule: NoSupply0Supply1Rule) -> None:
        mock_vnode = fake_vnode(WIRE_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoSupply0Supply1Rule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 2, "col": 12}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 12
        assert result["message"] == "Use of supply0/supply1 is discouraged in RTL; prefer explicit constant-driving intent instead"


class TestNoUwireRule:
    @pytest.fixture
    def rule(self) -> NoUwireRule:
        return NoUwireRule()

    def test_rule_has_correct_code(self, rule: NoUwireRule) -> None:
        assert rule.code == "NO_UWIRE"

    def test_rule_has_correct_message(self, rule: NoUwireRule) -> None:
        assert rule.message == "Use of uwire is discouraged in RTL; prefer explicit wire/tri declarations"

    def test_applies_returns_true_for_uwire_keyword(self, rule: NoUwireRule) -> None:
        mock_vnode = fake_vnode(UWIRE_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_wand_keyword(self, rule: NoUwireRule) -> None:
        mock_vnode = fake_vnode(WAND_KEYWORD_TOKEN_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoUwireRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of uwire is discouraged in RTL; prefer explicit wire/tri declarations"


class TestNoRealTypeRule:
    @pytest.fixture
    def rule(self) -> NoRealTypeRule:
        return NoRealTypeRule()

    def test_rule_has_correct_code(self, rule: NoRealTypeRule) -> None:
        assert rule.code == "NO_REAL_TYPE"

    def test_rule_has_correct_message(self, rule: NoRealTypeRule) -> None:
        assert rule.message == "Use of real/shortreal/realtime types is discouraged in synthesizable RTL; floating-point types are not synthesizable"

    def test_applies_returns_true_for_real_type_node(self, rule: NoRealTypeRule) -> None:
        mock_vnode = fake_vnode(REAL_TYPE_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_shortreal_type_node(self, rule: NoRealTypeRule) -> None:
        mock_vnode = fake_vnode(SHORT_REAL_TYPE_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_realtime_type_node(self, rule: NoRealTypeRule) -> None:
        mock_vnode = fake_vnode(REAL_TIME_TYPE_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_string_type_node(self, rule: NoRealTypeRule) -> None:
        mock_vnode = fake_vnode(STRING_TYPE_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoRealTypeRule, mock_vnode: BaseVNode) -> None:
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
        mock_vnode = fake_vnode(STRING_TYPE_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_real_type_node(self, rule: NoStringTypeRule) -> None:
        mock_vnode = fake_vnode(REAL_TYPE_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoStringTypeRule, mock_vnode: BaseVNode) -> None:
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
        mock_vnode = fake_vnode(CHANDLE_TYPE_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_string_type_node(self, rule: NoChandleTypeRule) -> None:
        mock_vnode = fake_vnode(STRING_TYPE_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoChandleTypeRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of chandle type is discouraged in synthesizable RTL; chandle is a DPI-only handle type"
