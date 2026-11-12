from ..walk.context import Context, ContextFlag, ProceduralBlockFrame
from ..semantic.scope import enclosing_module_scope
from ..semantic.symbol_table import SymbolTable
from .syntax_node_handler import SyntaxNodeHandler
from ..vnodes.syntax_vnode import SyntaxVNode

from ..parser.syntax import (
    ALWAYS_BLOCK_KIND,
    ALWAYS_COMB_BLOCK_KIND,
    ALWAYS_FF_BLOCK_KIND,
    ALWAYS_LATCH_BLOCK_KIND,
    async_reset_signal_names,
    classify_reset_style,
    is_combinational_style_always_block,
    missing_sensitivity_trigger_nodes,
    procedural_block_assignment_triggers,
)
from ..parser.types import (
    ProceduralBlockNode,
)
from ..walk.dispatch import dispatch

@dispatch.register(ProceduralBlockNode)
class ProceduralBlockHandler(SyntaxNodeHandler):
    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        ctx = ctx.push(vnode)
        kind = vnode.kind

        if kind == ALWAYS_COMB_BLOCK_KIND:
            ctx = ctx.with_flag(ContextFlag.ALWAYS_COMB)

        elif kind == ALWAYS_BLOCK_KIND:
            ctx = ctx.with_flag(ContextFlag.ALWAYS)

        elif kind == ALWAYS_FF_BLOCK_KIND:
            ctx = ctx.with_flag(ContextFlag.ALWAYS_FF)

        elif kind == ALWAYS_LATCH_BLOCK_KIND:
            ctx = ctx.with_flag(ContextFlag.ALWAYS_LATCH)

        # Computed once per block here rather than once per matching descendant node
        # in the rules themselves, which would re-walk the block's subtree O(K^2)
        # times. A deliberate exception to the usual layering
        # standard of not putting handler state behind a fact a rule could derive
        # statelessly -- here it can, but only cheaply if computed once per block.
        mix_trigger, multi_nb_triggers = procedural_block_assignment_triggers(vnode.raw)
        reset_style = classify_reset_style(vnode.raw)
        async_reset_names = (
            frozenset(async_reset_signal_names(vnode.raw))
            if reset_style == "async"
            else frozenset()
        )
        block_frame = ProceduralBlockFrame(
            block_raw=vnode.raw,
            missing_sensitivity=missing_sensitivity_trigger_nodes(vnode.raw),
            mix_trigger=mix_trigger,
            multiple_nonblocking_write_triggers=multi_nb_triggers,
            is_comb=is_combinational_style_always_block(vnode.raw),
            async_reset_names=async_reset_names,
        )
        ctx = ctx.with_block_frame(block_frame)

        if reset_style is not None:
            module_scope = enclosing_module_scope(ctx.scope())
            if module_scope is not None and module_scope.name:
                symbol_table.register_reset_style_event(module_scope.name, reset_style, vnode.location)

        return ctx

    def __str__(self) -> str:
        return "ProceduralBlockHandler"
