"""Node rule tests for `simulation_vs_synthesis`: system tasks and functions."""
import pytest
from src.pkg.parser.syntax_kinds import PROGRAM_DECLARATION_KIND
from src.pkg.rules.simulation_vs_synthesis.no_display_system_task import NoDisplaySystemTaskRule
from src.pkg.rules.simulation_vs_synthesis.no_simulation_control_task import NoSimulationControlTaskRule
from src.pkg.rules.simulation_vs_synthesis.no_random_system_function import NoRandomSystemFunctionRule
from src.pkg.rules.simulation_vs_synthesis.no_time_system_function import NoTimeSystemFunctionRule
from src.pkg.rules.simulation_vs_synthesis.no_vcd_dump_task import NoVcdDumpTaskRule
from src.pkg.rules.simulation_vs_synthesis.no_file_io_system_task import NoFileIoSystemTaskRule
from src.pkg.rules.simulation_vs_synthesis.no_plusargs_system_function import NoPlusargsSystemFunctionRule
from tests.support.fakes import fake_vnode
from src.pkg.walk.context import Context
from src.pkg.vnodes.base_vnode import BaseVNode
from tests.support.rule_node_helpers import _system_name_vnode, mock_vnode


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
        mock_vnode = fake_vnode(PROGRAM_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoDisplaySystemTaskRule, mock_vnode: BaseVNode) -> None:
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
        mock_vnode = fake_vnode(PROGRAM_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoSimulationControlTaskRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 7, "col": 9}
        result = rule.report(mock_vnode)

        assert result["line"] == 7
        assert result["col"] == 9
        assert result["message"] == "Use of $stop/$finish is discouraged in synthesizable RTL; these are simulation-only control tasks"


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
        mock_vnode = fake_vnode(PROGRAM_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoRandomSystemFunctionRule, mock_vnode: BaseVNode) -> None:
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
        mock_vnode = fake_vnode(PROGRAM_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoTimeSystemFunctionRule, mock_vnode: BaseVNode) -> None:
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
        mock_vnode = fake_vnode(PROGRAM_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoVcdDumpTaskRule, mock_vnode: BaseVNode) -> None:
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
        mock_vnode = fake_vnode(PROGRAM_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoFileIoSystemTaskRule, mock_vnode: BaseVNode) -> None:
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
        mock_vnode = fake_vnode(PROGRAM_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoPlusargsSystemFunctionRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 4, "col": 9}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 9
        assert result["message"] == "Use of $test$plusargs/$value$plusargs is discouraged in synthesizable RTL; these are simulation-only command-line-argument functions"
