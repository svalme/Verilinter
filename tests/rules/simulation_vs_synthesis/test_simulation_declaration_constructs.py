"""Node rule tests for `simulation_vs_synthesis`: declarations and constructs outside the synthesizable subset."""
import pytest
from src.pkg.parser.parse import parse_file
from src.pkg.parser.syntax_kinds import MODULE_DECLARATION_KIND, MODPORT_DECLARATION_KIND, CLOCKING_DECLARATION_KIND, CLASS_DECLARATION_KIND, CONFIG_DECLARATION_KIND, DPI_EXPORT_KIND, DPI_IMPORT_KIND, FUNCTION_DECLARATION_KIND, INTERFACE_DECLARATION_KIND, LET_DECLARATION_KIND, PACKAGE_DECLARATION_KIND, PROGRAM_DECLARATION_KIND, SPECIFY_BLOCK_KIND, TASK_DECLARATION_KIND, VIRTUAL_INTERFACE_TYPE_KIND
from src.pkg.rules.simulation_vs_synthesis.no_clocking_declaration import NoClockingDeclarationRule
from src.pkg.rules.simulation_vs_synthesis.no_interface_declaration import NoInterfaceDeclarationRule
from src.pkg.rules.simulation_vs_synthesis.no_modport_declaration import NoModportDeclarationRule
from src.pkg.rules.simulation_vs_synthesis.no_package_declaration import NoPackageDeclarationRule
from src.pkg.rules.simulation_vs_synthesis.no_program_declaration import NoProgramDeclarationRule
from src.pkg.rules.simulation_vs_synthesis.no_task_declaration import NoTaskDeclarationRule
from src.pkg.rules.simulation_vs_synthesis.no_specify_block import NoSpecifyBlockRule
from src.pkg.rules.simulation_vs_synthesis.no_class_declaration import NoClassDeclarationRule
from src.pkg.rules.simulation_vs_synthesis.no_function_declaration import NoFunctionDeclarationRule
from src.pkg.rules.simulation_vs_synthesis.no_let_declaration import NoLetDeclarationRule
from src.pkg.rules.simulation_vs_synthesis.no_config_declaration import NoConfigDeclarationRule
from src.pkg.rules.simulation_vs_synthesis.no_virtual_interface import NoVirtualInterfaceRule
from src.pkg.rules.simulation_vs_synthesis.no_dpi_import_export import NoDpiImportExportRule
from tests.support.fakes import FakeVNode, fake_vnode
from src.pkg.walk.context import Context
from src.pkg.vnodes.base_vnode import BaseVNode
from tests.support.rule_node_helpers import DATA, mock_vnode


class TestNoTaskDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoTaskDeclarationRule:
        return NoTaskDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoTaskDeclarationRule) -> None:
        assert rule.code == "NO_TASK_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoTaskDeclarationRule) -> None:
        assert rule.message == "Use of task declarations is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_task_declaration_node(self, rule: NoTaskDeclarationRule) -> None:
        tree = parse_file(str(DATA / "task_declaration.v"))

        def walk(node):
            if getattr(node, "kind", None) == TASK_DECLARATION_KIND:
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

    def test_applies_returns_false_for_function_declaration_node(self, rule: NoTaskDeclarationRule) -> None:
        mock_vnode = fake_vnode(FUNCTION_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoTaskDeclarationRule, mock_vnode: BaseVNode) -> None:
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
        mock_vnode = fake_vnode(PROGRAM_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_module_declaration_node(self, rule: NoProgramDeclarationRule) -> None:
        mock_vnode = fake_vnode(MODULE_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoProgramDeclarationRule, mock_vnode: BaseVNode) -> None:
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
        mock_vnode = fake_vnode(CLOCKING_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_program_declaration_node(self, rule: NoClockingDeclarationRule) -> None:
        mock_vnode = fake_vnode(PROGRAM_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoClockingDeclarationRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of clocking declarations is discouraged in synthesizable RTL"


class TestNoInterfaceDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoInterfaceDeclarationRule:
        return NoInterfaceDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoInterfaceDeclarationRule) -> None:
        assert rule.code == "NO_INTERFACE_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoInterfaceDeclarationRule) -> None:
        assert rule.message == "Use of interface declarations is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_interface_declaration_node(self, rule: NoInterfaceDeclarationRule) -> None:
        mock_vnode = fake_vnode(INTERFACE_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_program_declaration_node(self, rule: NoInterfaceDeclarationRule) -> None:
        mock_vnode = fake_vnode(PROGRAM_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoInterfaceDeclarationRule, mock_vnode: BaseVNode) -> None:
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
        mock_vnode = fake_vnode(MODPORT_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_interface_declaration_node(self, rule: NoModportDeclarationRule) -> None:
        mock_vnode = fake_vnode(INTERFACE_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoModportDeclarationRule, mock_vnode: BaseVNode) -> None:
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
        mock_vnode = fake_vnode(PACKAGE_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_program_declaration_node(self, rule: NoPackageDeclarationRule) -> None:
        mock_vnode = fake_vnode(PROGRAM_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoPackageDeclarationRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 1, "col": 1}
        result = rule.report(mock_vnode)

        assert result["line"] == 1
        assert result["col"] == 1
        assert result["message"] == "Use of package declarations is discouraged in synthesizable RTL"


class TestNoSpecifyBlockRule:
    @pytest.fixture
    def rule(self) -> NoSpecifyBlockRule:
        return NoSpecifyBlockRule()

    def test_rule_has_correct_code(self, rule: NoSpecifyBlockRule) -> None:
        assert rule.code == "NO_SPECIFY_BLOCK"

    def test_rule_has_correct_message(self, rule: NoSpecifyBlockRule) -> None:
        assert rule.message == "Use of specify blocks is discouraged in synthesizable RTL; pin-to-pin timing modeling is not synthesizable"

    def test_applies_returns_true_for_specify_block_node(self, rule: NoSpecifyBlockRule) -> None:
        mock_vnode = fake_vnode(SPECIFY_BLOCK_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoSpecifyBlockRule) -> None:
        mock_vnode = fake_vnode(PROGRAM_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoSpecifyBlockRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 4, "col": 5}
        result = rule.report(mock_vnode)

        assert result["line"] == 4
        assert result["col"] == 5
        assert result["message"] == "Use of specify blocks is discouraged in synthesizable RTL; pin-to-pin timing modeling is not synthesizable"


class TestNoClassDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoClassDeclarationRule:
        return NoClassDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoClassDeclarationRule) -> None:
        assert rule.code == "NO_CLASS_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoClassDeclarationRule) -> None:
        assert rule.message == "Use of class declarations is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_class_declaration_node(self, rule: NoClassDeclarationRule) -> None:
        mock_vnode = fake_vnode(CLASS_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoClassDeclarationRule) -> None:
        mock_vnode = fake_vnode(INTERFACE_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoClassDeclarationRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 1, "col": 1}
        result = rule.report(mock_vnode)

        assert result["line"] == 1
        assert result["col"] == 1
        assert result["message"] == "Use of class declarations is discouraged in synthesizable RTL"


class TestNoFunctionDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoFunctionDeclarationRule:
        return NoFunctionDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoFunctionDeclarationRule) -> None:
        assert rule.code == "NO_FUNCTION_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoFunctionDeclarationRule) -> None:
        assert rule.message == "Use of function declarations is discouraged in this restricted RTL subset"

    def test_applies_returns_true_for_function_declaration_node(self, rule: NoFunctionDeclarationRule) -> None:
        mock_vnode = fake_vnode(FUNCTION_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_task_declaration_node(self, rule: NoFunctionDeclarationRule) -> None:
        mock_vnode = fake_vnode(TASK_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoFunctionDeclarationRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of function declarations is discouraged in this restricted RTL subset"


class TestNoLetDeclarationRule:
    @pytest.fixture
    def rule(self) -> NoLetDeclarationRule:
        return NoLetDeclarationRule()

    def test_rule_has_correct_code(self, rule: NoLetDeclarationRule) -> None:
        assert rule.code == "NO_LET_DECLARATION"

    def test_rule_has_correct_message(self, rule: NoLetDeclarationRule) -> None:
        assert rule.message == "Use of let declarations is discouraged in synthesizable RTL"

    def test_applies_returns_true_for_let_declaration_node(self, rule: NoLetDeclarationRule) -> None:
        mock_vnode = fake_vnode(LET_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoLetDeclarationRule) -> None:
        mock_vnode = fake_vnode(FUNCTION_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoLetDeclarationRule, mock_vnode: BaseVNode) -> None:
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
        mock_vnode = fake_vnode(CONFIG_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoConfigDeclarationRule) -> None:
        mock_vnode = fake_vnode(PACKAGE_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoConfigDeclarationRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of config declarations is discouraged in synthesizable RTL; library/config binding is a compilation-flow concern, not design intent"


class TestNoVirtualInterfaceRule:
    @pytest.fixture
    def rule(self) -> NoVirtualInterfaceRule:
        return NoVirtualInterfaceRule()

    def test_rule_has_correct_code(self, rule: NoVirtualInterfaceRule) -> None:
        assert rule.code == "NO_VIRTUAL_INTERFACE"

    def test_rule_has_correct_message(self, rule: NoVirtualInterfaceRule) -> None:
        assert rule.message == "Use of virtual interface declarations is discouraged in synthesizable RTL; virtual interfaces are a testbench-only construct"

    def test_applies_returns_true_for_virtual_interface_type_node(self, rule: NoVirtualInterfaceRule) -> None:
        mock_vnode = fake_vnode(VIRTUAL_INTERFACE_TYPE_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_interface_declaration_node(self, rule: NoVirtualInterfaceRule) -> None:
        mock_vnode = fake_vnode(INTERFACE_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoVirtualInterfaceRule, mock_vnode: BaseVNode) -> None:
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
        mock_vnode = fake_vnode(DPI_IMPORT_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_true_for_dpi_export_node(self, rule: NoDpiImportExportRule) -> None:
        mock_vnode = fake_vnode(DPI_EXPORT_KIND)

        assert rule.applies(mock_vnode, Context()) is True

    def test_applies_returns_false_for_other_node(self, rule: NoDpiImportExportRule) -> None:
        mock_vnode = fake_vnode(FUNCTION_DECLARATION_KIND)

        assert rule.applies(mock_vnode, Context()) is False

    def test_report_returns_correct_format(self, rule: NoDpiImportExportRule, mock_vnode: BaseVNode) -> None:
        mock_vnode.location = {"line": 2, "col": 3}
        result = rule.report(mock_vnode)

        assert result["line"] == 2
        assert result["col"] == 3
        assert result["message"] == "Use of DPI import/export declarations is discouraged in synthesizable RTL; DPI is a simulation/foreign-code bridge"
