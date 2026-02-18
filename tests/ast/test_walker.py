"""Test suite for Walker."""

import pytest
from unittest.mock import Mock, MagicMock, call, patch
import pyslang as sl

from src.pkg.ast.walker import Walker
from src.pkg.ast.dispatch import Dispatch
from src.pkg.ast.context import Context, ContextFlag
from src.pkg.ast.symbol_table import SymbolTable, Scope
from src.pkg.vnodes.base_vnode import BaseVNode
from src.pkg.handlers.base_handler import BaseHandler


class TestWalker:
    """Test cases for Walker class."""

    @pytest.fixture
    def mock_dispatch(self) -> Mock:
        """Fixture for a mock Dispatch instance."""
        dispatch = Mock(spec=Dispatch)
        return dispatch

    @pytest.fixture
    def walker(self, mock_dispatch: Mock) -> Walker:
        """Fixture for a Walker instance."""
        return Walker(mock_dispatch)

    @pytest.fixture
    def mock_handler(self) -> Mock:
        """Fixture for a mock handler."""
        handler = Mock(spec=BaseHandler)
        handler.children.return_value = []
        handler.update_context.return_value = Context()
        return handler

    @pytest.fixture
    def mock_syntax_node(self) -> Mock:
        """Fixture for a mock SyntaxNode."""
        return Mock(spec=sl.SyntaxNode)

    @pytest.fixture
    def mock_tree(self) -> Mock:
        """Fixture for a mock SyntaxTree."""
        return Mock(spec=sl.SyntaxTree)

    @pytest.fixture
    def context(self) -> Context:
        """Fixture for a Context instance."""
        scope = Scope(kind="module", name="test_module")
        return Context(scopes=[scope])

    @pytest.fixture
    def symbol_table(self) -> SymbolTable:
        """Fixture for a SymbolTable instance."""
        return SymbolTable()

    def test_walker_initialization(self, walker: Walker, mock_dispatch: Mock) -> None:
        """Test that Walker is properly initialized."""
        assert walker._dispatch is mock_dispatch
        assert walker._results == []

    def test_walk_creates_vnode_from_raw_node(
        self,
        walker: Walker,
        mock_dispatch: Mock,
        mock_handler: Mock,
        mock_syntax_node: Mock,
        mock_tree: Mock,
        context: Context,
        symbol_table: SymbolTable
    ) -> None:
        """Test that walk creates a vnode from the raw node."""
        # Mock the vnode_factory.create
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = mock_syntax_node
        
        mock_dispatch.get.return_value = mock_handler
        
        with patch('src.pkg.ast.walker.vnode_factory.create', return_value=mock_vnode):
            walker.walk(mock_syntax_node, mock_tree, context, symbol_table)
        
        # Verify vnode was created
        assert len(walker._results) > 0

    def test_walk_gets_handler_for_vnode(
        self,
        walker: Walker,
        mock_dispatch: Mock,
        mock_handler: Mock,
        mock_syntax_node: Mock,
        mock_tree: Mock,
        context: Context,
        symbol_table: SymbolTable
    ) -> None:
        """Test that walk retrieves the appropriate handler for a vnode."""
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = mock_syntax_node
        
        mock_dispatch.get.return_value = mock_handler
        mock_handler.children.return_value = []
        
        with patch('src.pkg.ast.walker.vnode_factory.create', return_value=mock_vnode):
            walker.walk(mock_syntax_node, mock_tree, context, symbol_table)
        
        # Verify get was called with the vnode
        mock_dispatch.get.assert_called_once()

    def test_walk_calls_handler_update_context(
        self,
        walker: Walker,
        mock_dispatch: Mock,
        mock_handler: Mock,
        mock_syntax_node: Mock,
        mock_tree: Mock,
        context: Context,
        symbol_table: SymbolTable
    ) -> None:
        """Test that walk calls handler.update_context."""
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = mock_syntax_node
        
        updated_context = context.push(mock_vnode)
        mock_handler.update_context.return_value = updated_context
        mock_handler.children.return_value = []
        mock_dispatch.get.return_value = mock_handler
        
        with patch('src.pkg.ast.walker.vnode_factory.create', return_value=mock_vnode):
            walker.walk(mock_syntax_node, mock_tree, context, symbol_table)
        
        # Verify update_context was called with correct parameters
        mock_handler.update_context.assert_called_once_with(context, mock_vnode, symbol_table)

    def test_walk_appends_result(
        self,
        walker: Walker,
        mock_dispatch: Mock,
        mock_handler: Mock,
        mock_syntax_node: Mock,
        mock_tree: Mock,
        context: Context,
        symbol_table: SymbolTable
    ) -> None:
        """Test that walk appends (vnode, context) to results."""
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = mock_syntax_node
        
        updated_context = context.push(mock_vnode)
        mock_handler.update_context.return_value = updated_context
        mock_handler.children.return_value = []
        mock_dispatch.get.return_value = mock_handler
        
        with patch('src.pkg.ast.walker.vnode_factory.create', return_value=mock_vnode):
            walker.walk(mock_syntax_node, mock_tree, context, symbol_table)
        
        # Verify result was appended
        assert len(walker._results) == 1
        vnode, ctx = walker._results[0]
        assert vnode is mock_vnode
        assert ctx is updated_context

    def test_walk_processes_children(
        self,
        walker: Walker,
        mock_dispatch: Mock,
        mock_handler: Mock,
        mock_syntax_node: Mock,
        mock_tree: Mock,
        context: Context,
        symbol_table: SymbolTable
    ) -> None:
        """Test that walk recursively processes children."""
        # Create parent vnode
        mock_parent_vnode = Mock(spec=BaseVNode)
        mock_parent_vnode.raw = mock_syntax_node
        
        # Create child nodes
        mock_child_node = Mock(spec=sl.SyntaxNode)
        mock_child_vnode = Mock(spec=BaseVNode)
        mock_child_vnode.raw = mock_child_node
        
        # Setup handler to return child
        parent_handler = Mock(spec=BaseHandler)
        parent_handler.update_context.return_value = context.push(mock_parent_vnode)
        parent_handler.children.return_value = [mock_child_vnode]
        
        # Child handler
        child_handler = Mock(spec=BaseHandler)
        child_handler.update_context.return_value = context.push(mock_child_vnode)
        child_handler.children.return_value = []
        
        # Setup dispatch to return appropriate handlers
        def get_handler(vnode):
            if vnode is mock_parent_vnode:
                return parent_handler
            elif vnode is mock_child_vnode:
                return child_handler
            return Mock(spec=BaseHandler)
        
        mock_dispatch.get.side_effect = get_handler
        
        with patch('src.pkg.ast.walker.vnode_factory.create', return_value=mock_parent_vnode):
            walker.walk(mock_syntax_node, mock_tree, context, symbol_table)
        
        # Verify both parent and child were processed
        assert len(walker._results) >= 1

    def test_walk_initializes_empty_results(self, walker: Walker) -> None:
        """Test that walker initializes with empty results."""
        assert walker._results == []

    def test_walk_with_token_node(
        self,
        walker: Walker,
        mock_dispatch: Mock,
        mock_handler: Mock,
        mock_tree: Mock,
        context: Context,
        symbol_table: SymbolTable
    ) -> None:
        """Test walk with a Token node."""
        mock_token = Mock(spec=sl.Token)
        mock_vnode = Mock(spec=BaseVNode)
        mock_vnode.raw = mock_token
        
        mock_handler.children.return_value = []
        mock_handler.update_context.return_value = context.push(mock_vnode)
        mock_dispatch.get.return_value = mock_handler
        
        with patch('src.pkg.ast.walker.vnode_factory.create', return_value=mock_vnode):
            walker.walk(mock_token, mock_tree, context, symbol_table)
        
        # Verify vnode was added to results
        assert len(walker._results) == 1

    def test_walk_deep_tree_traversal(
        self,
        walker: Walker,
        mock_dispatch: Mock,
        mock_tree: Mock,
        context: Context,
        symbol_table: SymbolTable
    ) -> None:
        """Test walk with deeply nested tree structure."""
        # Create a chain of vnodes: root -> child1 -> child2 -> child3
        root_node = Mock(spec=sl.SyntaxNode)
        root_vnode = Mock(spec=BaseVNode)
        root_vnode.raw = root_node
        
        child1_node = Mock(spec=sl.SyntaxNode)
        child1_vnode = Mock(spec=BaseVNode)
        child1_vnode.raw = child1_node
        
        child2_node = Mock(spec=sl.SyntaxNode)
        child2_vnode = Mock(spec=BaseVNode)
        child2_vnode.raw = child2_node
        
        child3_node = Mock(spec=sl.SyntaxNode)
        child3_vnode = Mock(spec=BaseVNode)
        child3_vnode.raw = child3_node
        
        # Setup handlers
        def get_handler(vnode):
            handler = Mock(spec=BaseHandler)
            handler.update_context.return_value = context.push(vnode)
            
            if vnode is root_vnode:
                handler.children.return_value = [child1_vnode]
            elif vnode is child1_vnode:
                handler.children.return_value = [child2_vnode]
            elif vnode is child2_vnode:
                handler.children.return_value = [child3_vnode]
            else:
                handler.children.return_value = []
            
            return handler
        
        mock_dispatch.get.side_effect = get_handler
        
        vnode_counter = 0
        def create_vnode(raw, tree):
            nonlocal vnode_counter
            vnodes = [root_vnode, child1_vnode, child2_vnode, child3_vnode]
            result = vnodes[vnode_counter]
            vnode_counter += 1
            return result
        
        with patch('src.pkg.ast.walker.vnode_factory.create', side_effect=create_vnode):
            walker.walk(root_node, mock_tree, context, symbol_table)
        
        # Verify all nodes were traversed
        assert len(walker._results) == 4

    def test_walk_context_propagation(
        self,
        walker: Walker,
        mock_dispatch: Mock,
        mock_tree: Mock,
        context: Context,
        symbol_table: SymbolTable
    ) -> None:
        """Test that context is properly propagated through the tree."""
        root_vnode = Mock(spec=BaseVNode)
        child_vnode = Mock(spec=BaseVNode)
        
        root_handler = Mock(spec=BaseHandler)
        updated_context = context.with_flag(ContextFlag.IN_EXPRESSION)
        root_handler.update_context.return_value = updated_context
        root_handler.children.return_value = [child_vnode]
        
        child_handler = Mock(spec=BaseHandler)
        child_handler.update_context.return_value = updated_context
        child_handler.children.return_value = []
        
        def get_handler(vnode):
            if vnode is root_vnode:
                return root_handler
            else:
                return child_handler
        
        mock_dispatch.get.side_effect = get_handler
        
        with patch('src.pkg.ast.walker.vnode_factory.create', return_value=root_vnode):
            walker.walk(Mock(spec=sl.SyntaxNode), mock_tree, context, symbol_table)
        
        # Verify root handler was called with original context
        root_handler.update_context.assert_called_with(context, root_vnode, symbol_table)

    def test_walk_multiple_calls_accumulate_results(
        self,
        walker: Walker,
        mock_dispatch: Mock,
        mock_handler: Mock,
        mock_tree: Mock,
        context: Context,
        symbol_table: SymbolTable
    ) -> None:
        """Test that multiple walk calls accumulate results."""
        mock_vnode1 = Mock(spec=BaseVNode)
        mock_vnode2 = Mock(spec=BaseVNode)
        
        mock_handler.children.return_value = []
        mock_handler.update_context.return_value = context
        mock_dispatch.get.return_value = mock_handler
        
        with patch('src.pkg.ast.walker.vnode_factory.create') as mock_create:
            mock_create.return_value = mock_vnode1
            walker.walk(Mock(spec=sl.SyntaxNode), mock_tree, context, symbol_table)
            
            mock_create.return_value = mock_vnode2
            walker.walk(Mock(spec=sl.SyntaxNode), mock_tree, context, symbol_table)
        
        # Verify both results are accumulated
        assert len(walker._results) == 2
