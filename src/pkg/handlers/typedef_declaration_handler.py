from ..parser.syntax import token_location
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
        name_token = getattr(vnode.raw, "name", None)
        if name_token is not None:
            name = str(getattr(name_token, "value", "") or name_token).strip()
            if name:
                symbol = Symbol(name=name, kind="typedef")
                loc = token_location(name_token, vnode.tree)
                if loc.get("line", 0) == 0:
                    loc = vnode.location
                symbol.add_declaration(loc)
                ctx.scope().define(symbol)
        return ctx.push(vnode)

    def __str__(self) -> str:
        return "TypedefDeclarationHandler"
