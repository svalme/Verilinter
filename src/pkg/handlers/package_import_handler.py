from ..parser.syntax import package_import_items
from ..parser.types import PackageImportDeclarationNode
from ..semantic.symbol_table import SymbolTable
from ..vnodes.syntax_vnode import SyntaxVNode
from ..walk.context import Context
from ..walk.dispatch import dispatch
from .syntax_node_handler import SyntaxNodeHandler


@dispatch.register(PackageImportDeclarationNode)
class PackageImportHandler(SyntaxNodeHandler):
    """Records `import pkg::*;` / `import pkg::name;` onto the importing scope.

    `.package`/`.item` are bare tokens, not `IdentifierNameSyntax` nodes, so
    `IdentifierNameHandler` never visits them -- this handler is the only place
    an import statement is read. See `SymbolTable.lookup_from_scope`, which
    consults `Scope.imports` once an ordinary ancestor-scope lookup fails.
    """

    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        scope = ctx.scope()
        for package_name, imported_name in package_import_items(vnode.raw):
            scope.add_import(package_name, imported_name)
        return ctx.push(vnode)

    def __str__(self) -> str:
        return "PackageImportHandler"
