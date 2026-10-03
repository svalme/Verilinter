from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *

CODE = """
module top;
  foo_mod u_foo();
  bar_mod #(.WIDTH(8)) u_bar(.clk(clk));
  baz_mod u_baz(.*);
endmodule
"""


@pytest.fixture
def walked() -> tuple[Walker, SymbolTable]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(CODE)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return walker, symbol_table


class TestHierarchyInstantiationHandler:
    def test_registers_instance_symbols(self, walked: tuple[Walker, SymbolTable]) -> None:
        _, symbol_table = walked

        top_scope = symbol_table.lookup_module("top")
        assert top_scope is not None
        assert top_scope.lookup("u_foo") is not None
        assert top_scope.lookup("u_bar") is not None
        assert top_scope.lookup("u_foo").kind == "instance"

    def test_registers_module_type_references(self, walked: tuple[Walker, SymbolTable]) -> None:
        _, symbol_table = walked

        names = [name for name, _loc in symbol_table.module_references]
        assert names == ["foo_mod", "bar_mod", "baz_mod"]

    def test_module_reference_carries_a_real_location(self, walked: tuple[Walker, SymbolTable]) -> None:
        _, symbol_table = walked

        _, loc = symbol_table.module_references[0]
        assert loc["line"] == 3

    def test_records_instantiation_connection_details(self, walked: tuple[Walker, SymbolTable]) -> None:
        _, symbol_table = walked

        assert len(symbol_table.instantiations) == 3
        first = symbol_table.instantiations[0]
        second = symbol_table.instantiations[1]
        third = symbol_table.instantiations[2]

        assert first["instance_name"] == "u_foo"
        assert first["connection_style"] == "empty"
        assert first["connections"] == []

        assert second["instance_name"] == "u_bar"
        assert second["connection_style"] == "named"
        assert second["connections"][0]["port_name"] == "clk"
        assert second["connections"][0]["expr_text"] == "clk"

        assert third["instance_name"] == "u_baz"
        assert third["connection_style"] == "wildcard"
        assert third["connections"][0]["kind"] == "wildcard"

    def test_records_typed_domain_models(self, walked: tuple[Walker, SymbolTable]) -> None:
        from src.pkg.semantic.models import InstanceRecord, ParameterOverride, PortConnection

        _, symbol_table = walked
        assert len(symbol_table.instantiations) == 3

        second = symbol_table.instantiations[1]
        assert isinstance(second, InstanceRecord)
        assert second.instance_name == "u_bar"
        assert second.child_module == "bar_mod"
        assert second.connection_style == "named"
        assert len(second.connections) == 1
        assert isinstance(second.connections[0], PortConnection)
        assert second.connections[0].port_name == "clk"
        assert second.connections[0].expr_text == "clk"
        assert len(second.parameter_overrides) == 1
        assert isinstance(second.parameter_overrides[0], ParameterOverride)
        assert second.parameter_overrides[0].param_name == "WIDTH"


class TestParameterOverrideExtractor:
    def test_custom_evaluator_injection(self) -> None:
        from unittest.mock import Mock
        from src.pkg.handlers.hierarchy_instantiation import ParameterOverrideExtractor

        tree = parse_text("module top; child #(.PARAM(1 + 2)) u_inst(); endmodule\n")
        inst_node = tree.root.members[0]

        mock_eval = Mock(return_value=999)
        extractor = ParameterOverrideExtractor(evaluator=mock_eval)
        overrides, style = extractor.extract(inst_node, tree)

        assert style == "named"
        assert len(overrides) == 1
        assert overrides[0].param_name == "PARAM"
        assert overrides[0].expr_value == 999
        mock_eval.assert_called_once()


class TestPortConnectionExtractor:
    def test_custom_width_resolver_injection(self) -> None:
        from unittest.mock import Mock
        from src.pkg.handlers.hierarchy_instantiation import PortConnectionExtractor

        tree = parse_text("module top; child u_inst(.clk(sys_clk)); endmodule\n")
        inst_node = tree.root.members[0]
        item = inst_node.instances[0]

        mock_width_resolver = Mock(return_value=(32, True))
        extractor = PortConnectionExtractor(width_resolver=mock_width_resolver)
        conns, style = extractor.extract(item, tree)

        assert style == "named"
        assert len(conns) == 1
        assert conns[0].port_name == "clk"
        assert conns[0].expr_width == 32
        assert conns[0].expr_signed is True
        mock_width_resolver.assert_called_once()


class TestHierarchyInstantiationHandlerInjection:
    def test_extractors_injection(self) -> None:
        from unittest.mock import Mock
        from src.pkg.handlers.hierarchy_instantiation import (
            ParameterOverrideExtractor,
            PortConnectionExtractor,
        )
        from src.pkg.handlers.hierarchy_instantiation_handler import (
            HierarchyInstantiationHandler,
        )
        from src.pkg.semantic.models import ParameterOverride, PortConnection
        from src.pkg.semantic.scope import Scope
        from src.pkg.vnodes.syntax_vnode import SyntaxVNode

        mock_param_extractor = Mock(spec=ParameterOverrideExtractor)
        dummy_override = ParameterOverride(kind="named", param_name="DUMMY_PARAM")
        mock_param_extractor.extract.return_value = ([dummy_override], "named")

        mock_conn_extractor = Mock(spec=PortConnectionExtractor)
        dummy_conn = PortConnection(kind="named", port_name="dummy_port")
        mock_conn_extractor.extract.return_value = ([dummy_conn], "named")

        handler = HierarchyInstantiationHandler(
            parameter_extractor=mock_param_extractor,
            connection_extractor=mock_conn_extractor,
        )

        tree = parse_text("module top; child u_inst(); endmodule\n")
        inst_node = tree.root.members[0]
        vnode = SyntaxVNode(inst_node, tree)

        table = SymbolTable()
        top_scope = Scope(kind="module", name="top")
        table.register_module("top", top_scope)
        ctx = Context(scope=top_scope)

        handler.update_context(ctx, vnode, table)

        mock_param_extractor.extract.assert_called_once_with(vnode.raw, vnode.tree, ctx.scope())
        mock_conn_extractor.extract.assert_called_once()

        assert len(table.instantiations) == 1
        record = table.instantiations[0]
        assert record.parameter_overrides == [dummy_override]
        assert record.parameter_override_style == "named"
        assert record.connections == [dummy_conn]
        assert record.connection_style == "named"


