from ..walk.dispatch import dispatch
from ..walk.context import Context
from ..parser.syntax import identifier_name, is_task_declaration_node
from ..semantic.symbol_table import SymbolTable
from ..semantic.symbol import Symbol
from ..vnodes.syntax_vnode import SyntaxVNode
from ..parser.types import FunctionDeclarationNode
from .syntax_node_handler import SyntaxNodeHandler


@dispatch.register(FunctionDeclarationNode)
class FunctionDeclarationHandler(SyntaxNodeHandler):
    """Gives a function/task its own nested scope for its ports and body locals.

    pyslang represents both `function` and `task` declarations with the same
    `FunctionDeclarationSyntax` wrapper class, distinguishable only by `.kind`
    -- same shape as module/package (see ModuleDeclarationHandler). Without a
    dedicated scope here, a function/task's parameters and locals land in the
    flat enclosing module scope, so an ordinary parameter/local name reused
    across two independent function/task declarations (a common
    idiom, e.g. a local named `mnemonic`) looks like a
    REDECLARED_VARIABLE collision instead of two unrelated declarations.
    """

    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        kind = "task" if is_task_declaration_node(vnode.raw) else "function"
        name = identifier_name(getattr(vnode.raw.prototype, "name", None)) or "<anonymous>"
        scope = symbol_table.new_scope(kind=kind, name=name, location=vnode.location)
        if kind == "function" and str(vnode.raw.prototype.returnType).strip() != "void":
            # A non-void function has a local result variable bearing its name.
            result = Symbol(name=name, kind="variable")
            result.is_function_return = True
            result.add_declaration(vnode.location)
            # Returning exports its value to the caller, like an output formal.
            result.is_port = True
            result.port_direction = "output"
            scope.define(result)
        return ctx.push(vnode).with_scope(scope)

    def on_exit(self, _ctx: Context, _vnode: SyntaxVNode, symbol_table: SymbolTable) -> None:
        symbol_table.pop_scope()

    def __str__(self) -> str:
        return "FunctionDeclarationHandler"
