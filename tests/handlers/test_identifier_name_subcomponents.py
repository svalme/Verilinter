from __future__ import annotations

from unittest.mock import MagicMock, Mock
import pytest

from src.pkg.handlers.identifier_name import (
    DEFAULT_STRUCTURAL_NAME_PREDICATES,
    StructuralReferenceFilter,
    SymbolResolver,
    UseEventContext,
    UnresolvedNameRecorder,
    UseEventContextExtractor,
)
from src.pkg.handlers.identifier_name_handler import (
    IdentifierNameHandler,
    _is_structural_name_reference,
)
from src.pkg.parser.syntax_kinds import IDENTIFIER_NAME_KIND
from src.pkg.semantic.resolution import Resolution, ResolutionStatus
from src.pkg.semantic.scope_kinds import ScopeKind
from src.pkg.semantic.symbol import Symbol
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.vnodes.identifier_vnode import IdentifierNameVNode
from src.pkg.walk.context import Context
from tests.support.fakes import FakeNode


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


def _vnode() -> Mock:
    vnode = Mock(spec=IdentifierNameVNode)
    vnode.raw = FakeNode(IDENTIFIER_NAME_KIND)
    vnode.location = {"line": 1, "col": 1}
    return vnode


class TestSymbolResolver:
    def test_resolves_existing_symbol_in_scope(self) -> None:
        table = SymbolTable()
        ctx = Context(scope=table.global_scope)
        existing_symbol = Symbol(name="clk", kind="variable")
        ctx.scope().define(existing_symbol)

        resolution = SymbolResolver().resolve("clk", _vnode(), ctx, table)

        assert resolution.status is ResolutionStatus.RESOLVED
        assert resolution.symbol is existing_symbol

    def test_a_miss_is_an_implicit_net_under_default_nettype(self) -> None:
        table = SymbolTable()
        table.set_current_file("test.sv")
        ctx = Context(scope=table.global_scope)

        resolution = SymbolResolver().resolve("my_net", _vnode(), ctx, table)

        assert resolution.status is ResolutionStatus.UNRESOLVED_IMPLICIT_NET
        assert resolution.symbol is None

    def test_a_miss_is_undeclared_under_default_nettype_none(self) -> None:
        table = SymbolTable()
        table.set_current_file("test.sv")
        table.set_current_file_default_nettype_none(True)
        ctx = Context(scope=table.global_scope)

        resolution = SymbolResolver().resolve("my_var", _vnode(), ctx, table)

        assert resolution.status is ResolutionStatus.UNRESOLVED_UNDECLARED

    def test_resolving_does_not_change_the_symbol_table(self) -> None:
        table = SymbolTable()
        table.set_current_file("test.sv")
        ctx = Context(scope=table.global_scope)

        SymbolResolver().resolve("my_net", _vnode(), ctx, table)

        assert ctx.scope().lookup("my_net") is None
        assert table.unresolved_references == []

    def test_package_qualified_resolution_existing_and_missing(self) -> None:
        table = SymbolTable()
        ctx = Context(scope=table.global_scope)

        # Register package and symbol in package scope
        from src.pkg.semantic.scope import Scope
        pkg_scope = Scope(kind="package", name="my_pkg")
        pkg_symbol = Symbol(name="CONST_VAL", kind="parameter")
        pkg_scope.define(pkg_symbol)
        table.register_package("my_pkg", pkg_scope)

        vnode = _vnode()

        # Case 1: Injected qualifier finds registered package with matching symbol
        resolver = SymbolResolver(qualifier_fn=lambda raw: "my_pkg")
        resolved = resolver.resolve("CONST_VAL", vnode, ctx, table)
        assert resolved.status is ResolutionStatus.RESOLVED
        assert resolved.symbol is pkg_symbol

        # Case 2: Package exists, symbol does not exist in package
        assert resolver.resolve("UNKNOWN_VAL", vnode, ctx, table).status is ResolutionStatus.UNRESOLVABLE_HERE

        # Case 3: Injected qualifier returns unregistered package
        resolver_unregistered = SymbolResolver(qualifier_fn=lambda raw: "unregistered_pkg")
        assert resolver_unregistered.resolve("ANY", vnode, ctx, table).status is ResolutionStatus.UNRESOLVABLE_HERE


class TestUnresolvedNameRecorder:
    def test_resolved_name_returns_its_symbol_and_records_nothing(self) -> None:
        table = SymbolTable()
        ctx = Context(scope=table.global_scope)
        symbol = Symbol(name="clk", kind="variable")

        placeholder = UnresolvedNameRecorder().record(
            "clk", Resolution(ResolutionStatus.RESOLVED, symbol), _vnode(), ctx, table
        )

        assert placeholder is symbol
        assert table.unresolved_references == []

    def test_implicit_net_gets_a_placeholder_and_a_reference(self) -> None:
        table = SymbolTable()
        ctx = Context(scope=table.global_scope)

        placeholder = UnresolvedNameRecorder().record(
            "n", Resolution(ResolutionStatus.UNRESOLVED_IMPLICIT_NET), _vnode(), ctx, table
        )

        assert placeholder is not None
        assert placeholder.kind == "implicit_net"
        assert ctx.scope().lookup("n") is placeholder
        assert [(r.name, r.status) for r in table.unresolved_references] == [("n", ResolutionStatus.UNRESOLVED_IMPLICIT_NET)]

    def test_undeclared_name_gets_a_variable_placeholder(self) -> None:
        table = SymbolTable()
        ctx = Context(scope=table.global_scope)

        placeholder = UnresolvedNameRecorder().record(
            "v", Resolution(ResolutionStatus.UNRESOLVED_UNDECLARED), _vnode(), ctx, table
        )

        assert placeholder is not None
        assert placeholder.kind == "variable"
        assert table.unresolved_references[0].status is ResolutionStatus.UNRESOLVED_UNDECLARED

    def test_unresolvable_name_is_recorded_without_a_placeholder(self) -> None:
        table = SymbolTable()
        ctx = Context(scope=table.global_scope)

        placeholder = UnresolvedNameRecorder().record(
            "FOO", Resolution(ResolutionStatus.UNRESOLVABLE_HERE), _vnode(), ctx, table
        )

        assert placeholder is None
        assert ctx.scope().lookup("FOO") is None
        assert not table.unresolved_references[0].is_unresolved

    def test_placeholder_lives_in_the_enclosing_module_not_the_generate_block(self) -> None:
        table = SymbolTable()
        module = table.new_scope(ScopeKind.MODULE, name="m")
        block = table.new_scope(ScopeKind.GENERATE_BLOCK, name="g")
        ctx = Context(scope=block)

        placeholder = UnresolvedNameRecorder().record(
            "n", Resolution(ResolutionStatus.UNRESOLVED_IMPLICIT_NET), _vnode(), ctx, table
        )

        assert module.lookup("n") is placeholder
        assert block.lookup("n") is None


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
            "write_region": (),
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
        vnode.raw = FakeNode(IDENTIFIER_NAME_KIND)

        ctx = Context(scope=SymbolTable().global_scope)
        table = SymbolTable()

        res_ctx = handler.update_context(ctx, vnode, table)
        assert res_ctx is not ctx
        mock_filter.is_structural_reference.assert_not_called()
        mock_resolver.resolve.assert_not_called()
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
        vnode.raw = FakeNode(IDENTIFIER_NAME_KIND)

        ctx = Context(scope=SymbolTable().global_scope)
        table = SymbolTable()

        res_ctx = handler.update_context(ctx, vnode, table)
        mock_filter.is_structural_reference.assert_called_once_with(vnode.raw)
        mock_resolver.resolve.assert_not_called()
        mock_extractor.extract.assert_not_called()

    def test_skips_when_symbol_unresolved_package_qualifier(self) -> None:
        mock_filter = Mock(spec=StructuralReferenceFilter)
        mock_filter.is_structural_reference.return_value = False
        mock_resolver = Mock(spec=SymbolResolver)
        mock_resolver.resolve.return_value = Resolution(ResolutionStatus.UNRESOLVABLE_HERE)
        mock_extractor = Mock(spec=UseEventContextExtractor)

        handler = IdentifierNameHandler(
            filter=mock_filter,
            resolver=mock_resolver,
            extractor=mock_extractor,
        )

        vnode = Mock(spec=IdentifierNameVNode)
        vnode.identifier_name = "pkg_item"
        vnode.raw = FakeNode(IDENTIFIER_NAME_KIND)

        ctx = Context(scope=SymbolTable().global_scope)
        table = SymbolTable()

        res_ctx = handler.update_context(ctx, vnode, table)
        mock_resolver.resolve.assert_called_once_with("pkg_item", vnode, ctx, table)
        mock_extractor.extract.assert_not_called()

    def test_full_successful_orchestration(self) -> None:
        mock_filter = Mock(spec=StructuralReferenceFilter)
        mock_filter.is_structural_reference.return_value = False

        mock_symbol = Mock(spec=Symbol)
        mock_resolver = Mock(spec=SymbolResolver)
        mock_resolver.resolve.return_value = Resolution(ResolutionStatus.RESOLVED, mock_symbol)

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
        vnode.raw = FakeNode(IDENTIFIER_NAME_KIND)
        vnode.location = {"file": "test.sv", "line": 5, "col": 10}

        ctx = Context(scope=SymbolTable().global_scope)
        table = SymbolTable()

        res_ctx = handler.update_context(ctx, vnode, table)
        mock_filter.is_structural_reference.assert_called_once_with(vnode.raw)
        mock_resolver.resolve.assert_called_once_with("valid_sig", vnode, ctx, table)
        mock_extractor.extract.assert_called_once_with(vnode, ctx, table)
        mock_symbol.add_use.assert_called_once_with(
            vnode.location,
            **event_context.to_use_kwargs(),
        )
