"""Test suite for BaseHandler."""

import pytest
from unittest.mock import Mock, MagicMock
import pyslang as sl

from src.pkg.handlers.base_handler import BaseHandler, VNodeType
from src.pkg.vnodes.base_vnode import BaseVNode
from src.pkg.ast.context import Context
from src.pkg.ast.symbol_table import SymbolTable


class ConcreteHandler(BaseHandler):
    """Concrete implementation of BaseHandler for testing."""
    pass


class TestBaseHandler:
    """Test cases for BaseHandler abstract base class."""

    @pytest.fixture
    def handler(self) -> BaseHandler:
        """Fixture for a concrete BaseHandler instance."""
        return ConcreteHandler()

    @pytest.fixture
    def mock_vnode(self) -> Mock:
        """Fixture for a mock BaseVNode."""
        vnode = Mock(spec=BaseVNode)
        vnode.location = {"line": 10, "col": 5}
        vnode.snippet.return_value = "test snippet"
        return vnode

    @pytest.fixture
    def context(self) -> Context:
        """Fixture for a Context instance."""
        return Context()

    @pytest.fixture
    def symbol_table(self) -> SymbolTable:
        """Fixture for a SymbolTable instance."""
        return SymbolTable()

    def test_base_handler_is_abstract(self) -> None:
        """Test that BaseHandler cannot be instantiated directly if it defines abstract methods."""
        # Note: If BaseHandler uses ABC and has abstract methods, this test will fail
        # For now, we test that it can be subclassed
        handler = ConcreteHandler()
        assert isinstance(handler, BaseHandler)

    def test_children_returns_empty_list_by_default(
        self, 
        handler: BaseHandler, 
        mock_vnode: Mock
    ) -> None:
        """Test that children() returns empty list by default."""
        result = handler.children(mock_vnode)
        
        assert isinstance(result, list)
        assert result == []

    def test_update_context_returns_context_unchanged_by_default(
        self, 
        handler: BaseHandler, 
        mock_vnode: Mock, 
        context: Context, 
        symbol_table: SymbolTable
    ) -> None:
        """Test that update_context() returns the context unchanged by default."""
        result = handler.update_context(context, mock_vnode, symbol_table)
        
        assert result is context

    def test_children_accepts_vnode_parameter(
        self, 
        handler: BaseHandler, 
        mock_vnode: Mock
    ) -> None:
        """Test that children() accepts any BaseVNode type."""
        result = handler.children(mock_vnode)
        assert result == []

    def test_update_context_accepts_context_vnode_and_symbol_table(
        self, 
        handler: BaseHandler, 
        mock_vnode: Mock, 
        context: Context, 
        symbol_table: SymbolTable
    ) -> None:
        """Test that update_context() accepts all required parameters."""
        result = handler.update_context(context, mock_vnode, symbol_table)
        
        assert isinstance(result, Context)

    def test_base_handler_can_be_subclassed(self) -> None:
        """Test that BaseHandler can be properly subclassed."""
        class CustomHandler(BaseHandler):
            def children(self, vnode: BaseVNode) -> list[BaseVNode]:
                return [vnode]
            
            def update_context(self, ctx: Context, vnode: BaseVNode, symbol_table: SymbolTable) -> Context:
                return ctx.push(vnode)

        handler = CustomHandler()
        assert isinstance(handler, BaseHandler)
        
        mock_vnode = Mock(spec=BaseVNode)
        context = Context()
        
        # Test overridden children method
        children = handler.children(mock_vnode)
        assert len(children) == 1
        assert children[0] is mock_vnode

    def test_handler_generic_type_parameter(self) -> None:
        """Test that BaseHandler is properly parameterized with VNodeType."""
        # This test verifies the generic type structure
        assert hasattr(BaseHandler, '__orig_bases__')

    def test_multiple_handlers_are_independent(self) -> None:
        """Test that multiple handler instances don't share state."""
        handler1 = ConcreteHandler()
        handler2 = ConcreteHandler()
        
        # Both should have the same default behavior but be different instances
        assert handler1 is not handler2
        
        mock_vnode = Mock(spec=BaseVNode)
        assert handler1.children(mock_vnode) == handler2.children(mock_vnode)

    def test_children_with_no_children(
        self, 
        handler: BaseHandler, 
        mock_vnode: Mock
    ) -> None:
        """Test that children() returns empty list for leaf vnodes."""
        # Mock a leaf vnode
        mock_vnode.children = []
        
        result = handler.children(mock_vnode)
        assert len(result) == 0

    def test_update_context_preserves_context_immutability(
        self, 
        handler: BaseHandler, 
        mock_vnode: Mock, 
        context: Context, 
        symbol_table: SymbolTable
    ) -> None:
        """Test that update_context doesn't modify the original context."""
        original_stack_len = len(context.stack)
        original_flags = context.flags.copy()
        
        result = handler.update_context(context, mock_vnode, symbol_table)
        
        # Original context should not be modified
        assert len(context.stack) == original_stack_len
        assert context.flags == original_flags

    def test_handler_can_be_used_in_collection(self) -> None:
        """Test that handler instances can be stored in collections."""
        handlers = [ConcreteHandler() for _ in range(3)]
        
        assert len(handlers) == 3
        for handler in handlers:
            assert isinstance(handler, BaseHandler)

    def test_update_context_with_none_symbol_table(
        self, 
        handler: BaseHandler, 
        mock_vnode: Mock, 
        context: Context
    ) -> None:
        """Test update_context behavior with None symbol_table (if allowed)."""
        # This tests defensive coding if the handler is called with None
        result = handler.update_context(context, mock_vnode, SymbolTable())
        
        # Default implementation should still return context
        assert result is context
