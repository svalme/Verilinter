"""Test suite for IdentifierNameVNode."""

import pytest
from unittest.mock import Mock, MagicMock, patch
import pyslang as sl

from src.pkg.vnodes.identifier_vnode import IdentifierNameVNode
from src.pkg.vnodes.syntax_vnode import SyntaxVNode
from src.pkg.vnodes.vnode_factory import vnode_factory


class TestIdentifierNameVNode:
    """Test cases for IdentifierNameVNode class."""

    @pytest.fixture
    def mock_syntax_node(self) -> Mock:
        """Fixture for a mock SyntaxNode (IdentifierNameSyntax)."""
        node = Mock(spec=sl.IdentifierNameSyntax)
        mock_identifier = Mock()
        mock_identifier.value = "my_signal"
        node.identifier = mock_identifier
        node.__iter__ = Mock(return_value=iter([]))
        return node

    @pytest.fixture
    def mock_tree(self) -> Mock:
        """Fixture for a mock SyntaxTree."""
        return Mock(spec=sl.SyntaxTree)

    @pytest.fixture
    def vnode(self, mock_syntax_node: Mock, mock_tree: Mock) -> IdentifierNameVNode:
        """Fixture for an IdentifierNameVNode instance."""
        return IdentifierNameVNode(mock_syntax_node, mock_tree)

    def test_identifier_vnode_is_syntax_vnode(self, vnode: IdentifierNameVNode) -> None:
        """Test that IdentifierNameVNode is a subclass of SyntaxVNode."""
        assert isinstance(vnode, SyntaxVNode)

    def test_identifier_name_returns_correct_value(self, vnode: IdentifierNameVNode) -> None:
        """Test that identifier_name returns the correct identifier name."""
        name = vnode.identifier_name
        assert name == "my_signal"

    def test_vnode_stores_raw_node(self, vnode: IdentifierNameVNode, mock_syntax_node: Mock) -> None:
        """Test that vnode stores the raw syntax node."""
        assert vnode.raw is mock_syntax_node

    def test_vnode_stores_tree(self, vnode: IdentifierNameVNode, mock_tree: Mock) -> None:
        """Test that vnode stores the syntax tree."""
        assert vnode.tree is mock_tree

    def test_vnode_registered_in_factory(self) -> None:
        """Test that IdentifierNameVNode is registered in vnode_factory."""
        # Check if sl.IdentifierNameSyntax is in the registry
        assert sl.IdentifierNameSyntax in vnode_factory._node_map
        assert vnode_factory._node_map[sl.IdentifierNameSyntax] is IdentifierNameVNode

    def test_identifier_name_with_different_names(self, mock_syntax_node: Mock, mock_tree: Mock) -> None:
        """Test identifier_name with different identifier names."""
        test_names = ["signal_a", "bus", "clk", "reset", "data_in", "_private_var"]
        
        for name in test_names:
            mock_syntax_node.identifier.value = name
            vnode = IdentifierNameVNode(mock_syntax_node, mock_tree)
            assert vnode.identifier_name == name

    def test_vnode_inherits_from_syntax_vnode(self, vnode: IdentifierNameVNode) -> None:
        """Test that IdentifierNameVNode inherits SyntaxVNode properties."""       
        assert hasattr(vnode, 'snippet')
        assert hasattr(vnode, 'location')
        assert hasattr(vnode, 'children')
        assert hasattr(vnode, 'kind')

    def test_vnode_init_sets_attributes_correctly(
        self, 
        mock_syntax_node: Mock, 
        mock_tree: Mock
    ) -> None:
        """Test that __init__ sets raw and tree attributes."""
        vnode = IdentifierNameVNode(mock_syntax_node, mock_tree)
        
        assert vnode.raw is mock_syntax_node
        assert vnode.tree is mock_tree

    def test_identifier_name_called_on_correct_attribute(
        self, 
        mock_syntax_node: Mock, 
        mock_tree: Mock
    ) -> None:
        """Test that identifier_name accesses the correct attribute."""
        vnode = IdentifierNameVNode(mock_syntax_node, mock_tree)
        
        # Verify it calls the identifier.value attribute
        name = vnode.identifier_name
        assert name == mock_syntax_node.identifier.value

    def test_multiple_vnodes_independent(
        self, 
        mock_syntax_node: Mock, 
        mock_tree: Mock
    ) -> None:
        """Test that multiple IdentifierNameVNode instances are independent."""
        # Create first vnode
        vnode1_node = Mock(spec=sl.IdentifierNameSyntax)
        vnode1_node.identifier = Mock(value="signal1")
        vnode1 = IdentifierNameVNode(vnode1_node, mock_tree)
        
        # Create second vnode
        vnode2_node = Mock(spec=sl.IdentifierNameSyntax)
        vnode2_node.identifier = Mock(value="signal2")
        vnode2 = IdentifierNameVNode(vnode2_node, mock_tree)
        
        # Verify they are independent
        assert vnode1.identifier_name == "signal1"
        assert vnode2.identifier_name == "signal2"
        assert vnode1.identifier_name != vnode2.identifier_name

    def test_vnode_location_inherited_from_syntax_vnode(self, vnode: IdentifierNameVNode) -> None:
        """Test that location property is inherited from SyntaxVNode."""
        location = vnode.location
        
        # Location should be a dict with line and col keys
        assert isinstance(location, dict)
        assert "line" in location
        assert "col" in location

    def test_identifier_name_with_special_characters(
        self, 
        mock_syntax_node: Mock, 
        mock_tree: Mock
    ) -> None:
        """Test identifier_name with names containing special characters."""
        special_names = ["signal_1", "clk_div_2", "_internal", "__private__"]
        
        for name in special_names:
            mock_syntax_node.identifier.value = name
            vnode = IdentifierNameVNode(mock_syntax_node, mock_tree)
            assert vnode.identifier_name == name

    def test_vnode_kind_inherited(self, vnode: IdentifierNameVNode) -> None:
        """Test that kind property is accessible from inherited SyntaxVNode."""
        # kind should be accessible as it's inherited from SyntaxVNode
        assert hasattr(vnode, 'kind')
        kind = vnode.kind
        # kind comes from raw.kind
        assert kind == vnode.raw.kind

    def test_vnode_children_inherited(self, vnode: IdentifierNameVNode) -> None:
        """Test that children property is inherited from SyntaxVNode."""
        # Even though IdentifierNameVNode doesn't override children,
        # it should inherit it from SyntaxVNode
        assert hasattr(vnode, 'children')
