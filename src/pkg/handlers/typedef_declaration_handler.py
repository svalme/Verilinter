from ..parser.syntax import typedef_declaration_name_and_location
from ..parser.types import ForwardTypedefDeclarationNode, TypedefDeclarationNode
from ..semantic.symbol import Symbol
from ..semantic.symbol_table import SymbolTable
from ..vnodes.syntax_vnode import SyntaxVNode
from ..walk.context import Context
from ..walk.dispatch import dispatch
from .syntax_node_handler import SyntaxNodeHandler


@dispatch.register(TypedefDeclarationNode)
@dispatch.register(ForwardTypedefDeclarationNode)
class TypedefDeclarationHandler(SyntaxNodeHandler):
    """Registers declared typedef names as symbols with kind='typedef' in the current scope.

    Prevents typedef identifiers (e.g. `pmp_cfg_t'(1'b0)` or `my_byte_t'(1'b0)`) from
    being misclassified as implicit nets when used as cast expression prefixes or type
    references, while preserving the distinction between declared types, parameter widths,
    and undeclared identifiers.
    """

    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        name, loc = typedef_declaration_name_and_location(vnode.raw, vnode.tree)
        if name:
            symbol = Symbol(name=name, kind="typedef")
            decl_loc = loc or vnode.location
            if decl_loc is not None:
                symbol.add_declaration(decl_loc)
            ctx.scope().define(symbol)
        return ctx.push(vnode)

    def __str__(self) -> str:
        return "TypedefDeclarationHandler"
