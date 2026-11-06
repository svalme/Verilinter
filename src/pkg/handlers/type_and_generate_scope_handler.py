"""Keep aggregate fields and generate-block locals out of enclosing namespaces."""
from ..parser.syntax import genvar_declaration_names_and_locations, loop_generate_genvar_name
from ..parser.types import GenerateBlockNode, GenvarDeclarationNode, StructUnionTypeNode, LoopGenerateNode
from ..semantic.symbol import Symbol
from ..semantic.symbol_kind import SymbolKind
from ..walk.dispatch import dispatch
from .syntax_node_handler import SyntaxNodeHandler
from ..semantic.scope_kinds import ScopeKind


@dispatch.register(StructUnionTypeNode)
class StructUnionTypeHandler(SyntaxNodeHandler):
    def update_context(self, ctx, vnode, symbol_table):
        scope = symbol_table.new_scope(kind=ScopeKind.AGGREGATE, location=vnode.location)
        return ctx.push(vnode).with_scope(scope)

    def on_exit(self, ctx, vnode, symbol_table):
        symbol_table.pop_scope()


@dispatch.register(LoopGenerateNode)
class LoopGenerateHandler(SyntaxNodeHandler):
    def update_context(self, ctx, vnode, symbol_table):
        scope = symbol_table.new_scope(kind=ScopeKind.GENERATE_FOR, location=vnode.location)
        genvar_name = loop_generate_genvar_name(vnode.raw)
        if genvar_name:
            symbol = Symbol(name=genvar_name, kind=SymbolKind.GENVAR)
            symbol.add_declaration(vnode.location)
            scope.define(symbol)
        return ctx.push(vnode).with_scope(scope)

    def on_exit(self, ctx, vnode, symbol_table):
        symbol_table.pop_scope()


@dispatch.register(GenerateBlockNode)
class GenerateBlockHandler(SyntaxNodeHandler):
    """Each `begin ... end` body of an if/case/loop generate construct is its own scope."""

    def update_context(self, ctx, vnode, symbol_table):
        scope = symbol_table.new_scope(kind=ScopeKind.GENERATE_BLOCK, location=vnode.location)
        return ctx.push(vnode).with_scope(scope)

    def on_exit(self, ctx, vnode, symbol_table):
        symbol_table.pop_scope()


@dispatch.register(GenvarDeclarationNode)
class GenvarDeclarationHandler(SyntaxNodeHandler):
    """Declares each name in `genvar a, b;` in the enclosing scope."""

    def update_context(self, ctx, vnode, symbol_table):
        for name, loc in genvar_declaration_names_and_locations(vnode.raw, vnode.tree):
            symbol = Symbol(name=name, kind=SymbolKind.GENVAR)
            symbol.add_declaration(loc or vnode.location)
            ctx.scope().define(symbol)
        return ctx.push(vnode)

