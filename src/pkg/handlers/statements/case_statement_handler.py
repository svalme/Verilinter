from ...parser.syntax import state_machine_model
from ...parser.types import CaseStatementNode
from ...semantic.scope import enclosing_module_scope
from ...semantic.symbol_table import SymbolTable
from ...vnodes.syntax_vnode import SyntaxVNode
from ...walk.context import CaseStatementFrame, Context
from ...walk.dispatch import dispatch
from ..syntax_node_handler import SyntaxNodeHandler


@dispatch.register(CaseStatementNode)
class CaseStatementHandler(SyntaxNodeHandler):
    """Precompute the shared structural `FsmModel` once per case statement and
    ride it down `ctx.case_frame` so descendant tokens (`endcase`) and case-level FSM
    rules share a single evaluation without re-walking module members."""

    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        ctx = ctx.push(vnode)
        model = state_machine_model(vnode.raw, ctx)
        case_frame = CaseStatementFrame(case_raw=vnode.raw, fsm_model=model)
        ctx = ctx.with_case_frame(case_frame)
        if model is not None:
            module_scope = enclosing_module_scope(ctx.scope())
            if module_scope is not None:
                module_scope.fsm_models.append(model)
        return ctx

    def __str__(self) -> str:
        return "CaseStatementHandler"
