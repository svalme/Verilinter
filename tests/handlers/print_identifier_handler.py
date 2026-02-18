from pathlib import Path
import pyslang as sl
from src.pkg.handlers.register_handlers import *
from src.pkg.vnodes.register_vnodes import *

from src.pkg.vnodes.syntax_vnode import SyntaxVNode
from src.pkg.vnodes.vnode_factory import vnode_factory
from src.pkg.vnodes.identifier_vnode import IdentifierNameVNode
from src.pkg.ast.walker import Walker
from src.pkg.ast.context import Context
from src.pkg.ast.symbol_table import SymbolTable
from src.pkg.ast.dispatch import dispatch

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
EXPECTED = ROOT / "expected"

def test_identifier_name_vnode():
    """Test IdentifierNameVNode creation and handler"""
    
    tree = sl.SyntaxTree.fromFile(str(DATA / "simple.v"))
    
    print("=" * 70)
    print("FACTORY REGISTRATION CHECK")
    print("=" * 70)
    print(f"VNode Factory registered types: {len(vnode_factory._node_map)}")
    print(f"Is IdentifierNameSyntax registered? {sl.IdentifierNameSyntax in vnode_factory._node_map}")
    if sl.IdentifierNameSyntax in vnode_factory._node_map:
        print(f"  -> Maps to: {vnode_factory._node_map[sl.IdentifierNameSyntax]}")
    print()
    
    print("=" * 70)
    print("DISPATCH REGISTRATION CHECK")
    print("=" * 70)
    print(f"Dispatch registered types: {len(dispatch._registry)}")
    print(f"Is IdentifierNameSyntax registered? {sl.IdentifierNameSyntax in dispatch._registry}")
    if sl.IdentifierNameSyntax in dispatch._registry:
        print(f"  -> Maps to: {dispatch._registry[sl.IdentifierNameSyntax]}")
    print()
    
    # Find an IdentifierNameSyntax node in the tree
    print("=" * 70)
    print("FINDING IDENTIFIER NODES IN TREE")
    print("=" * 70)
    
    def find_identifier_nodes(node, results=[]):
        """Recursively find IdentifierNameSyntax nodes"""
        if isinstance(node, sl.IdentifierNameSyntax):
            results.append(node)
        
        # Traverse children
        if hasattr(node, '__iter__'):
            for child in node:
                find_identifier_nodes(child, results)
        
        return results
    
    identifier_nodes = find_identifier_nodes(tree.root)
    print(f"Found {len(identifier_nodes)} IdentifierNameSyntax nodes")
    
    if identifier_nodes:
        raw_node = identifier_nodes[0]
        print(f"\nFirst identifier raw node:")
        print(f"  Type: {type(raw_node)}")
        print(f"  Kind: {raw_node.kind if hasattr(raw_node, 'kind') else 'N/A'}")
        if hasattr(raw_node, 'identifier'):
            print(f"  Identifier token: {raw_node.identifier}")
            print(f"  Identifier value: {raw_node.identifier.valueText}")
        print()
        
        # Test VNode creation
        print("=" * 70)
        print("TESTING VNODE CREATION")
        print("=" * 70)
        
        vnode = vnode_factory.create(raw_node, tree)
        print(f"Created VNode:")
        print(f"  Type: {type(vnode)}")
        print(f"  Class name: {vnode.__class__.__name__}")
        print(f"  Is IdentifierNameVNode? {isinstance(vnode, IdentifierNameVNode)}")
        print(f"  Has 'identifier_name' attr? {hasattr(vnode, 'identifier_name')}")
        
        if hasattr(vnode, 'identifier_name'):
            print(f"  identifier_name value: {vnode.identifier_name()}")
        else:
            print(f"  Available attributes: {[x for x in dir(vnode) if not x.startswith('_')]}")
        print()
        
        # Test Handler
        print("=" * 70)
        print("TESTING HANDLER")
        print("=" * 70)
        
        handler = dispatch.get(vnode)
        print(f"Handler: {handler}")
        print(f"Handler type: {type(handler)}")
        print()
        
        # Test update_context
        symbol_table = SymbolTable()
        ctx = Context(scopes=[symbol_table.global_scope])
        
        try:
            new_ctx = handler.update_context(ctx, vnode, symbol_table)
            print(f"✓ Handler.update_context succeeded")
            print(f"  Context stack length: {len(new_ctx.stack)}")
            print(f"  Symbol table scopes: {len(symbol_table.scopes)}")
        except Exception as e:
            print(f"✗ Handler.update_context failed:")
            print(f"  Error: {e}")
            print(f"  Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
        print()
    
    # Test full walker
    print("=" * 70)
    print("TESTING FULL WALKER")
    print("=" * 70)
    
    walker = Walker(dispatch)
    ctx = Context()
    symbol_table = SymbolTable()
    
    # Walk a small subtree (not the whole tree to avoid noise)
    if identifier_nodes:
        parent_node = tree.root  # Or find a smaller subtree
        try:
            walker.walk(parent_node, tree, ctx, symbol_table)
            print(f"✓ Walker completed successfully")
            print(f"  Total nodes visited: {len(walker._results)}")
            
            # Show IdentifierNameVNode results
            identifier_results = [
                (vnode, ctx) for vnode, ctx in walker._results 
                if isinstance(vnode, IdentifierNameVNode)
            ]
            print(f"  IdentifierNameVNode results: {len(identifier_results)}")
            
            if identifier_results:
                print("\n  First 3 identifiers found:")
                for i, (vnode, ctx) in enumerate(identifier_results[:3]):
                    print(f"    {i+1}. {vnode.identifier_name()} at {vnode.location}")
            
        except Exception as e:
            print(f"✗ Walker failed:")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    test_identifier_name_vnode()