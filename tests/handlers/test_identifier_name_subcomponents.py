from __future__ import annotations

from unittest.mock import MagicMock, Mock
import pytest

from src.pkg.handlers.identifier_name import (
    DEFAULT_STRUCTURAL_NAME_PREDICATES,
    StructuralReferenceFilter,
    SymbolResolver,
    UseEventContext,
    UseEventContextExtractor,
)
from src.pkg.handlers.identifier_name_handler import (
    IdentifierNameHandler,
    _is_structural_name_reference,
)
from src.pkg.semantic.symbol import Symbol
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.vnodes.identifier_vnode import IdentifierNameVNode
from src.pkg.walk.context import Context


class TestStructuralReferenceFilter:
    def test_default_predicates_present(self) -> None:
        filter_obj = StructuralReferenceFilter()
        assert len(filter_obj.predicates) == len(DEFAULT_STRUCTURAL_NAME_PREDICATES)
        assert len(filter_obj.predicates) >= 10

    def test_custom_predicates_injection(self) -> None:
        custom_pred = lambda raw: getattr(raw, "is_special", False)
        filter_obj = StructuralReferenceFilter(predicates=[custom_pred])
        assert len(filter_obj.predicates) == 1

        mock_raw_match = Mock(is_special=True)
        mock_raw_no_match = Mock(is_special=False)

        assert filter_obj.is_structural_reference(mock_raw_match) is True
        assert filter_obj.is_structural_reference(mock_raw_no_match) is False

    def test_backward_compatibility_helper(self) -> None:
        # None of the default predicates match a plain Mock object
        mock_raw = Mock()
        assert _is_structural_name_reference(mock_raw) is False


class TestSymbolResolver:
    def test_resolves_existing_symbol_in_scope(self) -> None:
        table = SymbolTable()
        ctx = Context(scope=table.global_scope)
        existing_symbol = Symbol(name="clk", kind="wire")
        ctx.scope().define(existing_symbol)

        vnode = Mock(spec=IdentifierNameVNode)
        vnode.raw = Mock()

        resolver = SymbolResolver()
        resolved = resolver.resolve_or_create("clk", vnode, ctx, table)
        assert resolved is existing_symbol

    def test_synthesizes_implicit_net_under_default_nettype(self) -> None:
        table = SymbolTable()
        table.set_current_file("test.sv")
        ctx = Context(scope=table.global_scope)

        vnode = Mock(spec=IdentifierNameVNode)
        vnode.raw = Mock()

        resolver = SymbolResolver()
        symbol = resolver.resolve_or_create("my_net", vnode, ctx, table)
        assert symbol is not None
        assert symbol.name == "my_net"
        assert symbol.kind == "implicit_net"
        assert symbol.is_implicit is True
        assert ctx.scope().lookup("my_net") is symbol

    def test_synthesizes_variable_under_default_nettype_none(self) -> None:
        table = SymbolTable()
        table.set_current_file("test.sv")
        table.set_current_file_default_nettype_none(True)
        ctx = Context(scope=table.global_scope)

        vnode = Mock(spec=IdentifierNameVNode)
        vnode.raw = Mock()

        resolver = SymbolResolver()
        symbol = resolver.resolve_or_create("my_var", vnode, ctx, table)
        assert symbol is not None
        assert symbol.name == "my_var"
        assert symbol.kind == "variable"
        assert symbol.is_implicit is False
        assert ctx.scope().lookup("my_var") is symbol

    def test_package_qualified_resolution_existing_and_missing(self) -> None:
        table = SymbolTable()
        ctx = Context(scope=table.global_scope)

        # Register package and symbol in package scope
        from src.pkg.semantic.scope import Scope
        pkg_scope = Scope(kind="package", name="my_pkg")
        pkg_symbol = Symbol(name="CONST_VAL", kind="parameter")
        pkg_scope.define(pkg_symbol)
        table.register_package("my_pkg", pkg_scope)

        vnode = Mock(spec=IdentifierNameVNode)
        vnode.raw = Mock()

        # Case 1: Injected qualifier finds registered package with matching symbol
        resolver = SymbolResolver(qualifier_fn=lambda raw: "my_pkg")
        resolved = resolver.resolve_or_create("CONST_VAL", vnode, ctx, table)
        assert resolved is pkg_symbol

        # Case 2: Package exists, symbol does not exist in package
        resolved_missing = resolver.resolve_or_create("UNKNOWN_VAL", vnode, ctx, table)
        assert resolved_missing is None

        # Case 3: Injected qualifier returns unregistered package
        resolver_unregistered = SymbolResolver(qualifier_fn=lambda raw: "unregistered_pkg")
        resolved_pkg_missing = resolver_unregistered.resolve_or_create("ANY", vnode, ctx, table)
        assert resolved_pkg_missing is None


class TestUseEventContext:
    def test_to_use_kwargs(self) -> None:
        ctx_info = UseEventContext(
            is_read=True,
            is_write=False,
            driver_id="always:test.sv:10:5",
            driver_location={"file": "test.sv", "line": 10, "col": 5},
            branch_signature=(("if", 1),),
            statement_id="stmt:test.sv:12:1",
            in_port_connection=False,
            is_nonblocking_write=False,
            loop_ids=("for:test.sv:8:2",),
        )

        kwargs = ctx_info.to_use_kwargs()
        assert kwargs == {
            "read": True,
            "write": False,
            "driver_id": "always:test.sv:10:5",
            "driver_location": {"file": "test.sv", "line": 10, "col": 5},
            "branch_signature": (("if", 1),),
            "statement_id": "stmt:test.sv:12:1",
            "in_port_connection": False,
            "is_nonblocking_write": False,
            "loop_ids": ("for:test.sv:8:2",),
        }


class TestIdentifierNameHandlerOrchestration:
    def test_skips_when_empty_identifier_name(self) -> None:
        mock_filter = Mock(spec=StructuralReferenceFilter)
        mock_resolver = Mock(spec=SymbolResolver)
        mock_extractor = Mock(spec=UseEventContextExtractor)

        handler = IdentifierNameHandler(
            filter=mock_filter,
            resolver=mock_resolver,
            extractor=mock_extractor,
        )

        vnode = Mock(spec=IdentifierNameVNode)
        vnode.identifier_name = ""
        vnode.raw = Mock()

        ctx = Context(scope=SymbolTable().global_scope)
        table = SymbolTable()

        res_ctx = handler.update_context(ctx, vnode, table)
        assert res_ctx is not ctx
        mock_filter.is_structural_reference.assert_not_called()
        mock_resolver.resolve_or_create.assert_not_called()
        mock_extractor.extract.assert_not_called()

    def test_skips_when_structural_reference(self) -> None:
        mock_filter = Mock(spec=StructuralReferenceFilter)
        mock_filter.is_structural_reference.return_value = True
        mock_resolver = Mock(spec=SymbolResolver)
        mock_extractor = Mock(spec=UseEventContextExtractor)

        handler = IdentifierNameHandler(
            filter=mock_filter,
            resolver=mock_resolver,
            extractor=mock_extractor,
        )

        vnode = Mock(spec=IdentifierNameVNode)
        vnode.identifier_name = "data_t"
        vnode.raw = Mock()

        ctx = Context(scope=SymbolTable().global_scope)
        table = SymbolTable()

        res_ctx = handler.update_context(ctx, vnode, table)
        mock_filter.is_structural_reference.assert_called_once_with(vnode.raw)
        mock_resolver.resolve_or_create.assert_not_called()
        mock_extractor.extract.assert_not_called()

    def test_skips_when_symbol_unresolved_package_qualifier(self) -> None:
        mock_filter = Mock(spec=StructuralReferenceFilter)
        mock_filter.is_structural_reference.return_value = False
        mock_resolver = Mock(spec=SymbolResolver)
        mock_resolver.resolve_or_create.return_value = None
        mock_extractor = Mock(spec=UseEventContextExtractor)

        handler = IdentifierNameHandler(
            filter=mock_filter,
            resolver=mock_resolver,
            extractor=mock_extractor,
        )

        vnode = Mock(spec=IdentifierNameVNode)
        vnode.identifier_name = "pkg_item"
        vnode.raw = Mock()

        ctx = Context(scope=SymbolTable().global_scope)
        table = SymbolTable()

        res_ctx = handler.update_context(ctx, vnode, table)
        mock_resolver.resolve_or_create.assert_called_once_with("pkg_item", vnode, ctx, table)
        mock_extractor.extract.assert_not_called()

    def test_full_successful_orchestration(self) -> None:
        mock_filter = Mock(spec=StructuralReferenceFilter)
        mock_filter.is_structural_reference.return_value = False

        mock_symbol = Mock(spec=Symbol)
        mock_resolver = Mock(spec=SymbolResolver)
        mock_resolver.resolve_or_create.return_value = mock_symbol

        event_context = UseEventContext(
            is_read=True,
            is_write=False,
            driver_id=None,
            driver_location=None,
            branch_signature=None,
            statement_id="stmt:test.sv:5:1",
            in_port_connection=False,
            is_nonblocking_write=False,
            loop_ids=(),
        )
        mock_extractor = Mock(spec=UseEventContextExtractor)
        mock_extractor.extract.return_value = event_context

        handler = IdentifierNameHandler(
            filter=mock_filter,
            resolver=mock_resolver,
            extractor=mock_extractor,
        )

        vnode = Mock(spec=IdentifierNameVNode)
        vnode.identifier_name = "valid_sig"
        vnode.raw = Mock()
        vnode.location = {"file": "test.sv", "line": 5, "col": 10}

        ctx = Context(scope=SymbolTable().global_scope)
        table = SymbolTable()

        res_ctx = handler.update_context(ctx, vnode, table)
        mock_filter.is_structural_reference.assert_called_once_with(vnode.raw)
        mock_resolver.resolve_or_create.assert_called_once_with("valid_sig", vnode, ctx, table)
        mock_extractor.extract.assert_called_once_with(vnode, ctx, table)
        mock_symbol.add_use.assert_called_once_with(
            vnode.location,
            **event_context.to_use_kwargs(),
        )
