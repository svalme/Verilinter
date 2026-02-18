"""Test suite for VNodeFactory."""

import pytest
from unittest.mock import Mock, MagicMock, patch
import pyslang as sl

from src.pkg.vnodes.vnode_factory import VNodeFactory, vnode_factory
from src.pkg.vnodes.base_vnode import BaseVNode
from src.pkg.vnodes.token_vnode import TokenVNode
from src.pkg.vnodes.syntax_vnode import SyntaxVNode


class TestVNodeFactory:
    """Test cases for VNodeFactory class."""

    def test_vnode_factory_is_singleton(self) -> None:
        """Test that vnode_factory is an instance of VNodeFactory."""
        assert isinstance(vnode_factory, VNodeFactory)

    def test_register_decorator_stores_vnode_class(self) -> None:
        """Test that register decorator stores vnode classes in the registry."""
        # Create a mock raw type
        mock_type = Mock()
        
        # Create a test vnode class
        class TestVNode(BaseVNode):
            pass

        # Register the vnode class
        registered = VNodeFactory.register(mock_type)(TestVNode)
        
        # Verify the class was returned
        assert registered is TestVNode
        
        # Verify it's in the registry
        assert VNodeFactory._node_map.get(mock_type) is TestVNode

    def test_create_returns_registered_vnode_for_token(self) -> None:
        """Test that create returns the registered vnode class for a Token."""
        # Create mock objects
        mock_token = Mock(spec=sl.Token)
        mock_tree = Mock(spec=sl.SyntaxTree)
        
        # Create a mock vnode class
        mock_vnode_class = Mock()
        mock_vnode_instance = Mock(spec=BaseVNode)
        mock_vnode_class.return_value = mock_vnode_instance
        
        # Register the vnode class
        VNodeFactory._node_map[type(mock_token)] = mock_vnode_class
        
        # Call create
        result = VNodeFactory.create(mock_token, mock_tree)
        
        # Verify the vnode class was instantiated with the correct arguments
        mock_vnode_class.assert_called_once_with(mock_token, mock_tree)
        assert result is mock_vnode_instance

    def test_create_returns_default_token_vnode_for_unregistered_token(self) -> None:
        """Test that create returns TokenVNode for unregistered Token types."""
        # Create mock objects
        mock_token = Mock(spec=sl.Token)
        mock_tree = Mock(spec=sl.SyntaxTree)
        
        # Ensure the token type is not in the registry
        VNodeFactory._node_map.pop(type(mock_token), None)
        
        # Call create
        result = VNodeFactory.create(mock_token, mock_tree)
        
        # Verify TokenVNode was returned
        assert isinstance(result, TokenVNode)
        assert result.raw is mock_token
        assert result.tree is mock_tree

    def test_create_returns_default_syntax_vnode_for_unregistered_syntax_node(self) -> None:
        """Test that create returns SyntaxVNode for unregistered SyntaxNode types."""
        # Create mock objects
        mock_syntax_node = Mock(spec=sl.SyntaxNode)
        mock_tree = Mock(spec=sl.SyntaxTree)
        
        # Ensure the syntax node type is not in the registry
        VNodeFactory._node_map.pop(type(mock_syntax_node), None)
        
        # Call create
        result = VNodeFactory.create(mock_syntax_node, mock_tree)
        
        # Verify SyntaxVNode was returned
        assert isinstance(result, SyntaxVNode)
        assert result.raw is mock_syntax_node
        assert result.tree is mock_tree

    def test_create_with_registered_syntax_node_type(self) -> None:
        """Test create with a registered SyntaxNode type."""
        # Create mock objects
        mock_syntax_node = Mock(spec=sl.SyntaxNode)
        mock_tree = Mock(spec=sl.SyntaxTree)
        
        # Create a custom vnode class
        class CustomSyntaxVNode(SyntaxVNode):
            pass

        # Register the custom vnode class
        VNodeFactory._node_map[type(mock_syntax_node)] = CustomSyntaxVNode
        
        # Call create
        result = VNodeFactory.create(mock_syntax_node, mock_tree)
        
        # Verify the custom vnode class was used
        assert isinstance(result, CustomSyntaxVNode)
        assert result.raw is mock_syntax_node
        assert result.tree is mock_tree

    def test_node_map_is_empty_by_default(self) -> None:
        """Test that _node_map starts empty."""
        # Save the original map
        original_map = VNodeFactory._node_map.copy()
        
        # Clear the map
        VNodeFactory._node_map.clear()
        
        # Create with a mock token (should use default TokenVNode)
        mock_token = Mock(spec=sl.Token)
        mock_tree = Mock(spec=sl.SyntaxTree)
        result = VNodeFactory.create(mock_token, mock_tree)
        
        # Verify TokenVNode was returned as default
        assert isinstance(result, TokenVNode)
        
        # Restore the original map
        VNodeFactory._node_map = original_map

    def test_register_with_multiple_vnodes(self) -> None:
        """Test registering multiple vnode types."""
        # Create mock types
        mock_type1 = Mock(name="Type1")
        mock_type2 = Mock(name="Type2")
        
        # Create mock vnode classes
        class TestVNode1(BaseVNode):
            pass

        class TestVNode2(BaseVNode):
            pass

        # Register both
        VNodeFactory.register(mock_type1)(TestVNode1)
        VNodeFactory.register(mock_type2)(TestVNode2)
        
        # Verify both are in the registry
        assert VNodeFactory._node_map.get(mock_type1) is TestVNode1
        assert VNodeFactory._node_map.get(mock_type2) is TestVNode2

    def test_vnode_factory_shared_registry(self) -> None:
        """Test that all VNodeFactory instances share the same registry."""
        # Create two factory instances
        factory1 = VNodeFactory()
        factory2 = VNodeFactory()
        
        # They should share the same _node_map
        assert factory1._node_map is factory2._node_map
